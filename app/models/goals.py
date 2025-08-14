"""Story goal tracking models"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .entities import Entity, EntityRead
    from .content import Milestone, MilestoneRead
    from .relationships import Embedding


# ============================================================================
# BASE MODELS FOR API
# ============================================================================

class StoryGoalBase(SQLModel):
    """Base model for narrative goals"""
    subject_id: UUID = Field(foreign_key="entities.id")
    verb: str = Field(min_length=1, max_length=100)
    object_id: Optional[UUID] = Field(default=None, foreign_key="entities.id")
    description: Optional[str] = Field(default=None, max_length=1000)
    timestamp: Optional[str] = Field(default=None, max_length=100)  # Expected fulfillment time


# ============================================================================
# DATABASE MODELS
# ============================================================================


class StoryGoal(StoryGoalBase, table=True):
    """Narrative objectives and their fulfillment tracking"""
    
    __tablename__ = "story_goals"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    fulfilled_at: Optional[datetime] = Field(default=None)
    linked_milestone_id: Optional[UUID] = Field(default=None, foreign_key="milestones.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    subject: "Entity" = Relationship(
        back_populates="story_goals_as_subject",
        sa_relationship_kwargs={"foreign_keys": "StoryGoal.subject_id"}
    )
    object: Optional["Entity"] = Relationship(
        back_populates="story_goals_as_object",
        sa_relationship_kwargs={"foreign_keys": "StoryGoal.object_id"}
    )
    linked_milestone: Optional["Milestone"] = Relationship(
        back_populates="fulfilled_goals"
    )
    
    @property
    def is_fulfilled(self) -> bool:
        """Check if goal has been fulfilled"""
        return self.fulfilled_at is not None
    
    def fulfill(self, milestone_id: Optional[UUID] = None) -> None:
        """Mark goal as fulfilled"""
        self.fulfilled_at = datetime.utcnow()
        if milestone_id:
            self.linked_milestone_id = milestone_id


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class StoryGoalRead(StoryGoalBase):
    """Read model for StoryGoal API responses"""
    id: UUID
    fulfilled_at: Optional[datetime]
    linked_milestone_id: Optional[UUID]
    created_at: datetime
    subject: "EntityRead"
    object: Optional["EntityRead"] = None
    linked_milestone: Optional["MilestoneRead"] = None


class StoryGoalCreate(StoryGoalBase):
    """Create model for StoryGoal API requests"""
    pass


class StoryGoalFulfill(SQLModel):
    """Model for fulfilling a story goal"""
    linked_milestone_id: Optional[UUID] = None