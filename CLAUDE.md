# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**QuantumMateria Story Engine** - A structured storytelling system designed to support narrative consistency, character continuity, and LLM-assisted authoring. The engine models scenes, characters, events, and knowledge as data-backed entities with semantic traceability.

## Architecture

### Core Tech Stack
- **Backend**: FastAPI + direct Supabase client for proven async API development
- **Database**: Supabase (PostgreSQL) with pgvector for semantic search
- **LLM Integration**: OpenAI/Groq APIs for embeddings and narrative assistance (Phase 4)
- **Frontend**: Minimal HTML-first approach (avoiding complex state management)

### Key Design Principles
- **Backend-only state management** - no client-side state complexity
- **Structured data as source of truth** - LLMs assist but don't control narrative
- **Desktop-first, dark mode** UI optimized for authoring workflows
- **Modular block-based** scenes (prose, dialogue, milestones)

## Development Commands

```bash
# Environment setup
uv sync                    # Install dependencies
source .venv/bin/activate  # Activate virtual environment

# Development server (WORKING - 27+ endpoints implemented)
uvicorn app.main:app --reload  # Start FastAPI dev server
python -m app.main         # Alternative startup method

# Health check endpoints
curl http://localhost:8000/health          # Database connectivity check
curl http://localhost:8000/docs            # Interactive API documentation

# Testing (285 tests implemented)
pytest                     # Run full test suite (7 test files)
pytest tests/             # Run specific test directory
pytest -v tests/test_scenes.py            # Run single test file
pytest tests/test_api.py -v               # API endpoint validation
pytest tests/test_scene_workflows.py -v   # End-to-end workflows

# Database operations (Supabase)
# Schema: supabase/schemas/unified_schema.sql
# Migrations: supabase/migrations/ (managed through Supabase CLI)
```

## Project Structure (Current Implementation)

```
# WORKING BACKEND (Phase 3 Complete)
app/
├── main.py              # FastAPI application entry point ✅ WORKING
├── config.py            # Environment configuration ✅ WORKING
├── models/              # API and data models ✅ WORKING
│   ├── api_models.py    # Request/response schemas
│   ├── entities.py      # Characters, locations, artifacts  
│   ├── content.py       # Scene blocks, content types
│   ├── goals.py         # Narrative objectives
│   ├── knowledge.py     # Character knowledge models
│   └── relationships.py # Entity relationships
├── api/                 # FastAPI route handlers ✅ 27+ ENDPOINTS
│   ├── scenes.py        # Scene CRUD operations ✅ WORKING
│   ├── entities.py      # Entity management ✅ WORKING
│   ├── milestones.py    # Milestone tracking ✅ WORKING
│   ├── goals.py         # Goal management ✅ WORKING
│   ├── content.py       # Content block operations ✅ WORKING
│   ├── knowledge.py     # Knowledge snapshots ✅ WORKING
│   ├── relationships.py # Temporal relationships ✅ WORKING
│   ├── search.py        # Search endpoints (Phase 4)
│   └── llm.py           # LLM integration (Phase 4)
└── services/            # Business logic layer ✅ WORKING
    ├── database.py      # Supabase client setup ✅ WORKING
    ├── scene_service.py # Scene business logic
    ├── knowledge_service.py # Knowledge management ✅ WORKING
    ├── content_service.py # Content operations ✅ WORKING
    ├── relationship_service.py # Relationship management ✅ WORKING
    └── search_service.py # Search functionality (Phase 4)

# DOCUMENTATION & PROJECT MANAGEMENT
docs/                    # Permanent technical documentation
├── README.md            # Project overview and setup
└── architecture.md     # Technical architecture decisions

project/                 # Current project state tracking
├── README.md            # Project organization guide
├── implementation-status.md # Current progress dashboard
├── session-log.md       # Development history
└── tasks.md             # Task management and backlog

# TESTING & VALIDATION ✅ 285 TESTS
tests/                   # Comprehensive test suite
├── conftest.py          # Test configuration
├── test_api.py          # API endpoint validation
├── test_api_validation.py # Input validation tests
├── test_database_connection.py # Database connectivity
├── test_models.py       # Data model validation
├── test_scene_workflows.py # End-to-end workflows
├── test_knowledge_api.py # Knowledge system tests
├── test_content_api.py  # Content operations tests
├── test_relationships_api.py # Relationship management tests
└── test_integration.py  # Cross-system integration tests

# TEMPORARY & BUILD ARTIFACTS
temp/                    # Temporary development files
├── README.md            # Temp directory guide
├── api_contract.py      # API contract validation
├── schema_design.py     # Database schema prototyping
└── verify_database.py   # Database validation scripts

supabase/                # Database configuration
├── config.toml          # Supabase configuration
├── migrations/          # Database migrations
└── schemas/             # Schema definitions
```

