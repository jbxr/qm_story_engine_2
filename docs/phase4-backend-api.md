# Phase 4 Backend API Documentation

## Overview

Phase 4 introduces AI-powered storytelling features including multi-provider LLM integration, semantic search with pgvector, and timeline-aware narrative assistance. All features are accessible via REST API endpoints.

## API Base URL

```
http://localhost:8000
```

## Authentication

Currently using Supabase service key authentication. Ensure `SUPABASE_SERVICE_KEY` is configured in your environment.

---

## LLM Integration Endpoints

### 1. Generate Content

**POST** `/llm/generate`

Generate content using AI with multi-provider support (OpenAI, Groq, Gemini).

#### Request Body

```json
{
  "prompt": "Write a brief story about a wizard and apprentice.",
  "provider": "auto",  // "auto" | "openai" | "groq" | "gemini"
  "model": null,       // Optional specific model
  "max_tokens": 1000,
  "temperature": 0.7,
  "system_prompt": "You are a fantasy storytelling assistant."
}
```

#### Response

```json
{
  "success": true,
  "content": "In the ancient tower overlooking the mystical valley...",
  "provider_used": "openai",
  "model_used": "gpt-4o-mini",
  "token_count": 156
}
```

#### curl Example

```bash
curl -X POST http://localhost:8000/llm/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Describe a magical library scene",
    "max_tokens": 200,
    "temperature": 0.8
  }'
```

### 2. Analyze Narrative Consistency

**POST** `/llm/analyze`

Analyze content for narrative consistency issues using character knowledge and timeline context.

#### Request Body

```json
{
  "content": "The young apprentice cast a powerful lightning spell.",
  "character_id": "123e4567-e89b-12d3-a456-426614174000",
  "timeline_timestamp": 1100
}
```

#### Response

```json
{
  "success": true,
  "analysis": {
    "content": "The young apprentice cast a powerful lightning spell.",
    "analysis": "This scene shows inconsistency with character knowledge...",
    "character_knowledge": {"skill_level": "beginner"},
    "timeline_context": {"timestamp": 1100}
  },
  "consistency_score": 0.4,
  "issues_found": ["Power level inconsistency"],
  "suggestions": ["Consider reducing spell complexity"]
}
```

#### curl Example

```bash
curl -X POST http://localhost:8000/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Finn mastered advanced fire magic in his first lesson.",
    "character_id": "550e8400-e29b-41d4-a716-446655440000",
    "timeline_timestamp": 1000
  }'
```

### 3. Expand Shorthand Notation

**POST** `/llm/expand-shorthand`

Convert structured shorthand notation into full narrative prose and dialogue.

#### Request Body

```json
{
  "shorthand": "[Wizard enters] -> [Greets apprentice] -> [Begins lesson]",
  "style_guide": {
    "tone": "epic fantasy",
    "perspective": "third person",
    "focus": "character development"
  }
}
```

#### Response

```json
{
  "success": true,
  "expanded_content": {
    "full_content": "The ancient wizard stepped through the doorway..."
  },
  "shorthand_input": "[Wizard enters] -> [Greets apprentice] -> [Begins lesson]"
}
```

### 4. Generate Scene Content

**POST** `/llm/generate-scene`

Generate scene content based on story context and character states with timeline awareness.

#### Request Body

```json
{
  "scene_id": "123e4567-e89b-12d3-a456-426614174000",
  "character_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ],
  "goal_ids": ["789e0123-e89b-12d3-a456-426614174000"],
  "content_type": "mixed",  // "prose" | "dialogue" | "mixed"
  "timeline_timestamp": 1100,
  "additional_context": "Second magic lesson, focus on control"
}
```

#### Response

```json
{
  "success": true,
  "generated_content": "The second lesson began with Elara observing...",
  "content_type": "mixed",
  "scene_context": {
    "title": "The Second Lesson",
    "location_id": "456e7890-e89b-12d3-a456-426614174000"
  },
  "character_states": [
    {
      "entity_id": "550e8400-e29b-41d4-a716-446655440000",
      "knowledge": {"mood": "patient", "goal": "teach control"},
      "timestamp": 1000
    }
  ]
}
```

### 5. Suggest Narrative Continuations

**POST** `/llm/suggest-continuations`

Get AI-powered narrative continuation suggestions based on current story state.

#### Request Body

