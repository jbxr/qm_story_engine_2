"""
Scene API endpoints using proven patterns - New Schema
Based on successful test_minimal_api.py implementation
Updated to use proper SQLModel classes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from uuid import UUID
from ..services.database import get_db
from ..utils.serialization import serialize_database_response, create_success_response, create_error_response, create_list_response, create_item_response
from ..models.entities import (
    SceneRead, SceneCreate, SceneUpdate,
    SceneBlockRead, SceneBlockCreate, SceneBlockUpdate,
    SceneBlockMoveRequest, BulkBlockCreateRequest
)

router = APIRouter()

# All API models now imported from entities.py
# Using proper SQLModel classes for consistency

@router.get("")
def list_scenes():
    """List all scenes - using proven database operation"""
    try:
        db = get_db()
        result = db.table("scenes").select("*").order("created_at").execute()
        
        scenes = result.data if result.data else []
        
        return create_list_response(scenes, "scenes")
    except Exception as e:
        return create_error_response(error=str(e))

@router.post("")
def create_scene(scene_data: SceneCreate):
    """Create a new scene - using proven database operation"""
    try:
        db = get_db()
        
        # Use the same operation we proved works in test_scene_workflow.py
        scene_to_create = {
            "title": scene_data.title
        }
        
        # Add optional fields as per new schema
        if scene_data.location_id:
            scene_to_create["location_id"] = scene_data.location_id
        if scene_data.timestamp is not None:
            scene_to_create["timestamp"] = scene_data.timestamp
        
        result = db.table("scenes").insert(scene_to_create).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Failed to create scene")
        
        created_scene = result.data[0]
        
        return create_item_response(created_scene, "scene", "Scene created successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.get("/{scene_id}")
def get_scene(scene_id: str):
    """Get a specific scene by ID"""
    try:
        db = get_db()
        result = db.table("scenes").select("*").eq("id", scene_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Scene not found", status_code=404)
        
        return create_item_response(result.data[0], "scene")
    except Exception as e:
        return create_error_response(str(e))

@router.get("/{scene_id}/blocks")
def get_scene_blocks(scene_id: str):
    """Get blocks for a scene in order - using proven database operation"""
    try:
        db = get_db()
        # Use exact same query from test_scene_workflow.py
        result = db.table("scene_blocks").select("*").eq("scene_id", scene_id).order("order").execute()
        
        blocks = result.data if result.data else []
        
        # Use standardized success response format to include scene_id
        data = {
            "blocks": serialize_database_response(blocks),
            "count": len(blocks),
            "scene_id": scene_id
        }
        return create_success_response(data=data)
    except Exception as e:
        return create_error_response(error=str(e))

@router.post("/{scene_id}/blocks")
def create_scene_block(scene_id: str, block_data: SceneBlockCreate):
    """Add a block to a scene - using proven database operation"""
    try:
        db = get_db()
        
        # Use exact same structure from test_scene_workflow.py with new schema fields
        # Use scene_id from URL path, not from request body to avoid confusion
        block_to_create = {
            "scene_id": str(scene_id),
            "block_type": block_data.block_type,
            "order": block_data.order
        }
        
        # Add optional fields based on new schema
        if block_data.content:
            block_to_create["content"] = block_data.content
        if block_data.summary:
            block_to_create["summary"] = block_data.summary
        if block_data.lines:
            block_to_create["lines"] = block_data.lines
        if block_data.subject_id:
            block_to_create["subject_id"] = str(block_data.subject_id)
        if block_data.verb:
            block_to_create["verb"] = block_data.verb
        if block_data.object_id:
            block_to_create["object_id"] = str(block_data.object_id)
        if block_data.weight is not None:
            block_to_create["weight"] = block_data.weight
        if block_data.meta:
            block_to_create["metadata"] = block_data.meta
        
        result = db.table("scene_blocks").insert(block_to_create).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Failed to create block")
        
        created_block = result.data[0]
        
        return create_item_response(created_block, "block", "Block created successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.put("/{scene_id}")
def update_scene(scene_id: str, scene_data: SceneUpdate):
    """Update an existing scene"""
    try:
        db = get_db()
        
        # Build update object with only provided fields
        update_data = {}
        if scene_data.title is not None:
            update_data["title"] = scene_data.title
        if scene_data.location_id is not None:
            update_data["location_id"] = scene_data.location_id
        if scene_data.timestamp is not None:
            update_data["timestamp"] = scene_data.timestamp
        
        if not update_data:
            return create_error_response("No fields to update")
        
        result = db.table("scenes").update(update_data).eq("id", scene_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Scene not found or failed to update", status_code=404)
        
        return create_item_response(result.data[0], "scene", "Scene updated successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.put("/{scene_id}/blocks/{block_id}")
def update_scene_block(scene_id: str, block_id: str, block_data: SceneBlockUpdate):
    """Update a scene block"""
    try:
        db = get_db()
        
        # Build update object with only provided fields
        update_data = {}
        if block_data.block_type is not None:
            update_data["block_type"] = block_data.block_type
        if block_data.order is not None:
            update_data["order"] = block_data.order
        if block_data.content is not None:
            update_data["content"] = block_data.content
        if block_data.summary is not None:
            update_data["summary"] = block_data.summary
        if block_data.lines is not None:
            update_data["lines"] = block_data.lines
        if block_data.subject_id is not None:
            update_data["subject_id"] = block_data.subject_id
        if block_data.verb is not None:
            update_data["verb"] = block_data.verb
        if block_data.object_id is not None:
            update_data["object_id"] = block_data.object_id
        if block_data.weight is not None:
            update_data["weight"] = block_data.weight
        if block_data.meta is not None:
            update_data["metadata"] = block_data.meta
        
        if not update_data:
            return create_error_response("No fields to update")
        
        result = db.table("scene_blocks").update(update_data).eq("id", block_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Block not found or failed to update", status_code=404)
        
        return create_item_response(result.data[0], "block", "Block updated successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.put("/{scene_id}/blocks/{block_id}/reorder")
def reorder_block(scene_id: str, block_id: str, reorder_data: SceneBlockMoveRequest):
    """Reorder a block within a scene - using proven test_scene_workflow.py logic"""
    try:
        db = get_db()
        
        # Use exact same reordering logic from test_scene_workflow.py
        result = db.table("scene_blocks").update({"order": reorder_data.new_order}).eq("id", block_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Failed to reorder block")
        
        return create_item_response(result.data[0], "block", "Block reordered successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.delete("/{scene_id}")
def delete_scene(scene_id: str):
    """Delete a scene and all its blocks"""
    try:
        db = get_db()
        
        # Delete scene blocks first (foreign key constraint)
        db.table("scene_blocks").delete().eq("scene_id", scene_id).execute()
        
        # Delete the scene
        result = db.table("scenes").delete().eq("id", scene_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Scene not found or failed to delete", status_code=404)
        
        return create_item_response(result.data[0], "deleted_scene", "Scene deleted successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.delete("/{scene_id}/blocks/{block_id}")
def delete_scene_block(scene_id: str, block_id: str):
    """Delete a scene block"""
    try:
        db = get_db()
        result = db.table("scene_blocks").delete().eq("id", block_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Block not found or failed to delete", status_code=404)
        
        return create_item_response(result.data[0], "deleted_block", "Block deleted successfully")
    except Exception as e:
        return create_error_response(str(e))