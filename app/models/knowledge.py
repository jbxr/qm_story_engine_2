"""Character knowledge and belief tracking models"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from enum import Enum

if TYPE_CHECKING:
    from .entities import Entity, SceneBlock, EntityRead, SceneBlockRead


class KnowledgePredicate(str, Enum):
    """Knowledge predicates (what characters think about facts)"""
    KNOWS = "knows"
    BELIEVES = "believes"
    SUSPECTS = "suspects"
    DOUBTS = "doubts"
    FORGETS = "forgets"


class CertaintyLevel(str, Enum):
    """Certainty levels for knowledge assertions"""
    TRUE = "true"
    FALSE = "false"
    UNCERTAIN = "uncertain"


# ============================================================================
# BASE MODELS FOR API
# ============================================================================

class KnowledgeAssertionBase(SQLModel):
    """Base model for character knowledge over time"""
    character_id: UUID = Field(foreign_key="entities.id")
    predicate: KnowledgePredicate
    fact_subject: str = Field(min_length=1, max_length=200)
    fact_verb: str = Field(min_length=1, max_length=100)
    fact_object: Optional[str] = Field(default=None, max_length=200)
    timestamp: str = Field(min_length=1, max_length=100)
    certainty: CertaintyLevel


# ============================================================================
# DATABASE MODELS
# ============================================================================

class KnowledgeAssertion(KnowledgeAssertionBase, table=True):
    """Character knowledge state over time"""
    
    __tablename__ = "knowledge_assertions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_block_id: Optional[UUID] = Field(default=None, foreign_key="scene_blocks.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    character: "Entity" = Relationship(back_populates="knowledge_assertions")
    source_block: Optional["SceneBlock"] = Relationship(
        back_populates="knowledge_assertions"
    )
    
    @property
    def fact_string(self) -> str:
        """Get formatted fact string"""
        parts = [self.fact_subject, self.fact_verb, self.fact_object]
        return " ".join(part for part in parts if part)
    
    def __str__(self) -> str:
        """Human readable representation"""
        return f"{self.character.name} {self.predicate} that {self.fact_string}"


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class KnowledgeAssertionRead(KnowledgeAssertionBase):
    """Read model for KnowledgeAssertion API responses"""
    id: UUID
    source_block_id: Optional[UUID]
    created_at: datetime
    character: "EntityRead"
    source_block: Optional["SceneBlockRead"] = None


class KnowledgeAssertionCreate(KnowledgeAssertionBase):
    """Create model for KnowledgeAssertion API requests"""
    source_block_id: Optional[UUID] = None


class KnowledgeSnapshot(SQLModel):
    """Computed view of character knowledge at a timestamp"""
    character_id: UUID
    timestamp: str
    assertions: List[KnowledgeAssertionRead]