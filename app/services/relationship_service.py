"""Relationship service with temporal support

Handles entity relationships with temporal bounds using Supabase database functions.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from supabase import Client
import json

from app.models.entities import RelationshipCreate, RelationshipUpdate


async def create_relationship(db: Client, relationship_data: RelationshipCreate) -> dict:
    """Create a new relationship with temporal support"""
    try:
        data = {
            "source_id": str(relationship_data.source_id),
            "target_id": str(relationship_data.target_id),
            "relation_type": relationship_data.relation_type,
            "weight": relationship_data.weight,
            "starts_at": relationship_data.starts_at,
            "ends_at": relationship_data.ends_at,
            "metadata": relationship_data.meta or {}
        }
        
        response = db.table("relationships").insert(data).execute()
        
        if not response.data:
            raise ValueError("Failed to create relationship")
            
        return response.data[0]
        
    except Exception as e:
        raise Exception(f"Error creating relationship: {str(e)}")


async def get_relationship(db: Client, relationship_id: UUID) -> dict:
    """Get a specific relationship by ID"""
    try:
        response = db.table("relationships").select("*").eq("id", str(relationship_id)).execute()
        
        if not response.data:
            raise ValueError(f"Relationship {relationship_id} not found")
            
        return response.data[0]
        
    except ValueError:
        # Re-raise ValueError to maintain error semantics
        raise
    except Exception as e:
        raise Exception(f"Error getting relationship: {str(e)}")


async def update_relationship(db: Client, relationship_id: UUID, updates: RelationshipUpdate) -> dict:
    """Update relationship fields including temporal bounds"""
    try:
        # Build update data from non-None fields
        update_data = {}
        if updates.relation_type is not None:
            update_data["relation_type"] = updates.relation_type
        if updates.weight is not None:
            update_data["weight"] = updates.weight
        if updates.starts_at is not None:
            update_data["starts_at"] = updates.starts_at
        if updates.ends_at is not None:
            update_data["ends_at"] = updates.ends_at
        if updates.meta is not None:
            update_data["metadata"] = updates.meta
            
        if not update_data:
            raise ValueError("No fields to update")
            
        response = db.table("relationships").update(update_data).eq("id", str(relationship_id)).execute()
        
        if not response.data:
            raise ValueError(f"Relationship {relationship_id} not found")
            
        return response.data[0]
        
    except Exception as e:
        raise Exception(f"Error updating relationship: {str(e)}")


async def delete_relationship(db: Client, relationship_id: UUID) -> bool:
    """Delete a relationship"""
    try:
        response = db.table("relationships").delete().eq("id", str(relationship_id)).execute()
        return len(response.data) > 0
        
    except Exception as e:
        raise Exception(f"Error deleting relationship: {str(e)}")


async def get_entity_relationships(db: Client, entity_id: UUID, timestamp: Optional[int] = None) -> List[dict]:
    """Get all relationships for an entity (as subject or object)"""
    try:
        if timestamp is not None:
            # Use temporal function for time-scoped relationships
            response = db.rpc('relationships_active_at', {
                'as_of': timestamp
            }).execute()
            
            # Filter by entity_id in either source_id or target_id
            filtered_data = [
                rel for rel in response.data 
                if rel.get('source_id') == str(entity_id) or rel.get('target_id') == str(entity_id)
            ]
            return filtered_data
        else:
            # Get all relationships for entity
            source_response = db.table("relationships").select("*").eq("source_id", str(entity_id)).execute()
            target_response = db.table("relationships").select("*").eq("target_id", str(entity_id)).execute()
            
            # Combine and deduplicate
            all_relationships = source_response.data + target_response.data
            seen_ids = set()
            unique_relationships = []
            for rel in all_relationships:
                if rel['id'] not in seen_ids:
                    seen_ids.add(rel['id'])
                    unique_relationships.append(rel)
                    
            return unique_relationships
            
    except Exception as e:
        raise Exception(f"Error getting entity relationships: {str(e)}")


async def get_active_relationships(db: Client, entity_id: Optional[UUID] = None, timestamp: Optional[int] = None) -> List[dict]:
    """Get active relationships at a specific timestamp"""
    try:
        if timestamp is None:
            raise ValueError("Timestamp required for active relationships query")
            
        response = db.rpc('relationships_active_at', {
            'as_of': timestamp
        }).execute()
        
        if entity_id:
            # Filter by entity_id
            filtered_data = [
                rel for rel in response.data 
                if rel.get('source_id') == str(entity_id) or rel.get('target_id') == str(entity_id)
            ]
            return filtered_data
        
        return response.data
        
    except Exception as e:
        raise Exception(f"Error getting active relationships: {str(e)}")


async def get_overlapping_relationships(db: Client, from_t: int, to_t: int) -> List[dict]:
    """Get relationships that overlap with a time range"""
    try:
        response = db.rpc('relationships_overlapping', {
            'from_t': from_t,
            'to_t': to_t
        }).execute()
        
        return response.data
        
    except Exception as e:
        raise Exception(f"Error getting overlapping relationships: {str(e)}")


async def get_relationships_between(db: Client, subject_id: UUID, object_id: UUID, timestamp: Optional[int] = None) -> List[dict]:
    """Get relationships between two specific entities"""
    try:
        if timestamp is not None:
            # Get active relationships at timestamp, then filter
            active_rels = await get_active_relationships(db, timestamp=timestamp)
            between_rels = [
                rel for rel in active_rels 
                if (rel.get('source_id') == str(subject_id) and rel.get('target_id') == str(object_id)) or
                   (rel.get('source_id') == str(object_id) and rel.get('target_id') == str(subject_id))
            ]
            return between_rels
        else:
            # Get all relationships between the entities
            forward_response = db.table("relationships").select("*").eq("source_id", str(subject_id)).eq("target_id", str(object_id)).execute()
            backward_response = db.table("relationships").select("*").eq("source_id", str(object_id)).eq("target_id", str(subject_id)).execute()
            
            return forward_response.data + backward_response.data
            
    except Exception as e:
        raise Exception(f"Error getting relationships between entities: {str(e)}")


async def get_entity_relationship_graph(db: Client, entity_id: UUID, timestamp: Optional[int] = None, max_depth: int = 2) -> dict:
    """Get relationship graph for an entity with configurable depth"""
    try:
        visited = set()
        graph = {
            "center_entity": str(entity_id),
            "timestamp": timestamp,
            "relationships": [],
            "entities": set()
        }
        
        async def explore_relationships(current_id: UUID, depth: int):
            if depth > max_depth or str(current_id) in visited:
                return
                
            visited.add(str(current_id))
            graph["entities"].add(str(current_id))
            
            # Get relationships for current entity
            relationships = await get_entity_relationships(db, current_id, timestamp)
            
            for rel in relationships:
                graph["relationships"].append(rel)
                
                # Find connected entity
                connected_id = None
                if rel['source_id'] == str(current_id):
                    connected_id = rel['target_id']
                elif rel['target_id'] == str(current_id):
                    connected_id = rel['source_id']
                    
                if connected_id and connected_id not in visited:
                    graph["entities"].add(connected_id)
                    if depth < max_depth:
                        await explore_relationships(UUID(connected_id), depth + 1)
        
        await explore_relationships(entity_id, 0)
        
        # Convert entities set to list for JSON serialization
        graph["entities"] = list(graph["entities"])
        
        return graph
        
    except Exception as e:
        raise Exception(f"Error getting relationship graph: {str(e)}")


async def batch_relationship_operations(db: Client, operations: List[Dict[str, Any]]) -> List[dict]:
    """Execute multiple relationship operations in batch"""
    try:
        results = []
        
        for op in operations:
            operation_type = op.get("operation")
            
            if operation_type == "create":
                create_data = RelationshipCreate(**op["data"])
                result = await create_relationship(db, create_data)
                results.append({"operation": "create", "result": result})
                
            elif operation_type == "update":
                relationship_id = UUID(op["relationship_id"])
                update_data = RelationshipUpdate(**op["data"])
                result = await update_relationship(db, relationship_id, update_data)
                results.append({"operation": "update", "result": result})
                
            elif operation_type == "delete":
                relationship_id = UUID(op["relationship_id"])
                result = await delete_relationship(db, relationship_id)
                results.append({"operation": "delete", "result": result})
                
            else:
                results.append({"operation": operation_type, "error": "Unknown operation"})
                
        return results
        
    except Exception as e:
        raise Exception(f"Error in batch operations: {str(e)}")


def _map_to_api_format(relationship_data: dict) -> dict:
    """Map database fields to API format"""
    return {
        "id": relationship_data["id"],
        "subject_id": relationship_data["source_id"],  # API mapping
        "object_id": relationship_data["target_id"],   # API mapping
        "predicate": relationship_data["relation_type"], # API mapping
        "weight": relationship_data.get("weight"),
        "starts_at": relationship_data.get("starts_at"),
        "ends_at": relationship_data.get("ends_at"),
        "meta": relationship_data.get("metadata", {}),
        "created_at": relationship_data["created_at"]
    }


async def get_relationship_api_format(db: Client, relationship_id: UUID) -> dict:
    """Get relationship in API format with field mapping"""
    relationship = await get_relationship(db, relationship_id)
    return _map_to_api_format(relationship)


async def get_entity_relationships_api_format(db: Client, entity_id: UUID, timestamp: Optional[int] = None) -> List[dict]:
    """Get entity relationships in API format"""
    relationships = await get_entity_relationships(db, entity_id, timestamp)
    return [_map_to_api_format(rel) for rel in relationships]