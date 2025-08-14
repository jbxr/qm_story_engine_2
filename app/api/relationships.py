"""Relationship API endpoints with temporal support

Provides CRUD operations for entity relationships with temporal bounds.
All endpoints follow the established API response pattern.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.services.database import get_db
from app.services import relationship_service
from app.models.entities import (
    RelationshipCreate, 
    RelationshipRead, 
    RelationshipUpdate,
    RelationshipBatchOperation
)

router = APIRouter(tags=["relationships"])


@router.post("/", response_model=Dict[str, Any])
async def create_relationship(
    relationship: RelationshipCreate,
    db=Depends(get_db)
):
    """Create a new relationship with temporal support"""
    try:
        result = await relationship_service.create_relationship(db, relationship)
        api_result = relationship_service._map_to_api_format(result)
        
        return {
            "success": True,
            "data": api_result,
            "message": "Relationship created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=Dict[str, Any])
async def list_relationships(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of relationships to return"),
    offset: int = Query(0, ge=0, description="Number of relationships to skip"),
    time: Optional[int] = Query(None, description="Timestamp for temporal filtering"),
    db=Depends(get_db)
):
    """List relationships with pagination and optional temporal filtering"""
    try:
        if time is not None:
            # Use temporal filtering
            all_relationships = await relationship_service.get_active_relationships(db, timestamp=time)
        else:
            # Get all relationships with pagination
            response = db.table("relationships").select("*").range(offset, offset + limit - 1).execute()
            all_relationships = response.data
        
        # Apply pagination if not already applied
        if time is not None:
            paginated_relationships = all_relationships[offset:offset + limit]
        else:
            paginated_relationships = all_relationships
            
        api_relationships = [relationship_service._map_to_api_format(rel) for rel in paginated_relationships]
        
        return {
            "success": True,
            "data": api_relationships,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(all_relationships) if time is not None else "unknown"
            },
            "message": f"Retrieved {len(api_relationships)} relationships"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=Dict[str, Any])
async def get_active_relationships(
    time: int = Query(..., description="Timestamp for active relationships"),
    entity_id: Optional[UUID] = Query(None, description="Filter by specific entity"),
    db=Depends(get_db)
):
    """Get active relationships at a specific timestamp"""
    try:
        relationships = await relationship_service.get_active_relationships(db, entity_id, time)
        api_relationships = [relationship_service._map_to_api_format(rel) for rel in relationships]
        
        return {
            "success": True,
            "data": api_relationships,
            "message": f"Retrieved {len(api_relationships)} active relationships at timestamp {time}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overlapping", response_model=Dict[str, Any])
async def get_overlapping_relationships(
    from_time: int = Query(..., alias="from", description="Start timestamp"),
    to_time: int = Query(..., alias="to", description="End timestamp"),
    db=Depends(get_db)
):
    """Get relationships that overlap with a time range"""
    try:
        relationships = await relationship_service.get_overlapping_relationships(db, from_time, to_time)
        api_relationships = [relationship_service._map_to_api_format(rel) for rel in relationships]
        
        return {
            "success": True,
            "data": api_relationships,
            "message": f"Retrieved {len(api_relationships)} relationships overlapping time range {from_time}-{to_time}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types/list", response_model=Dict[str, Any])
async def list_relationship_types(
    db=Depends(get_db)
):
    """Get all unique relationship types in the system"""
    try:
        response = db.table("relationships").select("relation_type").execute()
        
        # Extract unique types, filtering out nulls
        types = set()
        for rel in response.data:
            if rel.get("relation_type"):
                types.add(rel["relation_type"])
        
        sorted_types = sorted(list(types))
        
        return {
            "success": True,
            "data": sorted_types,
            "message": f"Retrieved {len(sorted_types)} unique relationship types"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=Dict[str, Any])
async def batch_relationship_operations(
    operations: List[RelationshipBatchOperation],
    db=Depends(get_db)
):
    """Execute multiple relationship operations in batch"""
    try:
        # Convert to the format expected by the service
        service_operations = []
        for op in operations:
            service_op = {
                "operation": op.operation,
                "relationship_id": str(op.relationship_id) if op.relationship_id else None,
                "data": op.data.model_dump() if op.data else None
            }
            service_operations.append(service_op)
        
        results = await relationship_service.batch_relationship_operations(db, service_operations)
        
        # Convert results to API format where applicable
        api_results = []
        for result in results:
            if "result" in result and isinstance(result["result"], dict) and "id" in result["result"]:
                # This is a relationship result that needs API mapping
                result["result"] = relationship_service._map_to_api_format(result["result"])
            api_results.append(result)
        
        return {
            "success": True,
            "data": api_results,
            "message": f"Executed {len(api_results)} batch operations"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entity/{entity_id}", response_model=Dict[str, Any])
async def get_entity_relationships(
    entity_id: UUID,
    time: Optional[int] = Query(None, description="Timestamp for temporal filtering"),
    db=Depends(get_db)
):
    """Get all relationships for an entity (as subject or object)"""
    try:
        relationships = await relationship_service.get_entity_relationships_api_format(db, entity_id, time)
        
        return {
            "success": True,
            "data": relationships,
            "message": f"Retrieved {len(relationships)} relationships for entity {entity_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/between/{subject_id}/{object_id}", response_model=Dict[str, Any])
async def get_relationships_between(
    subject_id: UUID,
    object_id: UUID,
    time: Optional[int] = Query(None, description="Timestamp for temporal filtering"),
    db=Depends(get_db)
):
    """Get relationships between two specific entities"""
    try:
        relationships = await relationship_service.get_relationships_between(db, subject_id, object_id, time)
        api_relationships = [relationship_service._map_to_api_format(rel) for rel in relationships]
        
        return {
            "success": True,
            "data": api_relationships,
            "message": f"Retrieved {len(api_relationships)} relationships between entities"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/{entity_id}", response_model=Dict[str, Any])
async def get_entity_relationship_graph(
    entity_id: UUID,
    time: Optional[int] = Query(None, description="Timestamp for temporal filtering"),
    max_depth: int = Query(2, ge=1, le=5, description="Maximum graph traversal depth"),
    db=Depends(get_db)
):
    """Get relationship graph for an entity with configurable depth"""
    try:
        graph = await relationship_service.get_entity_relationship_graph(db, entity_id, time, max_depth)
        
        # Convert relationships to API format
        api_relationships = [relationship_service._map_to_api_format(rel) for rel in graph["relationships"]]
        graph["relationships"] = api_relationships
        
        return {
            "success": True,
            "data": graph,
            "message": f"Retrieved relationship graph for entity {entity_id} (depth {max_depth})"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{relationship_id}", response_model=Dict[str, Any])
async def get_relationship(
    relationship_id: UUID,
    db=Depends(get_db)
):
    """Get a specific relationship by ID"""
    try:
        result = await relationship_service.get_relationship_api_format(db, relationship_id)
        
        return {
            "success": True,
            "data": result,
            "message": "Relationship retrieved successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{relationship_id}", response_model=Dict[str, Any])
async def update_relationship(
    relationship_id: UUID,
    updates: RelationshipUpdate,
    db=Depends(get_db)
):
    """Update relationship fields including temporal bounds"""
    try:
        result = await relationship_service.update_relationship(db, relationship_id, updates)
        api_result = relationship_service._map_to_api_format(result)
        
        return {
            "success": True,
            "data": api_result,
            "message": "Relationship updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{relationship_id}", response_model=Dict[str, Any])
async def delete_relationship(
    relationship_id: UUID,
    db=Depends(get_db)
):
    """Delete a relationship"""
    try:
        success = await relationship_service.delete_relationship(db, relationship_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Relationship {relationship_id} not found")
        
        return {
            "success": True,
            "data": {"id": str(relationship_id)},
            "message": "Relationship deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))