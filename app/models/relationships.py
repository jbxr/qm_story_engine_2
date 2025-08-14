"""Semantic relationships and embedding models"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING, Any
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON as SQLAlchemyJSON
from uuid import UUID, uuid4
from enum import Enum

if TYPE_CHECKING:
    from .entities import Entity, SceneBlock, EntityRead
    from .content import Milestone
    from .goals import StoryGoal


class RelationshipType(str, Enum):
    """Relationship types for semantic graph"""
    CAUSES = "causes"
    KNOWS_ABOUT = "knows_about"
    LOCATED_AT = "located_at"
    PRECEDES = "precedes"
    FULFILLS = "fulfills"


class EmbeddingContentType(str, Enum):
    """Content types for embeddings"""
    SCENE_BLOCK = "scene_block"
    MILESTONE = "milestone"
    GOAL = "goal"
    ENTITY = "entity"


# ============================================================================
# BASE MODELS FOR API
# ============================================================================

class EventRelationshipBase(SQLModel):
    """Base model for semantic relationships between entities/events"""
    source_id: UUID = Field(foreign_key="entities.id")
    target_id: UUID = Field(foreign_key="entities.id")
    relationship_type: RelationshipType
    weight: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    description: Optional[str] = Field(default=None, max_length=500)


class EmbeddingBase(SQLModel):
    """Base model for vector embeddings"""
    content_type: EmbeddingContentType
    # Note: embedding field defined separately in table class due to pgvector requirement


# ============================================================================
# DATABASE MODELS
# ============================================================================

class EventRelationship(EventRelationshipBase, table=True):
    """Semantic relationships between entities in the story world"""
    
    __tablename__ = "event_relationships"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    source: "Entity" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "EventRelationship.source_id"}
    )
    target: "Entity" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "EventRelationship.target_id"}
    )


class Embedding(SQLModel, table=True):
    """Vector embeddings for semantic search across all content types"""
    
    __tablename__ = "embeddings"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    content_type: EmbeddingContentType
    embedding: Any = Field(sa_column=Column(SQLAlchemyJSON))  # Vector embeddings stored as JSON
    scene_block_id: Optional[UUID] = Field(default=None, foreign_key="scene_blocks.id")
    milestone_id: Optional[UUID] = Field(default=None, foreign_key="milestones.id")
    goal_id: Optional[UUID] = Field(default=None, foreign_key="story_goals.id")
    entity_id: Optional[UUID] = Field(default=None, foreign_key="entities.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    scene_block: Optional["SceneBlock"] = Relationship(back_populates="embeddings")
    
    def get_content_id(self) -> Optional[UUID]:
        """Get the content ID based on content type"""
        return {
            "scene_block": self.scene_block_id,
            "milestone": self.milestone_id,
            "goal": self.goal_id,
            "entity": self.entity_id,
        }.get(self.content_type)
    
    def set_content_id(self, content_id: UUID) -> None:
        """Set the appropriate content ID based on content type"""
        # Clear all other content IDs
        self.scene_block_id = None
        self.milestone_id = None
        self.goal_id = None
        self.entity_id = None
        
        # Set the correct one
        if self.content_type == "scene_block":
            self.scene_block_id = content_id
        elif self.content_type == "milestone":
            self.milestone_id = content_id
        elif self.content_type == "goal":
            self.goal_id = content_id
        elif self.content_type == "entity":
            self.entity_id = content_id


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class EventRelationshipRead(EventRelationshipBase):
    """Read model for EventRelationship API responses"""
    id: UUID
    created_at: datetime
    source: "EntityRead"
    target: "EntityRead"


class EventRelationshipCreate(EventRelationshipBase):
    """Create model for EventRelationship API requests"""
    pass


class EmbeddingRead(SQLModel):
    """Read model for Embedding API responses"""
    id: UUID
    content_type: EmbeddingContentType
    embedding: List[float]
    scene_block_id: Optional[UUID]
    milestone_id: Optional[UUID]
    goal_id: Optional[UUID]
    entity_id: Optional[UUID]
    created_at: datetime


# ============================================================================
# SEARCH MODELS
# ============================================================================

class SemanticSearchRequest(SQLModel):
    """Request model for semantic search"""
    query: str = Field(min_length=1)
    content_types: Optional[List[EmbeddingContentType]] = None
    limit: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class SemanticSearchResult(SQLModel):
    """Response model for semantic search"""
    content_id: UUID
    content_type: str
    similarity_score: float
    content: str
    extra_data: dict = {}


# ============================================================================
# ERROR RESPONSE MODEL
# ============================================================================

class ErrorResponse(SQLModel):
    """Standard error response model"""
    error: str
    details: Optional[str] = None
    code: Optional[str] = None