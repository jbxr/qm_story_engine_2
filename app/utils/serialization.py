"""
JSON serialization utilities for handling Supabase UUID objects and SQLModel metadata
"""
from uuid import UUID
from typing import Any, Dict, List, Union
from datetime import datetime
import json
from fastapi.responses import JSONResponse


def serialize_for_json(obj: Any) -> Any:
    """
    Convert objects to JSON-serializable format.
    
    Handles:
    - UUID objects -> string
    - datetime objects -> ISO format string
    - dict/list with nested UUID/datetime objects
    - SQLModel MetaData objects -> skip (not needed in JSON response)
    - JSONB fields (already JSON-serializable)
    """
    if obj is None:
        return None
    
    # Handle UUID objects - check both standard UUID and string representations
    elif isinstance(obj, UUID):
        return str(obj)
    elif hasattr(obj, 'hex') and hasattr(obj, 'version') and len(str(obj)) == 36:
        # Alternative UUID-like object detection
        return str(obj)
    
    # Handle datetime objects
    elif isinstance(obj, datetime):
        return obj.isoformat()
    
    # Handle SQLModel MetaData objects and other non-serializable SQLAlchemy types
    elif hasattr(obj, '__class__'):
        obj_type_str = str(type(obj))
        if any(term in obj_type_str for term in ['MetaData', 'sqlalchemy', 'SQLModel']):
            return None
        # Also check for UUID in the type name as backup
        if 'UUID' in obj_type_str or 'uuid' in obj_type_str:
            return str(obj)
    
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            serialized_value = serialize_for_json(value)
            if serialized_value is not None:
                result[key] = serialized_value
        return result
    elif isinstance(obj, list):
        result = []
        for item in obj:
            serialized_item = serialize_for_json(item)
            if serialized_item is not None:
                result.append(serialized_item)
        return result
    else:
        # For primitive types and other JSON-serializable objects
        try:
            json.dumps(obj)  # Test if it's JSON serializable
            return obj
        except (TypeError, ValueError):
            # If not serializable, convert to string representation
            return str(obj)


def serialize_database_response(data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """
    Serialize database response for JSON output.
    
    Args:
        data: Single record (dict) or list of records from Supabase
        
    Returns:
        JSON-serializable version of the data
    """
    return serialize_for_json(data)




def create_error_response(
    error: str, 
    details: str = None,
    status_code: int = 400
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        error: Error message
        details: Optional detailed error info
        status_code: HTTP status code for the error
        
    Returns:
        JSONResponse with standardized error format
    """
    response = {
        "success": False,
        "error": error
    }
    
    if details:
        response["details"] = details
    
    # Serialize the response content and return as JSONResponse
    serialized_content = serialize_for_json(response)
    return JSONResponse(content=serialized_content, status_code=status_code)


def create_success_response(
    data: Any = None,
    message: str = None,
    **additional_data
) -> JSONResponse:
    """
    Create a standardized success response.
    
    Args:
        data: The main data to return (can be single item, list, or dict)
        message: Optional success message
        **additional_data: Additional data fields to include in the data object
        
    Returns:
        JSONResponse with standardized success format:
        {
            "success": true,
            "data": {
                // data content or additional_data
            },
            "message": "Optional message"
        }
    """
    response = {
        "success": True,
        "data": {}
    }
    
    # Handle different data structures
    if data is not None:
        if isinstance(data, dict) and any(key in data for key in ['entities', 'scenes', 'milestones', 'goals', 'blocks', 'entity', 'scene', 'milestone', 'goal', 'block']):
            # List response with count or single item response
            response["data"] = data
        elif isinstance(data, list):
            # Direct list - determine the type and add count
            response["data"] = {
                "items": data,
                "count": len(data)
            }
        else:
            # Single item or other data structure
            response["data"] = data
    
    # Add any additional data fields
    if additional_data:
        if isinstance(response["data"], dict):
            response["data"].update(additional_data)
        else:
            # If data is not a dict, wrap it and add additional fields
            response["data"] = {
                "item": response["data"],
                **additional_data
            }
    
    if message:
        response["message"] = message
    
    # Serialize the response content and return as JSONResponse
    serialized_content = serialize_for_json(response)
    return JSONResponse(content=serialized_content)


def create_list_response(
    items: List[Any],
    list_name: str,
    message: str = None
) -> JSONResponse:
    """
    Create a standardized list response.
    
    Args:
        items: List of items to return
        list_name: Name for the list (e.g., "entities", "scenes")
        message: Optional message
        
    Returns:
        JSONResponse with format:
        {
            "success": true,
            "data": {
                "{list_name}": [...],
                "count": N
            }
        }
    """
    data = {
        list_name: serialize_database_response(items),
        "count": len(items)
    }
    
    return create_success_response(data=data, message=message)


def create_item_response(
    item: Any,
    item_name: str,
    message: str = None
) -> JSONResponse:
    """
    Create a standardized single item response.
    
    Args:
        item: Single item to return
        item_name: Name for the item (e.g., "entity", "scene")
        message: Optional message
        
    Returns:
        JSONResponse with format:
        {
            "success": true,
            "data": {
                "{item_name}": {...}
            }
        }
    """
    data = {item_name: serialize_database_response(item)}
    
    return create_success_response(data=data, message=message)