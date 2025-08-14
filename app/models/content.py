"""Content-specific models: DialogueBlock, Milestone"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .entities import Entity, SceneBlock, EntityRead
    from .goals import StoryGoal
    from .relationships import Embedding


# ============================================================================
# BASE MODELS FOR API
# ============================================================================

class DialogueBlockBase(SQLModel):
    """Base model for detailed dialogue blocks"""
    speaker_id: UUID = Field(foreign_key="entities.id")
    listener_ids: Optional[str] = Field(default=None)  # JSON array of UUIDs
    emotion: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class MilestoneBase(SQLModel):
    """Base model for structured story events"""
    subject_id: UUID = Field(foreign_key="entities.id")
    verb: str = Field(min_length=1, max_length=100)
    object_id: Optional[UUID] = Field(default=None, foreign_key="entities.id")
    timestamp: Optional[str] = Field(default=None, max_length=100)


# ============================================================================
# DATABASE MODELS
# ============================================================================


class DialogueBlock(DialogueBlockBase, table=True):
    """Detailed dialogue information for dialogue-type scene blocks"""
    
    __tablename__ = "dialogue_blocks"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scene_block_id: UUID = Field(foreign_key="scene_blocks.id", unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    scene_block: "SceneBlock" = Relationship(back_populates="dialogue")
    speaker: "Entity" = Relationship()


class Milestone(MilestoneBase, table=True):
    """Structured story events for milestone-type scene blocks"""
    
    __tablename__ = "milestones"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scene_block_id: UUID = Field(foreign_key="scene_blocks.id", unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    scene_block: "SceneBlock" = Relationship(back_populates="milestone")
    subject: "Entity" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Milestone.subject_id"}
    )
    object: Optional["Entity"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Milestone.object_id"}
    )
    fulfilled_goals: List["StoryGoal"] = Relationship(
        back_populates="linked_milestone"
    )


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class DialogueBlockRead(DialogueBlockBase):
    """Read model for DialogueBlock API responses"""
    id: UUID
    scene_block_id: UUID
    created_at: datetime
    speaker: "EntityRead"


class DialogueBlockCreate(DialogueBlockBase):
    """Create model for DialogueBlock API requests"""
    scene_block_id: UUID


class MilestoneRead(MilestoneBase):
    """Read model for Milestone API responses"""
    id: UUID
    scene_block_id: UUID
    created_at: datetime
    subject: "EntityRead"
    object: Optional["EntityRead"] = None


class MilestoneCreate(MilestoneBase):
    """Create model for Milestone API requests"""
    scene_block_id: UUID