```json
{
  "current_timeline": 1100,
  "character_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ],
  "available_goal_ids": ["789e0123-e89b-12d3-a456-426614174000"],
  "suggestion_count": 3
}
```

#### Response

```json
{
  "success": true,
  "suggestions": [
    {
      "suggestion": "1. Focus on Finn's struggle with magical control...\n2. Explore the mentor-student relationship...\n3. Introduce a magical accident that teaches humility..."
    }
  ],
  "story_state": {
    "timeline": 1100,
    "active_characters": ["550e8400-e29b-41d4-a716-446655440000"],
    "recent_milestones": []
  }
}
```

---

## Semantic Search Endpoints

### 1. Entity Search

Search entities using semantic similarity with pgvector embeddings.

#### Direct Service Usage (Python)

```python
from app.services.search_service import search_service

results = await search_service.search_entities(
    query="wise magical mentor teacher",
    similarity_threshold=0.7,
    limit=10,
    entity_type="character"  # Optional filter
)
```

#### Expected Response Structure

```python
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Elara the Wise",
    "entity_type": "character",
    "description": "An ancient wizard with deep knowledge...",
    "metadata": {"age": 800, "specialization": "protective_magic"},
    "similarity": 0.85
  }
]
```

### 2. Scene Block Search

Search scene content using semantic similarity.

#### Direct Service Usage (Python)

```python
from app.services.search_service import search_service

results = await search_service.search_scene_blocks(
    query="magic lesson teaching apprentice",
    similarity_threshold=0.6,
    limit=5,
    scene_id="123e4567-e89b-12d3-a456-426614174000",  # Optional filter
    block_type="prose"  # Optional filter
)
```

#### Expected Response Structure

```python
[
  {
    "id": "789e0123-e89b-12d3-a456-426614174000",
    "scene_id": "123e4567-e89b-12d3-a456-426614174000",
    "block_type": "prose",
    "content": "Elara the Wise stood among the towering shelves...",
    "similarity": 0.78
  }
]
```

### 3. Knowledge Snapshot Search

Search character knowledge snapshots with timeline context.

#### Direct Service Usage (Python)

```python
from app.services.search_service import search_service

results = await search_service.search_knowledge_snapshots(
    query="magical energy control training",
    similarity_threshold=0.5,
    limit=10,
    character_id="550e8400-e29b-41d4-a716-446655440000",  # Optional filter
    timeline_start=1000,  # Optional filter
    timeline_end=2000     # Optional filter
)
```

#### Expected Response Structure

```python
[
  {
    "id": "abc12345-e89b-12d3-a456-426614174000",
    "entity_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": 1000,
    "knowledge": {
      "location": "Arcane Library",
      "emotional_state": "calm, focused",
      "current_goal": "teach Finn the fundamentals"
    },
    "similarity": 0.72
  }
]
```

### 4. Unified Search

Search across all content types simultaneously.

#### Direct Service Usage (Python)

```python
from app.services.search_service import search_service

results = await search_service.search_all(
    query="ancient magical knowledge wisdom",
    similarity_threshold=0.6,
    limit_per_type=5
)
```

#### Expected Response Structure

```python
{
  "scene_blocks": [
    {"id": "...", "content": "...", "similarity": 0.85}
  ],
  "entities": [
    {"id": "...", "name": "...", "similarity": 0.82}
  ],
  "knowledge_snapshots": [
    {"id": "...", "knowledge": {...}, "similarity": 0.78}
  ]
}
```

---

## Utility Endpoints

### 1. LLM Provider Status

**GET** `/llm/providers`

Get status and capabilities of all LLM providers.

#### Response

```json
{
  "success": true,
  "providers": {
    "openai": {
      "available": true,
      "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
      "capabilities": ["generation", "analysis", "embeddings"]
    },
    "groq": {
      "available": true,
      "models": ["llama-3.1-8b-instant", "mixtral-8x7b-32768"],
      "capabilities": ["generation", "fast_inference"]
    },
    "gemini": {
      "available": true,
      "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
      "capabilities": ["generation", "multimodal", "creative"]
    }
  },
  "available_providers": 3,
  "total_providers": 3
}
```

#### curl Example

```bash
curl http://localhost:8000/llm/providers
```

### 2. Test Content Generation

**POST** `/llm/test-generation`

Simple endpoint for testing LLM functionality.

#### Request Parameters

