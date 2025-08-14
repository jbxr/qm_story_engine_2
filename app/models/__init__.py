"""SQLModel schemas and database models for the story engine"""

# Database Models
from .entities import (
    Entity, Scene, SceneBlock,
    EntityRead, EntityCreate, EntityUpdate,
    SceneRead, SceneCreate,
    SceneBlockRead, SceneBlockCreate, SceneBlockUpdate,
    SceneBlockMoveRequest, BulkBlockCreateRequest
)
from .content import (
    DialogueBlock, Milestone,
    DialogueBlockRead, DialogueBlockCreate,
    MilestoneRead, MilestoneCreate
)
from .goals import (
    StoryGoal,
    StoryGoalRead, StoryGoalCreate, StoryGoalFulfill
)
from .knowledge import (
    KnowledgeAssertion,
    KnowledgeAssertionRead, KnowledgeAssertionCreate,
    KnowledgeSnapshot
)
from .relationships import (
    EventRelationship, Embedding,
    EventRelationshipRead, EventRelationshipCreate,
    EmbeddingRead,
    SemanticSearchRequest, SemanticSearchResult,
    ErrorResponse
)

# Type definitions
from .entities import EntityType, BlockType
from .knowledge import KnowledgePredicate, CertaintyLevel
from .relationships import RelationshipType, EmbeddingContentType

__all__ = [
    # Database Models
    "Entity", "Scene", "SceneBlock",
    "DialogueBlock", "Milestone",
    "StoryGoal", "KnowledgeAssertion",
    "EventRelationship", "Embedding",
    
    # API Models - Read
    "EntityRead", "SceneRead", "SceneBlockRead",
    "DialogueBlockRead", "MilestoneRead",
    "StoryGoalRead", "KnowledgeAssertionRead",
    "EventRelationshipRead", "EmbeddingRead",
    
    # API Models - Create/Update
    "EntityCreate", "EntityUpdate",
    "SceneCreate", "SceneBlockCreate", "SceneBlockUpdate",
    "DialogueBlockCreate", "MilestoneCreate",
    "StoryGoalCreate", "StoryGoalFulfill",
    "KnowledgeAssertionCreate", "EventRelationshipCreate",
    
    # Request Models
    "SceneBlockMoveRequest", "BulkBlockCreateRequest",
    "SemanticSearchRequest", "KnowledgeSnapshot",
    
    # Response Models
    "SemanticSearchResult", "ErrorResponse",
    
    # Type Definitions
    "EntityType", "BlockType",
    "KnowledgePredicate", "CertaintyLevel",
    "RelationshipType", "EmbeddingContentType",
]