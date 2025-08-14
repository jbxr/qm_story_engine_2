"""
Complete SQLModel Schema Design for QuantumMateria Story Engine
Based on comprehensive analysis of all 9 specification documents
"""

from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship
from pgvector.sqlalchemy import Vector


# ============================================================================
# ENUMS AND TYPE DEFINITIONS
# ============================================================================

BlockType = Literal["prose", "dialogue", "milestone"]
EntityType = Literal["character", "location", "artifact", "concept"]
RelationshipType = Literal["causes", "knows_about", "located_at", "precedes", "fulfills"]
KnowledgePredicate = Literal["knows", "believes", "suspects", "doubts", "forgets"]
CertaintyLevel = Literal["true", "false", "uncertain"]


# ============================================================================
# CORE ENTITY MODELS
# ============================================================================

class EntityBase(SQLModel):
    """Base model for all story entities (characters, locations, artifacts)"""
    name: str = Field(min_length=1, max_length=200)
    entity_type: EntityType
    description: Optional[str] = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Entity(EntityBase, table=True):
    """Characters, locations, artifacts, and concepts in the story"""
    __tablename__ = "entities"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Relationships
    knowledge_assertions: List["KnowledgeAssertion"] = Relationship(
        back_populates="character", 
        sa_relationship_kwargs={"foreign_keys": "KnowledgeAssertion.character_id"}
    )
    story_goals_as_subject: List["StoryGoal"] = Relationship(
        back_populates="subject",
        sa_relationship_kwargs={"foreign_keys": "StoryGoal.subject_id"}
    )
    story_goals_as_object: List["StoryGoal"] = Relationship(
        back_populates="object",
        sa_relationship_kwargs={"foreign_keys": "StoryGoal.object_id"}
    )


class EntityRead(EntityBase):
    """Read model for Entity API responses"""
    id: UUID
    created_at: datetime


class EntityCreate(EntityBase):
    """Create model for Entity API requests"""
    pass


