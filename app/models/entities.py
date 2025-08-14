"""Core entity models aligned with new Supabase schema

Schema Alignment Notes:
- All models match the new Supabase schema structure
- INT timestamps for story timeline, datetime for database timestamps
- JSONB metadata fields throughout for extensibility  
- Vector embeddings handled by database triggers (not exposed in SQLModel)
- Milestones are first-class entities (separate table)
- Direct Supabase client operations (not SQLModel ORM)
- Models used for API validation only, not SQLAlchemy table generation

IMPORTANT: These models are for API request/response validation.
Database operations use direct Supabase client calls, not SQLModel ORM.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from uuid import UUID, uuid4
from enum import Enum


class EntityType(str, Enum):
    """Valid entity types - matches schema"""
    CHARACTER = "character"
    LOCATION = "location"
    ARTIFACT = "artifact"
    EVENT = "event"
    KNOWLEDGE_FACT = "knowledge_fact"


class BlockType(str, Enum):
    """Valid block types - matches schema"""
    PROSE = "prose"
    DIALOGUE = "dialogue"
    MILESTONE = "milestone"


# ============================================================================
# BASE MODELS FOR API - Aligned with Schema
# ============================================================================

class EntityBase(SQLModel):
    """Base model for all story entities - matches schema structure"""
    name: str = Field(min_length=1, max_length=200)
    entity_type: EntityType
    description: Optional[str] = Field(default=None)
    meta: Optional[Dict[str, Any]] = Field(default=None)


class SceneBase(SQLModel):
    """Base model for story scenes - matches schema structure"""
    title: str = Field(min_length=1, max_length=300)
    location_id: Optional[UUID] = Field(default=None)
    timestamp: Optional[int] = Field(default=None)  # INT timestamp as per schema


class SceneBlockBase(SQLModel):
    """Base model for content blocks within scenes - matches schema structure"""
    block_type: BlockType
    order: int = Field(ge=0)
    # Block-type specific fields (nullable as per schema)
    content: Optional[str] = Field(default=None)  # For prose blocks
    summary: Optional[str] = Field(default=None)  # For dialogue blocks
    lines: Optional[Dict[str, Any]] = Field(default=None)  # JSONB for dialogue lines
    subject_id: Optional[UUID] = Field(default=None)  # For milestone blocks
    verb: Optional[str] = Field(default=None)  # For milestone blocks
    object_id: Optional[UUID] = Field(default=None)  # For milestone blocks
    weight: Optional[float] = Field(default=None)
    meta: Optional[Dict[str, Any]] = Field(default=None)


# ============================================================================
# DATABASE MODELS - New Schema Structure
# ============================================================================

class Entity(EntityBase):
    """Characters, locations, artifacts, events, and knowledge facts"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Scene(SceneBase):
    """Story scenes with location and timestamp tracking"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SceneBlock(SceneBlockBase):
    """Unified content blocks supporting prose, dialogue, and milestones"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scene_id: UUID
    # Vector embedding for semantic search - handled by database triggers
    # Note: Vector embeddings are managed by database-side triggers and functions
    # embedding: VECTOR(1536) field exists in database but not exposed in SQLModel
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Milestone(SQLModel):
    """First-class milestone tracking table"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scene_id: UUID
    subject_id: Optional[UUID] = Field(default=None)
    verb: str = Field(min_length=1)
    object_id: Optional[UUID] = Field(default=None)
    description: Optional[str] = Field(default=None)
    weight: float = Field(default=1.0)
    meta: Optional[Dict[str, Any]] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeSnapshot(SQLModel):
    """Time-scoped knowledge states for entities"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    entity_id: UUID
    timestamp: Optional[int] = Field(default=None)  # INT timestamp
    knowledge: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    meta: Optional[Dict[str, Any]] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Relationship(SQLModel):
    """Entity relationships with weights and metadata (temporal support)"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_id: UUID
    target_id: UUID
    relation_type: Optional[str] = Field(default=None)
    weight: Optional[float] = Field(default=None)
    starts_at: Optional[int] = Field(default=None)  # Temporal start
    ends_at: Optional[int] = Field(default=None)    # Temporal end
    meta: Optional[Dict[str, Any]] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StoryGoal(SQLModel):
    """Narrative goals with milestone linkage"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    description: Optional[str] = Field(default=None)
    subject_id: Optional[UUID] = Field(default=None)
    verb: Optional[str] = Field(default=None)
    object_id: Optional[UUID] = Field(default=None)
    milestone_id: Optional[UUID] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DAGEdge(SQLModel):
    """Event graph connections"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    from_id: UUID
    to_id: UUID
    label: Optional[str] = Field(default=None)
    meta: Optional[Dict[str, Any]] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TimelineEvent(SQLModel):
    """Timeline-aware event tracking"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scene_id: Optional[UUID] = Field(default=None)
    entity_id: Optional[UUID] = Field(default=None)
    timestamp: Optional[int] = Field(default=None)  # INT timestamp
    summary: Optional[str] = Field(default=None)
    meta: Optional[Dict[str, Any]] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# API REQUEST/RESPONSE MODELS - New Schema
