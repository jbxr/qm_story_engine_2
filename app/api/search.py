"""
Timeline-aware search and discovery API endpoints.
Handles semantic search, entity search, knowledge search, and complex temporal queries.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from ..models.api_models import (
    SemanticSearchRequest, TextSearchRequest, TimelineSearchRequest,
    EntitySearchRequest, KnowledgeSearchRequest, ComplexQueryRequest,
    SearchResponse, TimelineSearchResult
)
from ..services.search_service import SearchService
from ..services.search_service import search_service

router = APIRouter()


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(search_request: SemanticSearchRequest):
    """Perform semantic search using pgvector embeddings"""
    try:
        service = SearchService()
        response = await service.semantic_search(search_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@router.post("/text", response_model=SearchResponse)
async def text_search(search_request: TextSearchRequest):
    """Perform full-text search across content"""
    try:
        service = SearchService()
        response = await service.text_search(search_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text search failed: {str(e)}")


@router.post("/entities", response_model=SearchResponse)
async def search_entities(search_request: EntitySearchRequest):
    """Search entities with optional relationship context"""
    try:
        service = SearchService()
        response = await service.search_entities(search_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entity search failed: {str(e)}")


@router.post("/timeline", response_model=TimelineSearchResult)
async def search_timeline(search_request: TimelineSearchRequest):
    """Timeline-aware story world state query"""
    try:
        service = SearchService()
        result = await service.search_timeline(search_request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline search failed: {str(e)}")


@router.post("/knowledge", response_model=SearchResponse)
async def search_knowledge(search_request: KnowledgeSearchRequest):
    """Search knowledge snapshots with entity context"""
    try:
        service = SearchService()
        response = await service.search_knowledge(search_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {str(e)}")


@router.post("/complex", response_model=SearchResponse)
async def complex_query(query_request: ComplexQueryRequest):
    """Complex multi-entity temporal query with relationship traversal"""
    try:
        service = SearchService()
        response = await service.complex_query(query_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complex query failed: {str(e)}")


@router.get("/health", response_model=dict)
async def search_health():
    """Health check for search service"""
    try:
        service = SearchService()
        
        # Test basic database connectivity
        result = service.db.table("entities").select("id").limit(1).execute()
        
        return {
            "success": True,
            "message": "Search service is healthy",
            "database_connected": True,
            "services": {
                "semantic_search": "available (fallback to text search)",
                "text_search": "available",
                "entity_search": "available",
                "timeline_search": "available", 
                "knowledge_search": "available",
                "complex_query": "available"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search service health check failed: {str(e)}")


@router.get("/stats", response_model=dict)
async def search_statistics():
    """Get search performance and content statistics"""
    try:
        service = SearchService()
        
        # Get content counts for search statistics
        stats_queries = {
            "entities": "SELECT COUNT(*) as count FROM entities",
            "scenes": "SELECT COUNT(*) as count FROM scenes",
            "scene_blocks": "SELECT COUNT(*) as count FROM scene_blocks",
            "relationships": "SELECT COUNT(*) as count FROM entity_relationships",
            "knowledge_snapshots": "SELECT COUNT(*) as count FROM knowledge_snapshots",
            "milestones": "SELECT COUNT(*) as count FROM milestones"
        }
        
        stats = {}
        for name, query in stats_queries.items():
            try:
                result = service.db.rpc("execute_sql", {
                    "query": query,
                    "params": []
                }).execute()
                
                if result.data and result.data[0]:
                    stats[name] = result.data[0]["count"]
                else:
                    stats[name] = 0
            except:
                stats[name] = 0
        
        # Calculate searchable content score
        total_content = sum(stats.values())
        searchable_score = min(100, (total_content / 100) * 100)  # Scale to 100 max
        
        return {
            "success": True,
            "data": {
                "content_counts": stats,
                "total_searchable_items": total_content,
                "searchable_score": round(searchable_score, 1),
                "search_capabilities": {
                    "semantic_search": "fallback_mode",
                    "temporal_queries": "enabled",
                    "relationship_traversal": "enabled",
                    "knowledge_search": "enabled",
                    "complex_queries": "enabled"
                }
            },
            "message": f"Search statistics - {total_content} searchable items"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search statistics: {str(e)}")


@router.get("/predicates", response_model=List[str])
async def get_search_predicates():
    """Get all unique relationship predicates for search filtering"""
    try:
        service = SearchService()
        result = service.db.rpc("execute_sql", {
            "query": "SELECT DISTINCT predicate FROM entity_relationships ORDER BY predicate",
            "params": []
        }).execute()
        
        predicates = []
        if result.data:
            predicates = [row["predicate"] for row in result.data]
        
        return predicates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search predicates: {str(e)}")


@router.get("/entity-types", response_model=List[str])
async def get_entity_types():
    """Get all unique entity types for search filtering"""
    try:
        service = SearchService()
        result = service.db.rpc("execute_sql", {
            "query": "SELECT DISTINCT entity_type FROM entities ORDER BY entity_type",
            "params": []
        }).execute()
        
        entity_types = []
        if result.data:
            entity_types = [row["entity_type"] for row in result.data]
        
        return entity_types
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity types: {str(e)}")


# =============================
# PHASE 4: Semantic Search Endpoints
# =============================

@router.post("/semantic/scene-blocks")
async def semantic_search_scene_blocks(
    query: str,
    scene_id: str = None,
    block_type: str = None,
    similarity_threshold: float = 0.5,
    limit: int = 10
):
    """Search scene blocks using semantic similarity."""
    try:
        from uuid import UUID
        scene_uuid = UUID(scene_id) if scene_id else None
        
        results = await search_service.search_scene_blocks(
            query=query,
            scene_id=scene_uuid,
            block_type=block_type,
            similarity_threshold=similarity_threshold,
            limit=limit
        )
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic scene block search failed: {str(e)}")


@router.post("/semantic/entities")
async def semantic_search_entities(
    query: str,
    entity_type: str = None,
    similarity_threshold: float = 0.5,
    limit: int = 10
):
    """Search entities using semantic similarity."""
    try:
        results = await search_service.search_entities(
            query=query,
            entity_type=entity_type,
            similarity_threshold=similarity_threshold,
            limit=limit
        )
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic entity search failed: {str(e)}")


@router.post("/semantic/knowledge")
async def semantic_search_knowledge(
    query: str,
    character_id: str = None,
    timeline_start: int = None,
    timeline_end: int = None,
    similarity_threshold: float = 0.5,
    limit: int = 10
):
    """Search knowledge snapshots using semantic similarity."""
    try:
        from uuid import UUID
        character_uuid = UUID(character_id) if character_id else None
        
        results = await search_service.search_knowledge_snapshots(
            query=query,
            character_id=character_uuid,
            timeline_start=timeline_start,
            timeline_end=timeline_end,
            similarity_threshold=similarity_threshold,
            limit=limit
        )
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic knowledge search failed: {str(e)}")


@router.post("/semantic/all")
async def semantic_search_all(
    query: str,
    include_scenes: bool = True,
    include_entities: bool = True,
    include_knowledge: bool = True,
    similarity_threshold: float = 0.5,
    limit_per_type: int = 5
):
    """Search across all content types using semantic similarity."""
    try:
        results = await search_service.search_all(
            query=query,
            include_scenes=include_scenes,
            include_entities=include_entities,
            include_knowledge=include_knowledge,
            similarity_threshold=similarity_threshold,
            limit_per_type=limit_per_type
        )
        
        total_results = sum(len(results[key]) for key in results)
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_count": total_results,
            "counts_by_type": {
                key: len(results[key]) for key in results
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Universal semantic search failed: {str(e)}")


@router.post("/similar/{content_type}/{content_id}")
async def find_similar_content(
    content_type: str,
    content_id: str,
    similarity_threshold: float = 0.7,
    limit: int = 5
):
    """Find content similar to a specific piece of content."""
    try:
        from uuid import UUID
        
        if content_type not in ["scene_block", "entity", "knowledge_snapshot"]:
            raise HTTPException(status_code=400, detail="Invalid content type")
            
        content_uuid = UUID(content_id)
        
        results = await search_service.find_similar_content(
            content_type=content_type,
            content_id=content_uuid,
            similarity_threshold=similarity_threshold,
            limit=limit
        )
        
        return {
            "success": True,
            "reference": {
                "type": content_type,
                "id": content_id
            },
            "similar_content": results,
            "count": len(results)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar content search failed: {str(e)}")


@router.post("/embeddings/generate")
async def generate_content_embeddings(
    content_type: str = "all",
    batch_size: int = 50
):
    """Generate embeddings for existing content (admin endpoint)."""
    try:
        from ..services.embedding_service import embedding_service
        from ..services.database import supabase
        
        if content_type not in ["all", "scene_blocks", "entities", "knowledge_snapshots"]:
            raise HTTPException(status_code=400, detail="Invalid content type")
            
        processed_count = 0
        errors = []
        
        # Process scene blocks
        if content_type in ["all", "scene_blocks"]:
            try:
                response = await supabase.table("scene_blocks").select("id, content, summary, lines").execute()
                for block in response.data or []:
                    try:
                        await embedding_service.update_entity_embedding(
                            block["id"], "scene_block", block
                        )
                        processed_count += 1
                    except Exception as e:
                        errors.append(f"Scene block {block['id']}: {str(e)}")
            except Exception as e:
                errors.append(f"Scene blocks processing: {str(e)}")
                
        # Process entities
        if content_type in ["all", "entities"]:
            try:
                response = await supabase.table("entities").select("id, name, description, metadata").execute()
                for entity in response.data or []:
                    try:
                        await embedding_service.update_entity_embedding(
                            entity["id"], "entity", entity
                        )
                        processed_count += 1
                    except Exception as e:
                        errors.append(f"Entity {entity['id']}: {str(e)}")
            except Exception as e:
                errors.append(f"Entities processing: {str(e)}")
                
        # Process knowledge snapshots
        if content_type in ["all", "knowledge_snapshots"]:
            try:
                response = await supabase.table("knowledge_snapshots").select("id, knowledge_state").execute()
                for snapshot in response.data or []:
                    try:
                        await embedding_service.update_entity_embedding(
                            snapshot["id"], "knowledge_snapshot", snapshot
                        )
                        processed_count += 1
                    except Exception as e:
                        errors.append(f"Knowledge snapshot {snapshot['id']}: {str(e)}")
            except Exception as e:
                errors.append(f"Knowledge snapshots processing: {str(e)}")
        
        return {
            "success": True,
            "processed_count": processed_count,
            "content_type": content_type,
            "errors": errors[:10],  # Limit error list
            "total_errors": len(errors)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")