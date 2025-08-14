"""
Story Goals API endpoints using proven patterns
Based on successful scenes.py implementation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..services.database import get_db
from ..utils.serialization import serialize_database_response, create_success_response, create_error_response, create_list_response, create_item_response

router = APIRouter()

class StoryGoalCreate(BaseModel):
    subject_id: str  # Entity ID for the subject
    verb: str  # Action verb (e.g., "must defeat", "needs to learn", "should reach")
    object_id: str | None = None  # Optional entity ID for the object
    description: str | None = None  # Additional context for the goal

class StoryGoalUpdate(BaseModel):
    subject_id: str | None = None
    verb: str | None = None
    object_id: str | None = None
    description: str | None = None

class StoryGoalFulfill(BaseModel):
    linked_milestone_id: str | None = None  # Optional milestone that fulfills this goal

class StoryGoalResponse(BaseModel):
    id: str
    subject_id: str
    verb: str
    object_id: str | None
    description: str | None
    created_at: str

@router.get("")
def list_goals(subject_id: str | None = None):
    """List all story goals - using proven database operation"""
    try:
        db = get_db()
        query = db.table("story_goals").select("*").order("created_at", desc=False)
        
        # Filter by subject_id if provided
        if subject_id:
            query = query.eq("subject_id", subject_id)
        
        result = query.execute()
        goals = result.data if result.data else []
        
        return create_list_response(goals, "goals")
    except Exception as e:
        return create_error_response(error=str(e))

@router.post("")
def create_goal(goal_data: StoryGoalCreate):
    """Create a new story goal - using proven database operation"""
    try:
        db = get_db()
        
        # Use the same operation pattern we proved works
        goal_to_create = {
            "subject_id": goal_data.subject_id,
            "verb": goal_data.verb
        }
        
        # Add optional fields
        if goal_data.object_id:
            goal_to_create["object_id"] = goal_data.object_id
        if goal_data.description:
            goal_to_create["description"] = goal_data.description
        
        result = db.table("story_goals").insert(goal_to_create).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Failed to create goal")
        
        created_goal = result.data[0]
        
        return create_item_response(created_goal, "goal", "Goal created successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.get("/{goal_id}")
def get_goal(goal_id: str):
    """Get a specific goal by ID"""
    try:
        db = get_db()
        result = db.table("story_goals").select("*").eq("id", goal_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Goal not found", status_code=404)
        
        return create_item_response(result.data[0], "goal")
    except Exception as e:
        return create_error_response(str(e))

@router.put("/{goal_id}")
def update_goal(goal_id: str, goal_data: StoryGoalUpdate):
    """Update an existing goal"""
    try:
        db = get_db()
        
        # Build update object with only provided fields
        update_data = {}
        if goal_data.subject_id is not None:
            update_data["subject_id"] = goal_data.subject_id
        if goal_data.verb is not None:
            update_data["verb"] = goal_data.verb
        if goal_data.object_id is not None:
            update_data["object_id"] = goal_data.object_id
        if goal_data.description is not None:
            update_data["description"] = goal_data.description
        
        if not update_data:
            return create_error_response("No fields to update")
        
        result = db.table("story_goals").update(update_data).eq("id", goal_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Goal not found or failed to update", status_code=404)
        
        return create_item_response(result.data[0], "goal", "Goal updated successfully")
    except Exception as e:
        return create_error_response(str(e))

# Note: Goal fulfillment functionality will be added when 
# fulfilled_at and linked_milestone_id columns are added to the database

@router.delete("/{goal_id}")
def delete_goal(goal_id: str):
    """Delete a goal"""
    try:
        db = get_db()
        result = db.table("story_goals").delete().eq("id", goal_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Goal not found or failed to delete", status_code=404)
        
        return create_item_response(result.data[0], "deleted_goal", "Goal deleted successfully")
    except Exception as e:
        return create_error_response(str(e))