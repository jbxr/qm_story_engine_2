"""Knowledge snapshot business logic - Phase 2 Implementation"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import logging

from ..models.api_models import KnowledgeSnapshotCreate, KnowledgeSnapshotUpdate
from ..services.database import get_db

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Business logic for knowledge snapshot operations"""
    
    def __init__(self):
        self.db = get_db()
    
    def create_knowledge_snapshot(self, snapshot_data: KnowledgeSnapshotCreate) -> dict:
        """Create new knowledge snapshot for a character"""
        try:
            data = {
                "entity_id": str(snapshot_data.entity_id),
                "knowledge": snapshot_data.knowledge,
                "metadata": snapshot_data.metadata or {}
            }
            
            # Add timestamp if provided
            if snapshot_data.timestamp is not None:
                data["timestamp"] = snapshot_data.timestamp
            
            result = self.db.table("knowledge_snapshots").insert(data).execute()
            
            if not result.data or len(result.data) == 0:
                raise Exception("Failed to create knowledge snapshot")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Create knowledge snapshot failed: {e}")
            raise
    
    def get_knowledge_snapshot(self, snapshot_id: str) -> Optional[dict]:
        """Get specific knowledge snapshot by ID"""
        try:
            result = self.db.table("knowledge_snapshots") \
                .select("*") \
                .eq("id", snapshot_id) \
                .execute()
            
            if not result.data or len(result.data) == 0:
                return None
            
            snapshot = result.data[0]
            
            # Enhance with entity name if possible
            if snapshot.get("entity_id"):
                entity_result = self.db.table("entities") \
                    .select("name") \
                    .eq("id", snapshot["entity_id"]) \
                    .execute()
                
                if entity_result.data and len(entity_result.data) > 0:
                    snapshot["entity_name"] = entity_result.data[0]["name"]
            
            return snapshot
        except Exception as e:
            logger.error(f"Get knowledge snapshot failed: {e}")
            raise
    
    def get_character_knowledge_snapshots(
        self, 
        character_id: str,
        timestamp: Optional[int] = None,
        limit: int = 50
    ) -> List[dict]:
        """Get knowledge snapshots for a character"""
        try:
            query = self.db.table("knowledge_snapshots") \
                .select("*") \
                .eq("entity_id", character_id)
            
            # Filter by timestamp if provided
            if timestamp is not None:
                query = query.eq("timestamp", timestamp)
            
            result = query \
                .order("timestamp", desc=True) \
                .limit(limit) \
                .execute()
            
            snapshots = result.data if result.data else []
            
            # Enhance with entity name for each snapshot
            for snapshot in snapshots:
                if snapshot.get("entity_id"):
                    entity_result = self.db.table("entities") \
                        .select("name") \
                        .eq("id", snapshot["entity_id"]) \
                        .execute()
                    
                    if entity_result.data and len(entity_result.data) > 0:
                        snapshot["entity_name"] = entity_result.data[0]["name"]
            
            return snapshots
        except Exception as e:
            logger.error(f"Get character knowledge snapshots failed: {e}")
            raise
    
    def get_scene_knowledge_snapshots(
        self, 
        scene_id: str,
        character_id: Optional[str] = None
    ) -> List[dict]:
        """Get knowledge snapshots linked to a scene"""
        try:
            # First, get scene timestamp
            scene_result = self.db.table("scenes") \
                .select("timestamp") \
                .eq("id", scene_id) \
                .execute()
            
            if not scene_result.data or len(scene_result.data) == 0:
                return []
            
            scene_timestamp = scene_result.data[0].get("timestamp")
            
            if scene_timestamp is None:
                return []
            
            # Get snapshots at this timestamp
            query = self.db.table("knowledge_snapshots") \
                .select("*") \
                .eq("timestamp", scene_timestamp)
            
            # Filter by character if provided
            if character_id:
                query = query.eq("entity_id", character_id)
            
            result = query.execute()
            snapshots = result.data if result.data else []
            
            # Enhance with entity names
            for snapshot in snapshots:
                if snapshot.get("entity_id"):
                    entity_result = self.db.table("entities") \
                        .select("name") \
                        .eq("id", snapshot["entity_id"]) \
                        .execute()
                    
                    if entity_result.data and len(entity_result.data) > 0:
                        snapshot["entity_name"] = entity_result.data[0]["name"]
            
            return snapshots
        except Exception as e:
            logger.error(f"Get scene knowledge snapshots failed: {e}")
            raise
    
    def update_knowledge_snapshot(
        self, 
        snapshot_id: str, 
        snapshot_data: KnowledgeSnapshotUpdate
    ) -> Optional[dict]:
        """Update knowledge snapshot"""
        try:
            data = {}
            
            if snapshot_data.timestamp is not None:
                data["timestamp"] = snapshot_data.timestamp
            if snapshot_data.knowledge is not None:
                data["knowledge"] = snapshot_data.knowledge
            if snapshot_data.metadata is not None:
                data["metadata"] = snapshot_data.metadata
            
            if not data:
                # No updates provided
                return self.get_knowledge_snapshot(snapshot_id)
            
            result = self.db.table("knowledge_snapshots") \
                .update(data) \
                .eq("id", snapshot_id) \
                .execute()
            
            if not result.data or len(result.data) == 0:
                return None
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Update knowledge snapshot failed: {e}")
            raise
    
    def delete_knowledge_snapshot(self, snapshot_id: str) -> bool:
        """Delete knowledge snapshot"""
        try:
            result = self.db.table("knowledge_snapshots") \
                .delete() \
                .eq("id", snapshot_id) \
                .execute()
            
            return result.data is not None and len(result.data) > 0
        except Exception as e:
            logger.error(f"Delete knowledge snapshot failed: {e}")
            return False
    
    def compute_knowledge_at_timestamp(
        self, 
        character_id: str,
        target_timestamp: int
    ) -> dict:
        """Compute character's knowledge state at a specific timestamp"""
        try:
            # Get all snapshots for this character up to the target timestamp
            result = self.db.table("knowledge_snapshots") \
                .select("*") \
                .eq("entity_id", character_id) \
                .lte("timestamp", target_timestamp) \
                .order("timestamp", desc=True) \
                .execute()
            
            if not result.data or len(result.data) == 0:
                return {"knowledge": {}, "timestamp": target_timestamp}
            
            # Start with the latest snapshot before or at target timestamp
            latest_snapshot = result.data[0]
            
            # For now, return the most recent snapshot
            # TODO: Implement more sophisticated merge logic if needed
            return {
                "knowledge": latest_snapshot.get("knowledge", {}),
                "timestamp": target_timestamp,
                "source_snapshot_id": latest_snapshot["id"],
                "source_timestamp": latest_snapshot.get("timestamp")
            }
        except Exception as e:
            logger.error(f"Compute knowledge at timestamp failed: {e}")
            raise
    
    def create_snapshot_from_scene(
        self, 
        character_id: str,
        scene_id: str,
        knowledge_updates: Dict[str, Any]
    ) -> dict:
        """Create knowledge snapshot linked to a scene's timestamp"""
        try:
            # Get scene timestamp
            scene_result = self.db.table("scenes") \
                .select("timestamp") \
                .eq("id", scene_id) \
                .execute()
            
            if not scene_result.data or len(scene_result.data) == 0:
                raise Exception("Scene not found")
            
            scene_timestamp = scene_result.data[0].get("timestamp")
            
            if scene_timestamp is None:
                raise Exception("Scene has no timestamp")
            
            # Get current knowledge at this timestamp
            current_knowledge = self.compute_knowledge_at_timestamp(character_id, scene_timestamp - 1)
            
            # Merge with updates
            updated_knowledge = current_knowledge["knowledge"].copy()
            updated_knowledge.update(knowledge_updates)
            
            # Create new snapshot
            snapshot_data = KnowledgeSnapshotCreate(
                entity_id=UUID(character_id),
                timestamp=scene_timestamp,
                knowledge=updated_knowledge,
                metadata={"source_scene_id": scene_id}
            )
            
            return self.create_knowledge_snapshot(snapshot_data)
        except Exception as e:
            logger.error(f"Create snapshot from scene failed: {e}")
            raise
    
    def check_character_knowledge(
        self, 
        character_id: str,
        knowledge_key: str,
        at_timestamp: Optional[int] = None
    ) -> Dict[str, Any]:
        """Check if character knows a specific fact at given time"""
        try:
            if at_timestamp is None:
                # Use latest knowledge if no timestamp specified
                result = self.db.table("knowledge_snapshots") \
                    .select("*") \
                    .eq("entity_id", character_id) \
                    .order("timestamp", desc=True) \
                    .limit(1) \
                    .execute()
            else:
                knowledge_state = self.compute_knowledge_at_timestamp(character_id, at_timestamp)
                result_data = [knowledge_state] if knowledge_state else []
                
                if result_data and "knowledge" in result_data[0]:
                    knowledge = result_data[0]["knowledge"]
                    knows_fact = knowledge_key in knowledge
                    return {
                        "knows": knows_fact,
                        "value": knowledge.get(knowledge_key) if knows_fact else None,
                        "timestamp": at_timestamp
                    }
                
                return {"knows": False, "value": None, "timestamp": at_timestamp}
            
            if not result.data or len(result.data) == 0:
                return {"knows": False, "value": None}
            
            knowledge = result.data[0].get("knowledge", {})
            knows_fact = knowledge_key in knowledge
            
            return {
                "knows": knows_fact,
                "value": knowledge.get(knowledge_key) if knows_fact else None,
                "timestamp": result.data[0].get("timestamp")
            }
        except Exception as e:
            logger.error(f"Check character knowledge failed: {e}")
            raise