# ============================================================================

class EntityRead(EntityBase):
    """Read model for Entity API responses"""
    id: UUID
    created_at: datetime
    updated_at: datetime


class EntityCreate(EntityBase):
    """Create model for Entity API requests"""
    pass


class EntityUpdate(SQLModel):
    """Update model for Entity API requests"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    entity_type: Optional[EntityType] = None
    description: Optional[str] = Field(default=None)
    meta: Optional[Dict[str, Any]] = Field(default=None)


class SceneRead(SceneBase):
    """Read model for Scene API responses"""
    id: UUID
    created_at: datetime
    blocks: List["SceneBlockRead"] = []
    location_name: Optional[str] = None  # Resolved from location_id


class SceneCreate(SceneBase):
    """Create model for Scene API requests"""
    pass


class SceneUpdate(SQLModel):
    """Update model for Scene API requests"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    location_id: Optional[UUID] = Field(default=None)
    timestamp: Optional[int] = Field(default=None)


class SceneBlockRead(SceneBlockBase):
    """Read model for SceneBlock API responses"""
    id: UUID
    scene_id: UUID
    created_at: datetime
    updated_at: datetime
    # Resolved entity names for milestones
    subject_name: Optional[str] = None
    object_name: Optional[str] = None


class SceneBlockCreate(SceneBlockBase):
    """Create model for SceneBlock API requests"""
    scene_id: UUID


class SceneBlockUpdate(SQLModel):
    """Update model for SceneBlock API requests"""
    block_type: Optional[BlockType] = None
    order: Optional[int] = Field(default=None, ge=0)
    content: Optional[str] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    lines: Optional[Dict[str, Any]] = Field(default=None)
    subject_id: Optional[UUID] = Field(default=None)
    verb: Optional[str] = Field(default=None)
    object_id: Optional[UUID] = Field(default=None)
    weight: Optional[float] = Field(default=None)
    meta: Optional[Dict[str, Any]] = Field(default=None)


# Milestone API Models
class MilestoneRead(SQLModel):
    """Read model for Milestone API responses"""
    id: UUID
    scene_id: UUID
    subject_id: Optional[UUID]
    verb: str
    object_id: Optional[UUID]
    description: Optional[str]
    weight: float
    meta: Optional[Dict[str, Any]]
    created_at: datetime
    # Resolved names
    subject_name: Optional[str] = None
    object_name: Optional[str] = None
    scene_title: Optional[str] = None


class MilestoneCreate(SQLModel):
    """Create model for Milestone API requests"""
    scene_id: UUID
    subject_id: Optional[UUID] = None
    verb: str = Field(min_length=1)
    object_id: Optional[UUID] = None
    description: Optional[str] = None
    weight: float = 1.0
    meta: Optional[Dict[str, Any]] = None


