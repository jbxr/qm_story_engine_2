"""Knowledge snapshot management API endpoints - Phase 2 Implementation"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from uuid import UUID

from ..models.api_models import (
    KnowledgeSnapshotCreate, KnowledgeSnapshotUpdate, KnowledgeSnapshotResponse
)
from ..services.database import get_db
from ..services.knowledge_service import KnowledgeService
from ..utils.serialization import (
    create_success_response, create_error_response, 
    create_list_response, create_item_response
)

router = APIRouter()


@router.post("/snapshots")
def create_knowledge_snapshot(snapshot_data: KnowledgeSnapshotCreate):
    """Create new knowledge snapshot for a character"""
    try:
        service = KnowledgeService()
        created_snapshot = service.create_knowledge_snapshot(snapshot_data)
        return create_item_response(created_snapshot, "snapshot", "Knowledge snapshot created successfully")
    except Exception as e:
        return create_error_response(str(e))


@router.get("/snapshots/{snapshot_id}")
def get_knowledge_snapshot(snapshot_id: str):
    """Get specific knowledge snapshot by ID"""
    try:
        service = KnowledgeService()
        snapshot = service.get_knowledge_snapshot(snapshot_id)
        
        if not snapshot:
            return create_error_response("Knowledge snapshot not found", status_code=404)
        
        return create_item_response(snapshot, "snapshot")
    except Exception as e:
        return create_error_response(str(e))


@router.get("/snapshots/character/{character_id}")
def get_character_knowledge_snapshots(
    character_id: str,
    timestamp: Optional[int] = Query(None, description="Filter by timeline timestamp"),
    limit: int = Query(50, ge=1, le=1000, description="Limit results")
):
    """Get knowledge snapshots for a character"""
    try:
        service = KnowledgeService()
        snapshots = service.get_character_knowledge_snapshots(character_id, timestamp, limit)
        return create_list_response(snapshots, "snapshots")
    except Exception as e:
        return create_error_response(str(e))


@router.get("/snapshots/scene/{scene_id}")
def get_scene_knowledge_snapshots(
    scene_id: str,
    character_id: Optional[str] = Query(None, description="Filter by specific character")
):
    """Get knowledge snapshots linked to a scene"""
    try:
        service = KnowledgeService()
        snapshots = service.get_scene_knowledge_snapshots(scene_id, character_id)
        return create_list_response(snapshots, "snapshots")
    except Exception as e:
        return create_error_response(str(e))


@router.put("/snapshots/{snapshot_id}")
def update_knowledge_snapshot(
    snapshot_id: str,
    snapshot_data: KnowledgeSnapshotUpdate
):
    """Update knowledge snapshot"""
    try:
        service = KnowledgeService()
        updated_snapshot = service.update_knowledge_snapshot(snapshot_id, snapshot_data)
        
        if not updated_snapshot:
            return create_error_response("Knowledge snapshot not found", status_code=404)
        
        return create_item_response(updated_snapshot, "snapshot", "Knowledge snapshot updated successfully")
    except Exception as e:
        return create_error_response(str(e))


@router.delete("/snapshots/{snapshot_id}")
def delete_knowledge_snapshot(snapshot_id: str):
    """Delete knowledge snapshot"""
    try:
        service = KnowledgeService()
        success = service.delete_knowledge_snapshot(snapshot_id)
        
        if not success:
            return create_error_response("Knowledge snapshot not found", status_code=404)
        
        return create_success_response(message="Knowledge snapshot deleted successfully")
    except Exception as e:
        return create_error_response(str(e))