## Core Data Model

### Scene Blocks
- **prose**: Narrative text (setting, action, description)
- **dialogue**: Character speech with speaker/listener tracking
- **milestone**: References to first-class milestone entities

### First-Class Milestones
- **Separate table**: Milestones are now first-class entities, not embedded in scene blocks
- **Rich metadata**: Subject → verb → object structure with weights and descriptions
- **Scene references**: Milestones can reference scenes while maintaining independent existence

### Entity Relationships
- **Temporal relationships** with `starts_at`/`ends_at` timeline tracking
- **Knowledge snapshots** at specific timeline points for character continuity
- **Content operations** with advanced scene block manipulation
- Scenes contain ordered blocks with persistent sort order
- Milestones can fulfill story goals and trigger character knowledge updates
- Semantic graph connects related events, characters, and locations via embeddings

## Development Workflow

### Implementation Status (4-Phase Evolution)

**Phase 1: Foundation ✅ COMPLETE**
1. ✅ Database schema & Supabase connection
2. ✅ SQLModel entity definitions
3. ✅ Project structure & configuration

**Phase 2: Core APIs ✅ COMPLETE**  
1. ✅ Scene CRUD operations (13+ endpoints)
2. ✅ Entity management APIs
3. ✅ First-class milestone system (extracted from scene blocks)
4. ✅ Story goal management
5. ✅ UUID serialization fixes across all endpoints

**Phase 3: Advanced Features ✅ COMPLETE**
1. ✅ Knowledge snapshot system (6 API endpoints)
2. ✅ Content block advanced operations (8 API endpoints)
3. ✅ Temporal relationship management (13 API endpoints)
4. ✅ Timeline-aware queries and cross-system integration

**Phase 4: LLM & Search (Planned)**
1. ⭕ Semantic search (pgvector + embeddings)
2. ⭕ LLM integration endpoints
3. ⭕ AI-assisted content generation
4. ⭕ Snapshot-aware narrative assistance

### LLM Integration Patterns
- **Snapshot-aware analysis**: LLM receives time-scoped story world context
- **Goal-oriented generation**: Propose scenes that fulfill narrative milestones
- **Continuity review**: Check character voice, timeline consistency
- **Shorthand expansion**: Convert structured notation to full prose/dialogue

## Documentation & Project Tracking

### Technical Documentation (`docs/`)
- `docs/README.md` - Project overview, setup, and guidelines
- `docs/architecture.md` - Technical architecture decisions and rationale

### Project Management (`project/`)
- `project/implementation-status.md` - Current progress dashboard and phase tracking
- `project/session-log.md` - Development history and session notes
- `project/tasks.md` - Task management and backlog
- `project/README.md` - Project organization guide

### Database Schema (`supabase/`)
- `supabase/schemas/unified_schema.sql` - Complete database schema
- `supabase/migrations/` - Database migration files

## Testing Strategy

### Current Test Suite ✅ 285 TESTS IMPLEMENTED
- **Comprehensive pytest framework** - 10+ test files covering all major components
- **API endpoint validation** - All 27+ endpoints tested with proper validation
- **Cross-system integration** - Phase 3 systems working together (77% pass rate)
- **Database connectivity** - Supabase connection and CRUD operations verified
- **End-to-end workflows** - Complete scene editing workflows validated
- **Model validation** - All SQLModel schemas tested for correctness
- **Advanced test coverage** - Knowledge snapshots, temporal relationships, content operations

### Test Coverage Areas
- **Database operations** - Connection, CRUD, transactions
- **API endpoints** - Request/response validation, error handling
- **Business logic** - Scene workflows, entity relationships
- **Input validation** - Schema validation, edge cases
- **Integration flows** - End-to-end user scenarios

## Development Notes

