"""
Milestone API endpoints - First-Class Table Implementation
Based on new schema with milestones as separate table
Updated to use proper SQLModel classes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from uuid import UUID
from ..services.database import get_db
from ..utils.serialization import serialize_database_response, create_success_response, create_error_response, create_list_response, create_item_response
from ..models.entities import (
    MilestoneRead, MilestoneCreate, MilestoneUpdate
)

router = APIRouter()

# All API models now imported from entities.py
# Using proper SQLModel classes for consistency

@router.get("")
def list_milestones(scene_id: str | None = None, subject_id: str | None = None, verb: str | None = None):
    """List all milestones - using proven database operation"""
    try:
        db = get_db()
        query = db.table("milestones").select("*").order("created_at")
        
        # Filter by scene_id if provided
        if scene_id:
            query = query.eq("scene_id", scene_id)
        
        # Filter by subject_id if provided
        if subject_id:
            query = query.eq("subject_id", subject_id)
        
        # Filter by verb if provided (case insensitive)
        if verb:
            query = query.ilike("verb", f"%{verb}%")
        
        result = query.execute()
        milestones = result.data if result.data else []
        
        return create_list_response(milestones, "milestones")
    except Exception as e:
        return create_error_response(error=str(e))

@router.post("")
def create_milestone(milestone_data: MilestoneCreate):
    """Create a new milestone - using proven database operation"""
    try:
        db = get_db()
        
        # Use the same operation pattern we proved works
        # Convert UUIDs to strings for Supabase compatibility
        milestone_to_create = {
            "scene_id": str(milestone_data.scene_id),
            "verb": milestone_data.verb,
            "weight": milestone_data.weight
        }
        
        # Add optional fields, converting UUIDs to strings
        if milestone_data.subject_id:
            milestone_to_create["subject_id"] = str(milestone_data.subject_id)
        if milestone_data.object_id:
            milestone_to_create["object_id"] = str(milestone_data.object_id)
        if milestone_data.description:
            milestone_to_create["description"] = milestone_data.description
        if milestone_data.meta:
            milestone_to_create["metadata"] = milestone_data.meta
        
        result = db.table("milestones").insert(milestone_to_create).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Failed to create milestone")
        
        created_milestone = result.data[0]
        
        return create_item_response(created_milestone, "milestone", "Milestone created successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.get("/{milestone_id}")
def get_milestone(milestone_id: str):
    """Get a specific milestone by ID"""
    try:
        db = get_db()
        result = db.table("milestones").select("*").eq("id", milestone_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Milestone not found", status_code=404)
        
        return create_item_response(result.data[0], "milestone")
    except Exception as e:
        return create_error_response(str(e))

@router.put("/{milestone_id}")
def update_milestone(milestone_id: str, milestone_data: MilestoneUpdate):
    """Update an existing milestone"""
    try:
        db = get_db()
        
        # Build update object with only provided fields, converting UUIDs to strings
        update_data = {}
        if milestone_data.subject_id is not None:
            update_data["subject_id"] = str(milestone_data.subject_id) if milestone_data.subject_id else None
        if milestone_data.verb is not None:
            update_data["verb"] = milestone_data.verb
        if milestone_data.object_id is not None:
            update_data["object_id"] = str(milestone_data.object_id) if milestone_data.object_id else None
        if milestone_data.description is not None:
            update_data["description"] = milestone_data.description
        if milestone_data.weight is not None:
            update_data["weight"] = milestone_data.weight
        if milestone_data.meta is not None:
            update_data["metadata"] = milestone_data.meta
        
        if not update_data:
            return create_error_response("No fields to update")
        
        result = db.table("milestones").update(update_data).eq("id", milestone_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Milestone not found or failed to update", status_code=404)
        
        return create_item_response(result.data[0], "milestone", "Milestone updated successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.delete("/{milestone_id}")
def delete_milestone(milestone_id: str):
    """Delete a milestone"""
    try:
        db = get_db()
        result = db.table("milestones").delete().eq("id", milestone_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Milestone not found or failed to delete", status_code=404)
        
        return create_item_response(result.data[0], "deleted_milestone", "Milestone deleted successfully")
    except Exception as e:
        return create_error_response(str(e))