class EntityUpdate(SQLModel):
    """Update model for Entity API requests"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    entity_type: Optional[EntityType] = None
    description: Optional[str] = Field(default=None, max_length=2000)


# ============================================================================
# SCENE AND BLOCK MODELS
# ============================================================================

class SceneBase(SQLModel):
    """Base model for story scenes"""
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = Field(default=None, max_length=2000)
    timestamp: Optional[str] = Field(default=None, max_length=100)  # Flexible format per spec


class Scene(SceneBase, table=True):
    """Story scenes containing ordered blocks"""
    __tablename__ = "scenes"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    blocks: List["SceneBlock"] = Relationship(back_populates="scene")


class SceneRead(SceneBase):
    """Read model for Scene API responses"""
    id: UUID
    created_at: datetime
    blocks: List["SceneBlockRead"] = []


class SceneCreate(SceneBase):
    """Create model for Scene API requests"""
    pass


class SceneBlockBase(SQLModel):
    """Base model for content blocks within scenes"""
    block_type: BlockType
    content: str = Field(min_length=1)
    order: int = Field(ge=0)  # Zero-based ordering within scene


class SceneBlock(SceneBlockBase, table=True):
    """Content blocks within scenes (prose, dialogue, milestone)"""
    __tablename__ = "scene_blocks"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scene_id: UUID = Field(foreign_key="scenes.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    scene: Scene = Relationship(back_populates="blocks")
    dialogue: Optional["DialogueBlock"] = Relationship(back_populates="scene_block")
    milestone: Optional["Milestone"] = Relationship(back_populates="scene_block")
    knowledge_assertions: List["KnowledgeAssertion"] = Relationship(back_populates="source_block")
    embeddings: List["Embedding"] = Relationship(back_populates="scene_block")


class SceneBlockRead(SceneBlockBase):
    """Read model for SceneBlock API responses"""
    id: UUID
    scene_id: UUID
    created_at: datetime
    dialogue: Optional["DialogueBlockRead"] = None
    milestone: Optional["MilestoneRead"] = None


class SceneBlockCreate(SceneBlockBase):
    """Create model for SceneBlock API requests"""
    scene_id: UUID


class SceneBlockUpdate(SQLModel):
    """Update model for SceneBlock API requests"""
    content: Optional[str] = Field(default=None, min_length=1)
    order: Optional[int] = Field(default=None, ge=0)


# ============================================================================
# DIALOGUE MODELING
# ============================================================================

class DialogueBlockBase(SQLModel):
    """Base model for detailed dialogue blocks"""
    speaker_id: UUID = Field(foreign_key="entities.id")
    listener_ids: Optional[str] = Field(default=None)  # JSON array of UUIDs
    emotion: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class DialogueBlock(DialogueBlockBase, table=True):
    """Detailed dialogue information for dialogue scene blocks"""
    __tablename__ = "dialogue_blocks"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scene_block_id: UUID = Field(foreign_key="scene_blocks.id", unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    scene_block: SceneBlock = Relationship(back_populates="dialogue")
    speaker: Entity = Relationship()


class DialogueBlockRead(DialogueBlockBase):
    """Read model for DialogueBlock API responses"""
    id: UUID
    scene_block_id: UUID
    created_at: datetime
    speaker: EntityRead


class DialogueBlockCreate(DialogueBlockBase):
    """Create model for DialogueBlock API requests"""
    scene_block_id: UUID


# ============================================================================
# MILESTONE AND EVENT MODELING
# ============================================================================

class MilestoneBase(SQLModel):
    """Base model for structured story events"""
    subject_id: UUID = Field(foreign_key="entities.id")
    verb: str = Field(min_length=1, max_length=100)
    object_id: Optional[UUID] = Field(default=None, foreign_key="entities.id")
    timestamp: Optional[str] = Field(default=None, max_length=100)


class Milestone(MilestoneBase, table=True):
    """Structured story events (subject → verb → object)"""
    __tablename__ = "milestones"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scene_block_id: UUID = Field(foreign_key="scene_blocks.id", unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    scene_block: SceneBlock = Relationship(back_populates="milestone")
    subject: Entity = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Milestone.subject_id"}
    )
    object: Optional[Entity] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Milestone.object_id"}
    )
    fulfilled_goals: List["StoryGoal"] = Relationship(back_populates="linked_milestone")


class MilestoneRead(MilestoneBase):
    """Read model for Milestone API responses"""
    id: UUID
    scene_block_id: UUID
    created_at: datetime
    subject: EntityRead
    object: Optional[EntityRead] = None


class MilestoneCreate(MilestoneBase):
    """Create model for Milestone API requests"""
    scene_block_id: UUID


# ============================================================================
# STORY GOALS
# ============================================================================

class StoryGoalBase(SQLModel):
    """Base model for narrative goals"""
    subject_id: UUID = Field(foreign_key="entities.id")
    verb: str = Field(min_length=1, max_length=100)
    object_id: Optional[UUID] = Field(default=None, foreign_key="entities.id")
    description: Optional[str] = Field(default=None, max_length=1000)
    timestamp: Optional[str] = Field(default=None, max_length=100)  # Expected fulfillment time


class StoryGoal(StoryGoalBase, table=True):
    """Narrative objectives and goal tracking"""
    __tablename__ = "story_goals"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    fulfilled_at: Optional[datetime] = Field(default=None)
    linked_milestone_id: Optional[UUID] = Field(default=None, foreign_key="milestones.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    subject: Entity = Relationship(
        back_populates="story_goals_as_subject",
        sa_relationship_kwargs={"foreign_keys": "StoryGoal.subject_id"}
    )
    object: Optional[Entity] = Relationship(
        back_populates="story_goals_as_object",
        sa_relationship_kwargs={"foreign_keys": "StoryGoal.object_id"}
    )
    linked_milestone: Optional[Milestone] = Relationship(back_populates="fulfilled_goals")


class StoryGoalRead(StoryGoalBase):
    """Read model for StoryGoal API responses"""
    id: UUID
    fulfilled_at: Optional[datetime]
    linked_milestone_id: Optional[UUID]
    created_at: datetime
    subject: EntityRead
    object: Optional[EntityRead] = None
    linked_milestone: Optional[MilestoneRead] = None


class StoryGoalCreate(StoryGoalBase):
    """Create model for StoryGoal API requests"""
    pass


class StoryGoalFulfill(SQLModel):
    """Model for fulfilling a story goal"""
    linked_milestone_id: Optional[UUID] = None


# ============================================================================
# CHARACTER KNOWLEDGE SYSTEM
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


class KnowledgeAssertion(KnowledgeAssertionBase, table=True):
    """Character knowledge and beliefs over time"""
    __tablename__ = "knowledge_assertions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_block_id: Optional[UUID] = Field(default=None, foreign_key="scene_blocks.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    character: Entity = Relationship(back_populates="knowledge_assertions")
    source_block: Optional[SceneBlock] = Relationship(back_populates="knowledge_assertions")


class KnowledgeAssertionRead(KnowledgeAssertionBase):
    """Read model for KnowledgeAssertion API responses"""
    id: UUID
    source_block_id: Optional[UUID]
    created_at: datetime
    character: EntityRead
    source_block: Optional[SceneBlockRead] = None


class KnowledgeAssertionCreate(KnowledgeAssertionBase):
    """Create model for KnowledgeAssertion API requests"""
    source_block_id: Optional[UUID] = None


class KnowledgeSnapshot(SQLModel):
    """Computed view of character knowledge at a timestamp"""
    character_id: UUID
    timestamp: str
    assertions: List[KnowledgeAssertionRead]


# ============================================================================
# SEMANTIC GRAPH AND RELATIONSHIPS
# ============================================================================

class EventRelationshipBase(SQLModel):
    """Base model for semantic relationships between entities/events"""
    source_id: UUID = Field(foreign_key="entities.id")
    target_id: UUID = Field(foreign_key="entities.id")
    relationship_type: RelationshipType
    weight: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    description: Optional[str] = Field(default=None, max_length=500)


class EventRelationship(EventRelationshipBase, table=True):
    """Semantic relationships and causality graph edges"""
    __tablename__ = "event_relationships"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    source: Entity = Relationship(
        sa_relationship_kwargs={"foreign_keys": "EventRelationship.source_id"}
    )
    target: Entity = Relationship(
        sa_relationship_kwargs={"foreign_keys": "EventRelationship.target_id"}
    )


class EventRelationshipRead(EventRelationshipBase):
    """Read model for EventRelationship API responses"""
    id: UUID
    created_at: datetime
    source: EntityRead
    target: EntityRead


class EventRelationshipCreate(EventRelationshipBase):
    """Create model for EventRelationship API requests"""
    pass


# ============================================================================
# SEMANTIC SEARCH AND EMBEDDINGS
# ============================================================================

class EmbeddingBase(SQLModel):
    """Base model for vector embeddings"""
    content_type: Literal["scene_block", "milestone", "goal", "entity"]
    embedding: List[float] = Field(sa_column=Vector(1536))  # OpenAI embedding size


class Embedding(EmbeddingBase, table=True):
    """Vector embeddings for semantic search"""
    __tablename__ = "embeddings"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scene_block_id: Optional[UUID] = Field(default=None, foreign_key="scene_blocks.id")
    milestone_id: Optional[UUID] = Field(default=None, foreign_key="milestones.id")
    goal_id: Optional[UUID] = Field(default=None, foreign_key="story_goals.id")
    entity_id: Optional[UUID] = Field(default=None, foreign_key="entities.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    scene_block: Optional[SceneBlock] = Relationship(back_populates="embeddings")


class EmbeddingRead(EmbeddingBase):
    """Read model for Embedding API responses"""
    id: UUID
    scene_block_id: Optional[UUID]
    milestone_id: Optional[UUID]
    goal_id: Optional[UUID]
    entity_id: Optional[UUID]
    created_at: datetime


class SemanticSearchRequest(SQLModel):
    """Request model for semantic search"""
    query: str = Field(min_length=1)
    content_types: Optional[List[Literal["scene_block", "milestone", "goal", "entity"]]] = None
    limit: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class SemanticSearchResult(SQLModel):
    """Response model for semantic search"""
    content_id: UUID
    content_type: str
    similarity_score: float
    content: str
    metadata: dict = {}


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class SceneBlockMoveRequest(SQLModel):
    """Request model for reordering scene blocks"""
    new_order: int = Field(ge=0)


class BulkBlockCreateRequest(SQLModel):
    """Request model for creating multiple blocks at once"""
    blocks: List[SceneBlockCreate]


class ErrorResponse(SQLModel):
    """Standard error response model"""
    error: str
    details: Optional[str] = None
    code: Optional[str] = None


# ============================================================================
# LLM INTEGRATION MODELS
# ============================================================================

class LLMContextRequest(SQLModel):
    """Request model for LLM context generation"""
    timestamp: str
    character_ids: Optional[List[UUID]] = None
    include_goals: bool = True
    include_knowledge: bool = True


class LLMContextResponse(SQLModel):
    """Response model for LLM context"""
    timeline_events: List[MilestoneRead]
    character_knowledge: List[KnowledgeSnapshot]
    active_goals: List[StoryGoalRead]
    scene_context: List[SceneRead]


class SceneSuggestionRequest(SQLModel):
    """Request model for LLM scene suggestions"""
    goal_id: UUID
    max_suggestions: int = Field(default=3, ge=1, le=5)
    tone: Optional[str] = None
    constraints: Optional[str] = None


class SceneSuggestion(SQLModel):
    """Individual scene suggestion from LLM"""
    title: str
    description: str
    proposed_blocks: List[dict]  # Flexible structure for different block types
    rationale: str


class SceneSuggestionResponse(SQLModel):
    """Response model for LLM scene suggestions"""
    goal: StoryGoalRead
    suggestions: List[SceneSuggestion]


class BlockRewriteRequest(SQLModel):
    """Request model for LLM block rewriting"""
    block_id: UUID
    prompt: Optional[str] = None
    preserve_structure: bool = True


class BlockRewriteResponse(SQLModel):
    """Response model for LLM block rewriting"""
    original_content: str
    rewritten_content: str
    changes_summary: str


class ContinuityCheckRequest(SQLModel):
    """Request model for LLM continuity checking"""
    scene_id: UUID
    check_knowledge: bool = True
    check_timeline: bool = True
    check_character_voice: bool = True


class ContinuityIssue(SQLModel):
    """Individual continuity issue"""
    type: Literal["knowledge", "timeline", "character_voice", "other"]
    severity: Literal["low", "medium", "high"]
    description: str
    suggested_fix: Optional[str] = None
    affected_block_id: Optional[UUID] = None


class ContinuityCheckResponse(SQLModel):
    """Response model for LLM continuity checking"""
    scene: SceneRead
    issues: List[ContinuityIssue]
    overall_score: float = Field(ge=0.0, le=1.0)