"""
Entity API endpoints using proven patterns - New Schema
Based on successful scenes.py implementation
Updated to use proper SQLModel classes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from uuid import UUID
from ..services.database import get_db
from ..utils.serialization import serialize_database_response, create_success_response, create_error_response, create_list_response, create_item_response
from ..models.entities import (
    EntityRead, EntityCreate, EntityUpdate
)

router = APIRouter()

# All API models now imported from entities.py
# Using proper SQLModel classes for consistency

@router.get("")
def list_entities(entity_type: str | None = None):
    """List all entities - using proven database operation"""
    try:
        db = get_db()
        query = db.table("entities").select("*").order("created_at")
        
        # Filter by entity_type if provided
        if entity_type:
            query = query.eq("entity_type", entity_type)
        
        result = query.execute()
        entities = result.data if result.data else []
        
        return create_list_response(entities, "entities")
    except Exception as e:
        return create_error_response(error=str(e))

@router.post("")
def create_entity(entity_data: EntityCreate):
    """Create a new entity - using proven database operation"""
    try:
        db = get_db()
        
        # Use the same operation pattern we proved works
        entity_to_create = {
            "name": entity_data.name,
            "entity_type": entity_data.entity_type
        }
        
        # Add optional fields
        if entity_data.description:
            entity_to_create["description"] = entity_data.description
        if entity_data.meta:
            entity_to_create["metadata"] = entity_data.meta
        
        result = db.table("entities").insert(entity_to_create).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Failed to create entity")
        
        created_entity = result.data[0]
        
        return create_item_response(created_entity, "entity", "Entity created successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.get("/{entity_id}")
def get_entity(entity_id: str):
    """Get a specific entity by ID"""
    try:
        db = get_db()
        result = db.table("entities").select("*").eq("id", entity_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Entity not found", status_code=404)
        
        return create_item_response(result.data[0], "entity")
    except Exception as e:
        return create_error_response(str(e))

@router.put("/{entity_id}")
def update_entity(entity_id: str, entity_data: EntityUpdate):
    """Update an existing entity"""
    try:
        db = get_db()
        
        # Build update object with only provided fields
        update_data = {}
        if entity_data.name is not None:
            update_data["name"] = entity_data.name
        if entity_data.entity_type is not None:
            update_data["entity_type"] = entity_data.entity_type
        if entity_data.description is not None:
            update_data["description"] = entity_data.description
        if entity_data.meta is not None:
            update_data["metadata"] = entity_data.meta
        
        if not update_data:
            return create_error_response("No fields to update")
        
        # Add updated_at timestamp (handled by trigger in schema, but can be explicit)
        result = db.table("entities").update(update_data).eq("id", entity_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Entity not found or failed to update", status_code=404)
        
        return create_item_response(result.data[0], "entity", "Entity updated successfully")
    except Exception as e:
        return create_error_response(str(e))

@router.delete("/{entity_id}")
def delete_entity(entity_id: str):
    """Delete an entity"""
    try:
        db = get_db()
        result = db.table("entities").delete().eq("id", entity_id).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response("Entity not found or failed to delete", status_code=404)
        
        return create_item_response(result.data[0], "deleted_entity", "Entity deleted successfully")
    except Exception as e:
        return create_error_response(str(e))