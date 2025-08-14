"""Pydantic models for API requests and responses - New Schema"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

from .entities import EntityType, BlockType


# Base response models
class BaseResponse(BaseModel):
    """Base response model with common fields"""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 50
    has_next: bool = False
    has_prev: bool = False


# Entity API models - New Schema
class EntityCreate(BaseModel):
    """Create entity request"""
    name: str = Field(max_length=255)
    entity_type: EntityType
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EntityUpdate(BaseModel):
    """Update entity request"""
    name: Optional[str] = Field(None, max_length=255)
    entity_type: Optional[EntityType] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EntityResponse(BaseModel):
    """Entity response model"""
    id: UUID
    name: str
    entity_type: EntityType
    description: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# Scene API models - New Schema
class SceneCreate(BaseModel):
    """Create scene request"""
    title: str = Field(max_length=255)
    location_id: Optional[UUID] = None
    timestamp: Optional[int] = None  # INT timestamp as per schema


class SceneUpdate(BaseModel):
    """Update scene request"""
    title: Optional[str] = Field(None, max_length=255)
    location_id: Optional[UUID] = None
    timestamp: Optional[int] = None


class SceneResponse(BaseModel):
    """Scene response model"""
    id: UUID
    title: str
    location_id: Optional[UUID]
    timestamp: Optional[int]
    created_at: datetime
    block_count: int = 0
    location_name: Optional[str] = None  # Resolved from location_id


class SceneDetailResponse(SceneResponse):
    """Detailed scene response with blocks"""
    blocks: List["SceneBlockResponse"] = []


# Scene Block API models - New Schema
class SceneBlockCreate(BaseModel):
    """Create scene block request"""
    scene_id: UUID
    block_type: BlockType
    order: int = Field(ge=0)
    # Block-type specific fields
    content: Optional[str] = None  # For prose blocks
    summary: Optional[str] = None  # For dialogue blocks
    lines: Optional[Dict[str, Any]] = None  # JSONB for dialogue lines
    subject_id: Optional[UUID] = None  # For milestone blocks
    verb: Optional[str] = None  # For milestone blocks
    object_id: Optional[UUID] = None  # For milestone blocks
    weight: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class SceneBlockUpdate(BaseModel):
    """Update scene block request"""
    block_type: Optional[BlockType] = None
    order: Optional[int] = Field(None, ge=0)
    content: Optional[str] = None
    summary: Optional[str] = None
    lines: Optional[Dict[str, Any]] = None
    subject_id: Optional[UUID] = None
    verb: Optional[str] = None
    object_id: Optional[UUID] = None
    weight: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class SceneBlockMove(BaseModel):
    """Move scene block request"""
    new_order: int


class SceneBlockResponse(BaseModel):
    """Scene block response model"""
    id: UUID
    scene_id: UUID
    block_type: BlockType
    order: int
    # Block-type specific fields
    content: Optional[str]
    summary: Optional[str]
    lines: Optional[Dict[str, Any]]
    subject_id: Optional[UUID]
    verb: Optional[str]
    object_id: Optional[UUID]
    weight: Optional[float]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    # Resolved entity names for milestones
    subject_name: Optional[str] = None
    object_name: Optional[str] = None


# Milestone API models - First-Class Table
class MilestoneCreate(BaseModel):
    """Create milestone request"""
    scene_id: UUID
    subject_id: Optional[UUID] = None
    verb: str = Field(min_length=1)
    object_id: Optional[UUID] = None
    description: Optional[str] = None
    weight: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class MilestoneUpdate(BaseModel):
    """Update milestone request"""
    subject_id: Optional[UUID] = None
    verb: Optional[str] = Field(None, min_length=1)
    object_id: Optional[UUID] = None
    description: Optional[str] = None
    weight: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class MilestoneResponse(BaseModel):
    """Milestone response model"""
    id: UUID
    scene_id: UUID
    subject_id: Optional[UUID]
    verb: str
    object_id: Optional[UUID]
    description: Optional[str]
    weight: float
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    # Resolved names
    subject_name: Optional[str] = None
    object_name: Optional[str] = None
    scene_title: Optional[str] = None


# Knowledge Snapshot API models - New Schema
class KnowledgeSnapshotCreate(BaseModel):
    """Create knowledge snapshot request"""
    entity_id: UUID
    timestamp: Optional[int] = None  # INT timestamp
    knowledge: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeSnapshotUpdate(BaseModel):
    """Update knowledge snapshot request"""
    timestamp: Optional[int] = None
    knowledge: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeSnapshotResponse(BaseModel):
    """Knowledge snapshot response model"""
    id: UUID
    entity_id: UUID
    timestamp: Optional[int]
    knowledge: Dict[str, Any]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    entity_name: Optional[str] = None  # Resolved from entity_id


# Story Goal API models - New Schema
class StoryGoalCreate(BaseModel):
    """Create story goal request"""
    description: Optional[str] = None
    subject_id: Optional[UUID] = None
    verb: Optional[str] = None
    object_id: Optional[UUID] = None
    milestone_id: Optional[UUID] = None


class StoryGoalUpdate(BaseModel):
    """Update story goal request"""
    description: Optional[str] = None
    subject_id: Optional[UUID] = None
    verb: Optional[str] = None
    object_id: Optional[UUID] = None
    milestone_id: Optional[UUID] = None


class StoryGoalResponse(BaseModel):
    """Story goal response model"""
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


# Enhanced Temporal Relationship API models
class RelationshipCreate(BaseModel):
    """Create temporal relationship request"""
    subject_id: UUID
    object_id: UUID
    predicate: str = Field(min_length=1, max_length=100, description="Relationship type (causes, knows_about, located_at, etc.)")
    strength: float = Field(default=1.0, ge=0.0, le=1.0, description="Relationship strength from 0.0 to 1.0")
    starts_at: Optional[int] = Field(default=None, description="Timeline start (NULL for timeless relationships)")
    ends_at: Optional[int] = Field(default=None, description="Timeline end (NULL for ongoing relationships)")
    metadata: Optional[Dict[str, Any]] = None


class RelationshipUpdate(BaseModel):
    """Update temporal relationship request"""
    predicate: Optional[str] = Field(None, min_length=1, max_length=100)
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    starts_at: Optional[int] = None
    ends_at: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class RelationshipResponse(BaseModel):
    """Temporal relationship response model"""
    id: UUID
    subject_id: UUID
    object_id: UUID
    predicate: str
    strength: float
    starts_at: Optional[int]
    ends_at: Optional[int]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    # Resolved names
    subject_name: Optional[str] = None
    object_name: Optional[str] = None


class RelationshipSearchRequest(BaseModel):
    """Search relationships with temporal and strength filters"""
    predicate_filter: Optional[str] = Field(default=None, description="Filter by relationship predicate")
    min_strength: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum relationship strength")
    at_timestamp: Optional[int] = Field(default=None, description="Filter active relationships at specific timestamp")
    limit: int = Field(default=100, le=1000, description="Maximum number of results")


class RelationshipBetweenRequest(BaseModel):
    """Find relationships between two entities"""
    subject_id: UUID
    object_id: UUID
    at_timestamp: Optional[int] = Field(default=None, description="Filter active relationships at specific timestamp")
    include_reverse: bool = Field(default=True, description="Include reverse relationships (object->subject)")


class MultiHopTraversalRequest(BaseModel):
    """Multi-hop relationship traversal request"""
    start_entity_id: UUID
    max_hops: int = Field(default=3, ge=1, le=10, description="Maximum number of hops to traverse")
    at_timestamp: Optional[int] = Field(default=None, description="Filter active relationships at specific timestamp")
    min_strength: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum relationship strength threshold")


class RelatedEntityResult(BaseModel):
    """Result item for multi-hop traversal"""
    entity_id: UUID
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None
    hop_count: int
    relationship_path: str
    total_strength: float


# Enhanced Search API models - Timeline-Aware Search
class SemanticSearchRequest(BaseModel):
    """Semantic search request using pgvector"""
    query: str
    match_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    match_count: int = Field(default=10, le=100)


class TextSearchRequest(BaseModel):
    """Full-text search request"""
    query: str
    content_types: Optional[List[str]] = Field(default=None, description="Filter by content types")
    limit: int = Field(default=50, le=200)


class TimelineSearchRequest(BaseModel):
    """Timeline-aware story world search"""
    at_timestamp: int = Field(description="Timestamp to query story world state")
    entity_ids: Optional[List[UUID]] = Field(default=None, description="Filter by specific entities")
    include_relationships: bool = Field(default=True, description="Include entity relationships")
    include_knowledge: bool = Field(default=True, description="Include knowledge snapshots")
    include_scenes: bool = Field(default=True, description="Include active scenes")


class EntitySearchRequest(BaseModel):
    """Search entities with relationship context"""
    query: str
    entity_types: Optional[List[str]] = Field(default=None, description="Filter by entity types")
    at_timestamp: Optional[int] = Field(default=None, description="Include relationship context at timestamp")
    include_related: bool = Field(default=False, description="Include related entities")
    max_hops: int = Field(default=1, ge=1, le=3, description="Maximum relationship hops if include_related=True")
    limit: int = Field(default=50, le=200)


class KnowledgeSearchRequest(BaseModel):
    """Search knowledge snapshots with context"""
    query: str
    entity_ids: Optional[List[UUID]] = Field(default=None, description="Filter by specific entities")
    timestamp_range: Optional[List[int]] = Field(default=None, description="[start, end] timestamp range")
    include_entity_context: bool = Field(default=True, description="Include entity details and relationships")
    limit: int = Field(default=50, le=200)


class ComplexQueryRequest(BaseModel):
    """Complex multi-entity temporal query"""
    entities: List[UUID] = Field(description="Entities to include in query")
    at_timestamp: Optional[int] = Field(default=None, description="Timestamp for temporal consistency")
    include_relationships: bool = Field(default=True, description="Include relationships between entities")
    include_knowledge: bool = Field(default=True, description="Include knowledge states")
    include_scenes: bool = Field(default=True, description="Include scenes involving entities")
    relationship_depth: int = Field(default=1, ge=1, le=3, description="Relationship traversal depth")


class SearchResult(BaseModel):
    """Enhanced search result item"""
    id: UUID
    content_type: str = Field(description="Type of content (scene_block, entity, relationship, knowledge)")
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    similarity: Optional[float] = None
    relevance_score: float = Field(description="Overall relevance score")
    metadata: Optional[Dict[str, Any]] = None
    # Context information
    scene_id: Optional[UUID] = None
    entity_ids: Optional[List[UUID]] = None
    timestamp: Optional[int] = None


class TimelineSearchResult(BaseModel):
    """Timeline search result with story world state"""
    timestamp: int
    entities: List[Dict[str, Any]] = Field(description="Entity states at timestamp")
    relationships: List[RelationshipResponse] = Field(description="Active relationships")
    knowledge_snapshots: List[Dict[str, Any]] = Field(description="Knowledge states")
    active_scenes: List[Dict[str, Any]] = Field(description="Scenes active at timestamp")


class SearchResponse(BaseModel):
    """Enhanced search results response"""
    results: List[SearchResult]
    total: int
    query: str
    search_type: str = Field(description="Type of search performed")
    execution_time_ms: Optional[float] = None
    # Timeline context if applicable
    timeline_context: Optional[Dict[str, Any]] = None


# Timeline Event API models - New Schema
class TimelineEventCreate(BaseModel):
    """Create timeline event request"""
    scene_id: Optional[UUID] = None
    entity_id: Optional[UUID] = None
    timestamp: Optional[int] = None  # INT timestamp
    summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TimelineEventUpdate(BaseModel):
    """Update timeline event request"""
    timestamp: Optional[int] = None
    summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TimelineEventResponse(BaseModel):
    """Timeline event response model"""
    id: UUID
    scene_id: Optional[UUID]
    entity_id: Optional[UUID]
    timestamp: Optional[int]
    summary: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    # Resolved names
    scene_title: Optional[str] = None
    entity_name: Optional[str] = None


# DAG Edge API models - New Schema  
class DAGEdgeCreate(BaseModel):
    """Create DAG edge request"""
    from_id: UUID
    to_id: UUID
    label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DAGEdgeResponse(BaseModel):
    """DAG edge response model"""
    id: UUID
    from_id: UUID
    to_id: UUID
    label: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime


# Content Operation API models - Advanced Scene Block Operations
class BlockBatchCreate(BaseModel):
    """Batch create multiple scene blocks"""
    scene_id: UUID
    blocks: List[SceneBlockCreate]


class BlockBatchUpdate(BaseModel):
    """Batch update multiple scene blocks"""
    updates: List[Dict[str, Any]]  # [{id: UUID, updates: {...}}]


class BlockReorder(BaseModel):
    """Reorder blocks within a scene"""
    scene_id: UUID
    block_order: Dict[str, int]  # {block_id: new_order}


class BlockDuplicate(BaseModel):
    """Duplicate block with modifications"""
    modifications: Optional[Dict[str, Any]] = None


class BlockMerge(BaseModel):
    """Merge multiple blocks into one"""
    target_block_id: UUID
    source_block_ids: List[UUID]
    merge_strategy: str = "concatenate"  # "concatenate", "replace", "custom"


class ContentSearchRequest(BaseModel):
    """Search blocks by content/metadata"""
    query: str
    scene_id: Optional[UUID] = None
    block_types: Optional[List[BlockType]] = None
    metadata_filters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=50, le=500)


class ContentSearchResult(BaseModel):
    """Content search result item"""
    block_id: UUID
    scene_id: UUID
    block_type: BlockType
    order: int
    content_snippet: Optional[str] = None
    match_score: float
    scene_title: Optional[str] = None


class ContentSearchResponse(BaseModel):
    """Content search results"""
    results: List[ContentSearchResult]
    total: int
    query: str


class ValidationRule(BaseModel):
    """Validation rule result"""
    rule_name: str
    passed: bool
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Scene content validation result"""
    scene_id: UUID
    valid: bool
    rules_checked: int
    rules_passed: int
    issues: List[ValidationRule]


class BatchOperationResult(BaseModel):
    """Result of batch operations"""
    success: bool
    processed: int
    failed: int
    created_blocks: Optional[List[SceneBlockResponse]] = None
    updated_blocks: Optional[List[SceneBlockResponse]] = None
    errors: Optional[List[str]] = None


# Forward reference updates for Pydantic
SceneDetailResponse.model_rebuild()