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