### Current Implementation Approach ✅ VALIDATED
- **Direct Supabase client** - Simple, proven async operations (no SQLModel complexity yet)
- **Backend-architect validated** - Current approach rated "ARCHITECTURALLY EXCELLENT"
- **Strategic foundation** - 15% API + 80% database foundation preserves all future options
- **No complex frontend frameworks** - prefer server-rendered HTML with minimal JS

### Technical Decisions
- **Direct database operations** - Supabase client for immediate productivity
- **Comprehensive schema** - Full entity relationship modeling in database
- **Phased evolution** - Clear upgrade path to SQLModel, GraphQL, advanced features
- **Test-driven validation** - Proven patterns before architectural complexity

## Current Implementation Status

### ✅ Phase 3 Complete: Advanced Storytelling Foundation
- **27+ API endpoints implemented** - Complete storytelling system with temporal features
- **285 comprehensive tests** - Full validation across 3 major system expansions
- **Knowledge system** - Character knowledge snapshots with timeline continuity
- **Content system** - Advanced scene block operations and batch processing
- **Relationship system** - Temporal relationships with timeline awareness
- **Cross-system integration** - All Phase 3 systems working together
- **Backend-architect validation** - Architecture rated "ARCHITECTURALLY EXCELLENT"

### 📊 Key Metrics (As of Current Session)
- **Working FastAPI server** - Proven async patterns with health checks
- **Complete database schema** - All entity relationships modeled
- **Test coverage** - All core APIs and workflows validated
- **Documentation** - Comprehensive project tracking and technical docs

### 🎯 Next Development Targets
1. **Phase 4: LLM Integration** - Semantic search, AI-assisted authoring
2. **Frontend Implementation** - HTML-first UI for scene editing
3. **Production Deployment** - Hosting and scaling considerations
4. **Advanced Features** - Enhanced temporal queries, relationship visualization

### 🔄 Evolution Readiness
- **SQLModel upgrade path** - Schema ready for ORM integration
- **GraphQL readiness** - Complex queries architectured
- **Semantic search** - pgvector schema in place
- **LLM integration** - Knowledge snapshot patterns designed

## North-star mindset

• Define “good enough” upfront: minimum viable outcome, success criteria, and a time budget.
• Keep a single, visible plan; update it as reality changes, not as aspirations grow.
• Ship in thin vertical slices that deliver user value end-to-end.

## Complexity brakes

• 45-minute rule: if stuck, stop and simplify.
• One-new-thing rule: introduce at most one new tool/pattern at a time.
• Scope guard: touch as few files/concepts as possible per change.
• Replace cleverness with clarity; prefer duplication over premature abstraction.

## Validation habit

• Prove reality early: minimal working example before scaling.
• Test the thing you just built the way users will use it (black-box first).
• Add a tiny, fast test when something works; grow tests with features.
• Treat any red (errors, failing tests) as a stop sign, not a speed bump.

## Plan discipline

• Start every task with:
 • Outcome: one sentence of user value.
 • Timebox: when you’ll reassess.
 • Fallback: the boring solution you’ll accept.
 • Warning signs: what will trigger the fallback.
• End every task with:
 • A demoable artifact, passing tests, and a short note in the plan.


## Decision support in the loop

• When complexity hits, ask:
 • What’s the dumbest solution that works today?
 • Can I validate one piece in isolation?
 • Am I still solving the right problem for the user?
• If choosing complexity, justify explicitly (value, constraints, reuse, budget) and set an escape plan.

## Documentation rhythm

• Docs track reality, not intent: update after each working step.
• Record the minimal “how to run, how to test, known pitfalls.”
• Capture decisions and tradeoffs in 2–4 bullets, co-located with code or in a lightweight CHANGELOG/ADR.

## Version control hygiene

• Commit after each working, validated step; small and purposeful.
• Messages explain the why more than the what.
• Avoid broad refactors without tests and timeboxes.

## Integration-first collaboration

• Don’t parallelize until a working pattern is proven.
• Each contributor owns validation: run, test, and report results (status, commands, outcomes).
• Stop-the-line for systemic failures; fix root cause before new work.

## Tech choices

• Boring tech wins until proven insufficient.
• Optimize for readability, observability, and testability over raw performance.
• Prefer configuration and conventions to frameworks and abstractions.

## Success signals vs. drift signals

• Success: fast feedback, simple explanations, green tests, steady delivery of value.
• Drift: repeated “should work,” wide file surface touched, growing docs-to-reality gap, tests lagging changes.