- `prompt` (query param): The prompt to test (default: "Write a brief story about a dragon.")
- `provider` (query param): Provider to use (default: "auto")

#### Response

```json
{
  "success": true,
  "prompt": "Write a brief story about a dragon.",
  "generated_content": "In the misty mountains far above the clouds...",
  "provider": "auto",
  "test_status": "passed"
}
```

#### curl Example

```bash
curl -X POST "http://localhost:8000/llm/test-generation?prompt=Write about a wizard&provider=groq"
```

### 3. LLM Health Check

**GET** `/llm/health`

Check health status of LLM service and providers.

#### Response

```json
{
  "success": true,
  "status": "healthy",
  "available_providers": ["openai", "groq", "gemini"],
  "provider_details": {
    "openai": {"available": true},
    "groq": {"available": true},
    "gemini": {"available": true}
  },
  "capabilities": [
    "content_generation",
    "narrative_analysis",
    "scene_generation",
    "shorthand_expansion",
    "narrative_suggestions"
  ]
}
```

---

## Database Schema Updates

Phase 4 adds embedding columns and search functions to the database schema:

### New Columns

```sql
-- Added to entities table
embedding VECTOR(1536)

-- Added to knowledge_snapshots table  
embedding VECTOR(1536)

-- Already exists in scene_blocks table
embedding VECTOR(1536)
```

### New Database Functions

```sql
-- Search entities by embedding similarity
CREATE OR REPLACE FUNCTION search_entities_by_embedding(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10
)

-- Search scene blocks by embedding similarity
CREATE OR REPLACE FUNCTION match_scene_blocks(
  query_embedding VECTOR(1536),
  match_threshold FLOAT,
  match_count INT
)

-- Search knowledge snapshots by embedding similarity
CREATE OR REPLACE FUNCTION search_knowledge_by_embedding(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10,
  filter_entity_id UUID DEFAULT NULL
)
```

---

## Testing

### Running Tests

```bash
# Run comprehensive backend tests
python tests/test_phase4_backend.py

# Run dedicated semantic search tests  
python tests/test_semantic_search.py

# Run end-to-end AI storytelling test
python tests/test_e2e_ai_storytelling.py

# Run all tests with pytest
pytest tests/ -v
```

### Test Coverage

- ✅ Embedding generation for all content types
- ✅ Multi-provider LLM integration with fallback
- ✅ Semantic search functions (entities, scene blocks, knowledge)
- ✅ Narrative analysis and consistency checking
- ✅ Scene generation with timeline awareness
- ✅ Shorthand expansion
- ✅ Provider status and health monitoring
- ✅ Integration between embedding and search systems

---

## Environment Variables

Required environment variables for Phase 4:

```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-proj-...
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIzaSy...

# Supabase Configuration
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJhbGc...
SUPABASE_SERVICE_KEY=eyJhbGc...
```

---

## Error Handling

All endpoints include comprehensive error handling:

### Common Error Response Format

```json
{
  "success": false,
  "error": "Content generation failed: API key not configured",
  "status_code": 500
}
```

### Fallback Behavior

- **LLM failures**: Automatic fallback to alternative providers
- **Semantic search failures**: Fallback to text-based search
- **Missing embeddings**: Generate embeddings on-demand
- **API rate limits**: Retry with different providers

---

## Performance Considerations

### Embedding Generation

- Embeddings are generated asynchronously
- Batch operations supported for multiple items
- Embeddings cached in database to avoid regeneration

### Semantic Search

- HNSW indices provide sub-linear search performance  
- Similarity thresholds help limit result sets
- Parallel search across content types

### LLM Operations

- Provider selection optimized by task type
- Automatic fallback prevents single points of failure
- Temperature and token controls for response quality

---

## Next Steps

1. **UI Integration**: Create frontend interfaces for Phase 4 features
2. **Advanced Search**: Add filters, sorting, and faceted search
3. **Caching**: Implement Redis caching for frequent queries
4. **Monitoring**: Add detailed metrics and performance monitoring
5. **Real-time**: WebSocket integration for live AI assistance

---

## Support

For issues with Phase 4 backend features:

1. Check environment variables are properly configured
2. Verify database schema is up to date with unified_schema.sql
3. Run test suites to identify specific component failures
4. Check provider status via `/llm/health` endpoint
5. Review logs for detailed error information

The Phase 4 backend provides a robust foundation for AI-powered storytelling with comprehensive testing and error handling.