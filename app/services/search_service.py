"""
Search service layer for timeline-aware queries and complex story world search.
Handles semantic search, timeline queries, entity search with relationship context.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime

from ..services.database import get_db
from ..models.api_models import (
    SemanticSearchRequest, TextSearchRequest, TimelineSearchRequest,
    EntitySearchRequest, KnowledgeSearchRequest, ComplexQueryRequest,
    SearchResult, SearchResponse, TimelineSearchResult,
    RelationshipResponse
)


class SearchService:
    """Service for timeline-aware search and story world queries"""
    
    def __init__(self):
        self.db = get_db()
    
    async def semantic_search(self, search_request: SemanticSearchRequest) -> SearchResponse:
        """Perform semantic search using pgvector embeddings"""
        start_time = time.time()
        
        # TODO: Implement actual semantic search when LLM integration is ready
        # For now, fall back to text search
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