class MilestoneUpdate(SQLModel):
    """Update model for Milestone API requests"""
    subject_id: Optional[UUID] = None
    verb: Optional[str] = Field(default=None, min_length=1)
    object_id: Optional[UUID] = None
    description: Optional[str] = None
    weight: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None


# Knowledge Snapshot API Models
class KnowledgeSnapshotRead(SQLModel):
    """Read model for KnowledgeSnapshot API responses"""
    id: UUID
    entity_id: UUID
    timestamp: Optional[int]
    knowledge: Dict[str, Any]
    meta: Optional[Dict[str, Any]]
    created_at: datetime
    entity_name: Optional[str] = None  # Resolved from entity_id


class KnowledgeSnapshotCreate(SQLModel):
    """Create model for KnowledgeSnapshot API requests"""
    entity_id: UUID
    timestamp: Optional[int] = None
    knowledge: Dict[str, Any] = Field(default_factory=dict)
    meta: Optional[Dict[str, Any]] = None


class KnowledgeSnapshotUpdate(SQLModel):
    """Update model for KnowledgeSnapshot API requests"""
    timestamp: Optional[int] = None
    knowledge: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None


# Story Goal API Models  
class StoryGoalRead(SQLModel):
    """Read model for StoryGoal API responses"""
    id: UUID
    description: Optional[str]
    subject_id: Optional[UUID]
    verb: Optional[str]
    object_id: Optional[UUID]
    milestone_id: Optional[UUID]
    created_at: datetime
    # Resolved names
    subject_name: Optional[str] = None
    object_name: Optional[str] = None
    milestone_description: Optional[str] = None


class StoryGoalCreate(SQLModel):
    """Create model for StoryGoal API requests"""
    description: Optional[str] = None
    subject_id: Optional[UUID] = None
    verb: Optional[str] = None
    object_id: Optional[UUID] = None
    milestone_id: Optional[UUID] = None


class StoryGoalUpdate(SQLModel):
    """Update model for StoryGoal API requests"""
    description: Optional[str] = None
    subject_id: Optional[UUID] = None
    verb: Optional[str] = None
    object_id: Optional[UUID] = None
    milestone_id: Optional[UUID] = None


# Utility Models
class SceneBlockMoveRequest(SQLModel):
    """Request model for reordering scene blocks"""
    new_order: int = Field(ge=0)


class BulkBlockCreateRequest(SQLModel):
    """Request model for creating multiple blocks at once"""
    blocks: List[SceneBlockCreate]


# Relationship API Models
class RelationshipCreate(BaseModel):
    """Create a new relationship with temporal support"""
    source_id: UUID
    target_id: UUID  
    relation_type: str
    weight: Optional[float] = 1.0
    starts_at: Optional[int] = None  # Temporal start
    ends_at: Optional[int] = None    # Temporal end
    meta: Optional[Dict[str, Any]] = {}


class RelationshipRead(BaseModel):
    """Relationship response model with API field mapping"""
    id: UUID
    subject_id: UUID  # API mapping from source_id
    object_id: UUID   # API mapping from target_id
    predicate: str    # API mapping from relation_type
    weight: Optional[float]
    starts_at: Optional[int]
    ends_at: Optional[int] 
    meta: Optional[Dict[str, Any]]
    created_at: datetime


class RelationshipUpdate(BaseModel):
    """Update relationship fields"""
    relation_type: Optional[str] = None
    weight: Optional[float] = None
    starts_at: Optional[int] = None
    ends_at: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None


class RelationshipBatchOperation(BaseModel):
    """Single operation in a batch request"""
    operation: str  # "create", "update", "delete"
    relationship_id: Optional[UUID] = None  # For update/delete
    data: Optional[Union[RelationshipCreate, RelationshipUpdate]] = None
