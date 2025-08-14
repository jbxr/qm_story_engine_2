"""
Semantic Search Service

Provides comprehensive semantic search functionality across scenes, entities, and knowledge snapshots
using pgvector embeddings for similarity matching. Also includes timeline-aware queries and 
complex story world search capabilities.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from uuid import UUID
from datetime import datetime

from app.services.database import get_supabase
from app.services.embedding_service import embedding_service
from app.models.api_models import (
    SemanticSearchRequest, TextSearchRequest, TimelineSearchRequest,
    EntitySearchRequest, KnowledgeSearchRequest, ComplexQueryRequest,
    SearchResult, SearchResponse, TimelineSearchResult,
    RelationshipResponse
)

logger = logging.getLogger(__name__)


class SearchService:
    """
    Handles semantic search operations across the story engine database.
    
    Uses pgvector similarity search with OpenAI embeddings to find semantically
    related content across scenes, entities, and knowledge snapshots.
    Also provides timeline-aware queries and complex story world search.
    """
    
    def __init__(self):
        self.embedding_service = embedding_service
        
    @property
    def db(self):
        """Get the database client lazily."""
        return get_supabase()
    
    async def semantic_search(self, search_request: SemanticSearchRequest) -> SearchResponse:
        """Perform semantic search using pgvector embeddings"""
        start_time = time.time()
        
        try:
            # Generate embedding for the query
            query_embedding = await self.embedding_service.generate_embedding(search_request.query)
            
            # Perform unified search across all content types
            results = await self.search_all(
                search_request.query,
                similarity_threshold=search_request.similarity_threshold or 0.7,
                limit_per_type=search_request.match_count // 3 + 1
            )
            
            # Convert to SearchResult format and combine results
            search_results = []
            
            # Process scene blocks
            for block in results.get('scene_blocks', []):
                search_results.append(SearchResult(
                    id=UUID(block['id']),
                    content_type="scene_block",
                    title=f"Scene Block - {block.get('block_type', 'unknown')}",
                    content=block.get('content', '')[:200],
                    relevance_score=block.get('similarity', 0.0),
                    metadata={
                        "block_type": block.get('block_type'),
                        "scene_id": block.get('scene_id')
                    },
                    scene_id=UUID(block['scene_id']) if block.get('scene_id') else None
                ))
            
            # Process entities
            for entity in results.get('entities', []):
                search_results.append(SearchResult(
                    id=UUID(entity['id']),
                    content_type="entity",
                    title=entity.get('name', 'Unknown Entity'),
                    content=entity.get('description', '')[:200],
                    relevance_score=entity.get('similarity', 0.0),
                    metadata={
                        "entity_type": entity.get('entity_type')
                    },
                    entity_ids=[UUID(entity['id'])]
                ))
            
            # Process knowledge snapshots
            for knowledge in results.get('knowledge_snapshots', []):
                search_results.append(SearchResult(
                    id=UUID(knowledge['id']),
                    content_type="knowledge",
                    title=f"Knowledge - {knowledge.get('entity_name', 'Unknown')}",
                    content=str(knowledge.get('knowledge_data', ''))[:200],
                    relevance_score=knowledge.get('similarity', 0.0),
                    metadata={
                        "entity_id": knowledge.get('entity_id'),
                        "timestamp": knowledge.get('timestamp')
                    },
                    entity_ids=[UUID(knowledge['entity_id'])] if knowledge.get('entity_id') else []
                ))
            
            # Sort by relevance score and limit results
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)
            search_results = search_results[:search_request.match_count]
            
            execution_time = (time.time() - start_time) * 1000
            
            return SearchResponse(
                results=search_results,
                total=len(search_results),
                query=search_request.query,
                search_type="semantic_search",
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Semantic search failed, falling back to text search: {str(e)}")
            # Fall back to text search if semantic search fails
            text_results = await self._text_search_fallback(search_request.query, search_request.match_count)
            
            execution_time = (time.time() - start_time) * 1000
            
            return SearchResponse(
                results=text_results,
                total=len(text_results),
                query=search_request.query,
                search_type="semantic_fallback_text",
                execution_time_ms=execution_time
            )
    
    async def text_search(self, search_request: TextSearchRequest) -> SearchResponse:
        """Perform full-text search across content"""
        start_time = time.time()
        
        results = await self._text_search_fallback(search_request.query, search_request.limit)
        
        execution_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=search_request.query,
            search_type="text_search",
            execution_time_ms=execution_time
        )
    
    async def search_entities(self, search_request: EntitySearchRequest) -> SearchResponse:
        """Search entities with optional relationship context"""
        start_time = time.time()
        
        # Build entity search query with filters
        where_conditions = []
        params = []
        
        # Text search in name and description
        where_conditions.append("(e.name ILIKE %s OR e.description ILIKE %s)")
        search_pattern = f"%{search_request.query}%"
        params.extend([search_pattern, search_pattern])
        
        # Entity type filter
        if search_request.entity_types:
            where_conditions.append("e.entity_type = ANY(%s)")
            params.append(search_request.entity_types)
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            e.id, e.name, e.entity_type, e.description, e.metadata, e.created_at, e.updated_at
        FROM entities e
        WHERE {where_clause}
        ORDER BY 
            CASE 
                WHEN e.name ILIKE %s THEN 1 
                WHEN e.description ILIKE %s THEN 2 
                ELSE 3 
            END,
            e.name ASC
        LIMIT %s
        """
        
        params.extend([search_pattern, search_pattern, search_request.limit])
        
        result = self.db.rpc("execute_sql", {
            "query": query,
            "params": params
        }).execute()
        
        results = []
        if result.data:
            for row in result.data:
                entity_id = UUID(row["id"])
                
                # Calculate relevance score based on match type
                relevance_score = 1.0
                if search_request.query.lower() in row["name"].lower():
                    relevance_score = 0.9
                elif row["description"] and search_request.query.lower() in row["description"].lower():
                    relevance_score = 0.7
                else:
                    relevance_score = 0.5
                
                search_result = SearchResult(
                    id=entity_id,
                    content_type="entity",
                    title=row["name"],
                    content=row["description"],
                    relevance_score=relevance_score,
                    metadata={
                        "entity_type": row["entity_type"],
                        "entity_metadata": row["metadata"]
                    },
                    entity_ids=[entity_id]
                )
                
                results.append(search_result)
        
        execution_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=search_request.query,
            search_type="entity_search",
            execution_time_ms=execution_time,
            timeline_context={"at_timestamp": search_request.at_timestamp} if search_request.at_timestamp else None
        )
    
    async def search_timeline(self, search_request: TimelineSearchRequest) -> TimelineSearchResult:
        """Timeline-aware story world state query"""
        start_time = time.time()
        
        # Get entities (filtered if specified)
        entities = []
        if search_request.entity_ids:
            entity_query = """
            SELECT id, name, entity_type, description, metadata
            FROM entities
            WHERE id = ANY(%s)
            """
            params = [[str(eid) for eid in search_request.entity_ids]]
        else:
            entity_query = """
            SELECT id, name, entity_type, description, metadata
            FROM entities
            ORDER BY name ASC
            LIMIT 100
            """
            params = []
        
        entity_result = self.db.rpc("execute_sql", {
            "query": entity_query,
            "params": params
        }).execute()
        
        if entity_result.data:
            entities = [
                {
                    "id": row["id"],
                    "name": row["name"], 
                    "entity_type": row["entity_type"],
                    "description": row["description"],
                    "metadata": row["metadata"]
                }
                for row in entity_result.data
            ]
        
        # Get active relationships at timestamp
        relationships = []
        if search_request.include_relationships and entities:
            entity_ids = [e["id"] for e in entities]
            rel_query = """
            SELECT 
                r.id, r.subject_id, r.object_id, r.predicate, r.strength,
                r.starts_at, r.ends_at, r.metadata, r.created_at, r.updated_at,
                s.name as subject_name, o.name as object_name
            FROM entity_relationships r
            JOIN entities s ON s.id = r.subject_id
            JOIN entities o ON o.id = r.object_id
            WHERE (r.subject_id = ANY(%s) OR r.object_id = ANY(%s))
            AND ((r.starts_at IS NULL OR r.starts_at <= %s) 
                 AND (r.ends_at IS NULL OR r.ends_at > %s))
            ORDER BY r.strength DESC
            LIMIT 200
            """
            
            rel_result = self.db.rpc("execute_sql", {
                "query": rel_query,
                "params": [entity_ids, entity_ids, search_request.at_timestamp, search_request.at_timestamp]
            }).execute()
            
            if rel_result.data:
                relationships = [
                    RelationshipResponse(
                        id=UUID(row["id"]),
                        subject_id=UUID(row["subject_id"]),
                        object_id=UUID(row["object_id"]),
                        predicate=row["predicate"],
                        strength=row["strength"],
                        starts_at=row["starts_at"],
                        ends_at=row["ends_at"],
                        metadata=row["metadata"],
                        created_at=datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00')),
                        subject_name=row["subject_name"],
                        object_name=row["object_name"]
                    )
                    for row in rel_result.data
                ]
        
        # Get knowledge snapshots at timestamp
        knowledge_snapshots = []
        if search_request.include_knowledge and entities:
            entity_ids = [e["id"] for e in entities]
            
            # Use direct query for knowledge snapshots
            knowledge_query = """
            SELECT k.id, k.entity_id, k.timestamp, k.knowledge, k.metadata
            FROM knowledge_snapshots k
            WHERE k.entity_id = ANY(%s)
            AND (k.timestamp IS NULL OR k.timestamp <= %s)
            ORDER BY k.timestamp DESC
            LIMIT 100
            """
            
            knowledge_result = self.db.rpc("execute_sql", {
                "query": knowledge_query,
                "params": [entity_ids, search_request.at_timestamp]
            }).execute()
            
            if knowledge_result.data:
                knowledge_snapshots = [
                    {
                        "id": row["id"],
                        "entity_id": row["entity_id"],
                        "timestamp": row["timestamp"],
                        "knowledge": row["knowledge"],
                        "metadata": row["metadata"]
                    }
                    for row in knowledge_result.data
                ]
        
        # Get active scenes at timestamp
        active_scenes = []
        if search_request.include_scenes:
            scenes_query = """
            SELECT 
                s.id, s.title, s.location_id, s.timestamp, s.created_at,
                l.name as location_name
            FROM scenes s
            LEFT JOIN entities l ON l.id = s.location_id
            WHERE s.timestamp <= %s
            ORDER BY s.timestamp DESC
            LIMIT 50
            """
            
            scenes_result = self.db.rpc("execute_sql", {
                "query": scenes_query,
                "params": [search_request.at_timestamp]
            }).execute()
            
            if scenes_result.data:
                active_scenes = [
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "location_id": row["location_id"],
                        "timestamp": row["timestamp"],
                        "location_name": row["location_name"],
                        "created_at": row["created_at"]
                    }
                    for row in scenes_result.data
                ]
        
        return TimelineSearchResult(
            timestamp=search_request.at_timestamp,
            entities=entities,
            relationships=relationships,
            knowledge_snapshots=knowledge_snapshots,
            active_scenes=active_scenes
        )
    
    async def search_knowledge(self, search_request: KnowledgeSearchRequest) -> SearchResponse:
        """Search knowledge snapshots with entity context"""
        start_time = time.time()
        
        # Build knowledge search query
        where_conditions = []
        params = []
        
        # Text search in knowledge JSONB
        where_conditions.append("k.knowledge::text ILIKE %s")
        search_pattern = f"%{search_request.query}%"
        params.append(search_pattern)
        
        # Entity filter
        if search_request.entity_ids:
            where_conditions.append("k.entity_id = ANY(%s)")
            params.append([str(eid) for eid in search_request.entity_ids])
        
        # Timestamp range filter
        if search_request.timestamp_range and len(search_request.timestamp_range) == 2:
            where_conditions.append("k.timestamp BETWEEN %s AND %s")
            params.extend(search_request.timestamp_range)
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            k.id, k.entity_id, k.timestamp, k.knowledge, k.metadata, k.created_at,
            e.name as entity_name, e.entity_type
        FROM knowledge_snapshots k
        JOIN entities e ON e.id = k.entity_id
        WHERE {where_clause}
        ORDER BY k.timestamp DESC, k.created_at DESC
        LIMIT %s
        """
        
        params.append(search_request.limit)
        
        result = self.db.rpc("execute_sql", {
            "query": query,
            "params": params
        }).execute()
        
        results = []
        if result.data:
            for row in result.data:
                knowledge_id = UUID(row["id"])
                entity_id = UUID(row["entity_id"])
                
                # Create content snippet from knowledge
                knowledge_text = str(row["knowledge"])
                snippet_start = knowledge_text.lower().find(search_request.query.lower())
                if snippet_start >= 0:
                    start = max(0, snippet_start - 50)
                    end = min(len(knowledge_text), snippet_start + 150)
                    content_snippet = knowledge_text[start:end]
                    if start > 0:
                        content_snippet = "..." + content_snippet
                    if end < len(knowledge_text):
                        content_snippet = content_snippet + "..."
                else:
                    content_snippet = knowledge_text[:200] + ("..." if len(knowledge_text) > 200 else "")
                
                search_result = SearchResult(
                    id=knowledge_id,
                    content_type="knowledge",
                    title=f"{row['entity_name']} knowledge at {row['timestamp'] or 'unspecified time'}",
                    content=content_snippet,
                    relevance_score=0.8,  # Knowledge searches are generally high relevance
                    metadata={
                        "entity_type": row["entity_type"],
                        "full_knowledge": row["knowledge"],
                        "snapshot_metadata": row["metadata"]
                    },
                    entity_ids=[entity_id],
                    timestamp=row["timestamp"]
                )
                
                results.append(search_result)
        
        execution_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=search_request.query,
            search_type="knowledge_search",
            execution_time_ms=execution_time
        )
    
    async def complex_query(self, query_request: ComplexQueryRequest) -> SearchResponse:
        """Complex multi-entity temporal query with relationship traversal"""
        start_time = time.time()
        
        results = []
        timeline_context = {}
        
        # Get base entities
        entities_query = """
        SELECT id, name, entity_type, description, metadata
        FROM entities
        WHERE id = ANY(%s)
        """
        
        entity_result = self.db.rpc("execute_sql", {
            "query": entities_query,
            "params": [[str(eid) for eid in query_request.entities]]
        }).execute()
        
        base_entities = {}
        if entity_result.data:
            for row in entity_result.data:
                entity_id = UUID(row["id"])
                base_entities[entity_id] = row
                
                # Add entity as search result
                results.append(SearchResult(
                    id=entity_id,
                    content_type="entity",
                    title=row["name"],
                    content=row["description"],
                    relevance_score=1.0,  # Base entities are max relevance
                    metadata={
                        "entity_type": row["entity_type"],
                        "is_base_entity": True
                    },
                    entity_ids=[entity_id]
                ))
        
        # Get relationships between entities if requested
        if query_request.include_relationships:
            entity_ids_str = [str(eid) for eid in query_request.entities]
            rel_query = """
            SELECT 
                r.id, r.subject_id, r.object_id, r.predicate, r.strength,
                r.starts_at, r.ends_at, r.metadata, r.created_at, r.updated_at,
                s.name as subject_name, o.name as object_name
            FROM entity_relationships r
            JOIN entities s ON s.id = r.subject_id
            JOIN entities o ON o.id = r.object_id
            WHERE (r.subject_id = ANY(%s) OR r.object_id = ANY(%s))
            """
            
            params = [entity_ids_str, entity_ids_str]
            
            if query_request.at_timestamp:
                rel_query += " AND ((r.starts_at IS NULL OR r.starts_at <= %s) AND (r.ends_at IS NULL OR r.ends_at > %s))"
                params.extend([query_request.at_timestamp, query_request.at_timestamp])
            
            rel_query += " ORDER BY r.strength DESC LIMIT 100"
            
            rel_result = self.db.rpc("execute_sql", {
                "query": rel_query,
                "params": params
            }).execute()
            
            if rel_result.data:
                for row in rel_result.data:
                    results.append(SearchResult(
                        id=UUID(row["id"]),
                        content_type="relationship",
                        title=f"{row['subject_name']} {row['predicate']} {row['object_name']}",
                        content=f"Strength: {row['strength']}",
                        relevance_score=row["strength"],
                        metadata={
                            "predicate": row["predicate"],
                            "strength": row["strength"],
                            "temporal": {
                                "starts_at": row["starts_at"],
                                "ends_at": row["ends_at"]
                            }
                        },
                        entity_ids=[UUID(row["subject_id"]), UUID(row["object_id"])]
                    ))
                
                timeline_context["relationships_count"] = len([r for r in results if r.content_type == "relationship"])
        
        # Sort results by relevance and content type
        results.sort(key=lambda x: (x.relevance_score, x.content_type), reverse=True)
        
        execution_time = (time.time() - start_time) * 1000
        timeline_context["execution_time_ms"] = execution_time
        timeline_context["at_timestamp"] = query_request.at_timestamp
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=f"Complex query for {len(query_request.entities)} entities",
            search_type="complex_query",
            execution_time_ms=execution_time,
            timeline_context=timeline_context
        )
    
    async def _text_search_fallback(self, query: str, limit: int) -> List[SearchResult]:
        """Fallback text search implementation for when semantic search is not available"""
        search_pattern = f"%{query}%"
        
        # Search across multiple content types
        results = []
        
        # Search scene blocks
        blocks_query = """
        SELECT 
            sb.id, sb.scene_id, sb.block_type, sb.content, sb.summary, 
            sb.created_at, s.title as scene_title
        FROM scene_blocks sb
        JOIN scenes s ON s.id = sb.scene_id
        WHERE (sb.content ILIKE %s OR sb.summary ILIKE %s)
        ORDER BY 
            CASE 
                WHEN sb.content ILIKE %s THEN 1 
                WHEN sb.summary ILIKE %s THEN 2 
                ELSE 3 
            END,
            sb.created_at DESC
        LIMIT %s
        """
        
        blocks_result = self.db.rpc("execute_sql", {
            "query": blocks_query,
            "params": [search_pattern, search_pattern, search_pattern, search_pattern, limit // 2]
        }).execute()
        
        if blocks_result.data:
            for row in blocks_result.data:
                content = row["content"] or row["summary"] or ""
                results.append(SearchResult(
                    id=UUID(row["id"]),
                    content_type="scene_block",
                    title=f"{row['scene_title']} - {row['block_type']}",
                    content=content[:200] + ("..." if len(content) > 200 else ""),
                    relevance_score=0.7,
                    metadata={"block_type": row["block_type"]},
                    scene_id=UUID(row["scene_id"])
                ))
        
        # Search entities
        entities_query = """
        SELECT id, name, entity_type, description
        FROM entities
        WHERE name ILIKE %s OR description ILIKE %s
        ORDER BY 
            CASE 
                WHEN name ILIKE %s THEN 1 
                WHEN description ILIKE %s THEN 2 
                ELSE 3 
            END,
            name ASC
        LIMIT %s
        """
        
        entities_result = self.db.rpc("execute_sql", {
            "query": entities_query,
            "params": [search_pattern, search_pattern, search_pattern, search_pattern, limit // 2]
        }).execute()
        
        if entities_result.data:
            for row in entities_result.data:
                results.append(SearchResult(
                    id=UUID(row["id"]),
                    content_type="entity",
                    title=row["name"],
                    content=row["description"] or "",
                    relevance_score=0.8,
                    metadata={"entity_type": row["entity_type"]},
                    entity_ids=[UUID(row["id"])]
                ))
        
        return results[:limit]
    
    # =============================================================================
    # SEMANTIC SEARCH METHODS (Phase 4)
    # =============================================================================
    
    async def search_scene_blocks(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        scene_id: Optional[UUID] = None,
        block_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search scene blocks using semantic similarity.
        
        Args:
            query: Search query text
            similarity_threshold: Minimum similarity score (0.0-1.0)
            limit: Maximum number of results
            scene_id: Optional filter by specific scene
            block_type: Optional filter by block type (prose, dialogue, milestone)
            
        Returns:
            List of matching scene blocks with similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Build the RPC call with filters
            rpc_params = {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': limit
            }
            
            if scene_id:
                rpc_params['filter_scene_id'] = str(scene_id)
            if block_type:
                rpc_params['filter_block_type'] = block_type
                
            # Call the database search function
            response = self.db.rpc('match_scene_blocks', rpc_params).execute()
            
            if response.data:
                logger.info(f"Found {len(response.data)} scene blocks for query: {query[:50]}...")
                return response.data
            else:
                logger.info(f"No scene blocks found for query: {query[:50]}...")
                return []
                
        except Exception as e:
            logger.error(f"Error searching scene blocks: {str(e)}")
            raise
    
    async def search_entities(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search entities using semantic similarity.
        
        Args:
            query: Search query text
            similarity_threshold: Minimum similarity score (0.0-1.0)
            limit: Maximum number of results
            entity_type: Optional filter by entity type (character, location, artifact)
            
        Returns:
            List of matching entities with similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Build the RPC call with filters
            rpc_params = {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': limit
            }
            
            if entity_type:
                rpc_params['filter_entity_type'] = entity_type
                
            # Call the database search function
            response = self.db.rpc('search_entities_by_embedding', rpc_params).execute()
            
            if response.data:
                logger.info(f"Found {len(response.data)} entities for query: {query[:50]}...")
                return response.data
            else:
                logger.info(f"No entities found for query: {query[:50]}...")
                return []
                
        except Exception as e:
            logger.error(f"Error searching entities: {str(e)}")
            raise
    
    async def search_knowledge_snapshots(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        character_id: Optional[UUID] = None,
        timeline_start: Optional[int] = None,
        timeline_end: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge snapshots using semantic similarity.
        
        Args:
            query: Search query text
            similarity_threshold: Minimum similarity score (0.0-1.0)
            limit: Maximum number of results
            character_id: Optional filter by specific character
            timeline_start: Optional filter by timeline position (inclusive)
            timeline_end: Optional filter by timeline position (inclusive)
            
        Returns:
            List of matching knowledge snapshots with similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Build the RPC call with filters
            rpc_params = {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': limit
            }
            
            if character_id:
                rpc_params['filter_character_id'] = str(character_id)
            if timeline_start is not None:
                rpc_params['filter_timeline_start'] = timeline_start
            if timeline_end is not None:
                rpc_params['filter_timeline_end'] = timeline_end
                
            # Call the database search function
            response = self.db.rpc('search_knowledge_by_embedding', rpc_params).execute()
            
            if response.data:
                logger.info(f"Found {len(response.data)} knowledge snapshots for query: {query[:50]}...")
                return response.data
            else:
                logger.info(f"No knowledge snapshots found for query: {query[:50]}...")
                return []
                
        except Exception as e:
            logger.error(f"Error searching knowledge snapshots: {str(e)}")
            raise
    
    async def search_all(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        limit_per_type: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Unified search across all content types.
        
        Args:
            query: Search query text
            similarity_threshold: Minimum similarity score (0.0-1.0)
            limit_per_type: Maximum results per content type
            
        Returns:
            Dictionary with results grouped by content type:
            {
                'scene_blocks': [...],
                'entities': [...],
                'knowledge_snapshots': [...]
            }
        """
        try:
            logger.info(f"Performing unified search for: {query[:50]}...")
            
            # Search all content types in parallel
            scene_blocks_task = self.search_scene_blocks(
                query, similarity_threshold, limit_per_type
            )
            entities_task = self.search_entities(
                query, similarity_threshold, limit_per_type
            )
            knowledge_task = self.search_knowledge_snapshots(
                query, similarity_threshold, limit_per_type
            )
            
            # Wait for all searches to complete
            scene_blocks = await scene_blocks_task
            entities = await entities_task
            knowledge_snapshots = await knowledge_task
            
            results = {
                'scene_blocks': scene_blocks,
                'entities': entities,
                'knowledge_snapshots': knowledge_snapshots
            }
            
            total_results = len(scene_blocks) + len(entities) + len(knowledge_snapshots)
            logger.info(f"Unified search returned {total_results} total results")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in unified search: {str(e)}")
            raise
    
    async def find_similar_content(
        self,
        content_type: str,
        content_id: UUID,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find content similar to a specific item.
        
        Args:
            content_type: Type of content ('scene_block', 'entity', 'knowledge_snapshot')
            content_id: ID of the reference content
            similarity_threshold: Minimum similarity score (0.0-1.0)
            limit: Maximum number of results
            
        Returns:
            List of similar content items with similarity scores
        """
        try:
            # Get the embedding of the reference content
            if content_type == 'scene_block':
                response = self.db.table('scene_blocks').select('content, content_embedding').eq('id', str(content_id)).execute()
                if not response.data:
                    raise ValueError(f"Scene block {content_id} not found")
                
                reference_text = response.data[0]['content']
                reference_embedding = response.data[0]['content_embedding']
                
            elif content_type == 'entity':
                response = self.db.table('entities').select('name, description, description_embedding').eq('id', str(content_id)).execute()
                if not response.data:
                    raise ValueError(f"Entity {content_id} not found")
                
                entity_data = response.data[0]
                reference_text = f"{entity_data['name']}: {entity_data['description']}"
                reference_embedding = entity_data['description_embedding']
                
            elif content_type == 'knowledge_snapshot':
                response = self.db.table('knowledge_snapshots').select('knowledge_data, knowledge_embedding').eq('id', str(content_id)).execute()
                if not response.data:
                    raise ValueError(f"Knowledge snapshot {content_id} not found")
                
                reference_text = str(response.data[0]['knowledge_data'])
                reference_embedding = response.data[0]['knowledge_embedding']
                
            else:
                raise ValueError(f"Invalid content type: {content_type}")
            
            # If no embedding exists, generate one
            if not reference_embedding:
                reference_embedding = await self.embedding_service.generate_embedding(reference_text)
            
            # Search for similar content across all types
            rpc_params = {
                'query_embedding': reference_embedding,
                'match_threshold': similarity_threshold,
                'match_count': limit
            }
            
            # Search all content types
            similar_blocks = self.db.rpc('search_scene_blocks', rpc_params).execute()
            similar_entities = self.db.rpc('search_entities', rpc_params).execute()
            similar_knowledge = self.db.rpc('search_knowledge_snapshots', rpc_params).execute()
            
            # Combine and sort results
            all_results = []
            
            if similar_blocks.data:
                for item in similar_blocks.data:
                    item['content_type'] = 'scene_block'
                    all_results.append(item)
                    
            if similar_entities.data:
                for item in similar_entities.data:
                    item['content_type'] = 'entity'
                    all_results.append(item)
                    
            if similar_knowledge.data:
                for item in similar_knowledge.data:
                    item['content_type'] = 'knowledge_snapshot'
                    all_results.append(item)
            
            # Remove the reference item itself and sort by similarity
            filtered_results = [
                item for item in all_results 
                if item.get('id') != str(content_id)
            ]
            
            # Sort by similarity score (descending)
            sorted_results = sorted(
                filtered_results,
                key=lambda x: x.get('similarity', 0),
                reverse=True
            )[:limit]
            
            logger.info(f"Found {len(sorted_results)} similar items for {content_type} {content_id}")
            return sorted_results
            
        except Exception as e:
            logger.error(f"Error finding similar content: {str(e)}")
            raise
    
    async def get_content_recommendations(
        self,
        scene_id: UUID,
        recommendation_type: str = 'all',
        limit: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get content recommendations for a scene based on existing content.
        
        Args:
            scene_id: ID of the scene to get recommendations for
            recommendation_type: Type of recommendations ('entities', 'knowledge', 'all')
            limit: Maximum recommendations per type
            
        Returns:
            Dictionary with recommended content by type
        """
        try:
            # Get scene content for context
            scene_response = self.db.table('scenes').select('title, summary').eq('id', str(scene_id)).execute()
            if not scene_response.data:
                raise ValueError(f"Scene {scene_id} not found")
            
            scene_data = scene_response.data[0]
            scene_context = f"{scene_data['title']}: {scene_data['summary']}"
            
            # Get scene blocks for additional context
            blocks_response = self.db.table('scene_blocks').select('content').eq('scene_id', str(scene_id)).execute()
            if blocks_response.data:
                block_content = " ".join([block['content'] for block in blocks_response.data])
                scene_context += f" {block_content}"
            
            recommendations = {}
            
            if recommendation_type in ['entities', 'all']:
                # Find relevant entities
                relevant_entities = await self.search_entities(
                    scene_context,
                    similarity_threshold=0.6,
                    limit=limit
                )
                recommendations['entities'] = relevant_entities
            
            if recommendation_type in ['knowledge', 'all']:
                # Find relevant knowledge snapshots
                relevant_knowledge = await self.search_knowledge_snapshots(
                    scene_context,
                    similarity_threshold=0.6,
                    limit=limit
                )
                recommendations['knowledge_snapshots'] = relevant_knowledge
            
            total_recommendations = sum(len(recs) for recs in recommendations.values())
            logger.info(f"Generated {total_recommendations} recommendations for scene {scene_id}")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting content recommendations: {str(e)}")
            raise


# Global search service instance
search_service = SearchService()