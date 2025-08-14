# 🧱 Architecture Decisions and Rationale

This document outlines the key architectural choices for the story engine project prototype, including our reasoning and future considerations.

---

## 1. 🗃️ Database Layer: Supabase

### ✅ Decision
Use **Supabase** for the backend PostgreSQL database.

### 🔎 Rationale
- Hosted PostgreSQL with generous free tier
- Built-in API access (REST + GraphQL)
- Native support for **pgvector** (essential for LLM embeddings)
- Web UI makes schema exploration and iteration fast

### 🚫 What We’re Avoiding
- **Row-level security (RLS)** — not needed for solo prototyping
- **Manual database migrations** — unless necessary, we’ll iterate declaratively

### 🔮 Future Considerations
- Re-enable RLS and formalize auth for multi-user scenarios
- Integrate schema migrations via `dbml`, Alembic, or Supabase CLI workflows

---

## 2. 🐍 Backend Logic: FastAPI + SQLModel

### ✅ Decision
Use **FastAPI** with **SQLModel** to implement all core logic and authoring tools.

### 🔎 Rationale
- Familiar stack with great developer experience
- Async-native, fast, typed
- Easy to write LLM-facing endpoints (e.g., rewriting, analysis, planning)
- SQLModel allows defining schema objects declaratively, and works well with Pydantic

### 🚫 What We’re Avoiding
- Full SQLAlchemy complexity
- Alembic migrations (for now — only if required)

### 🔮 Future Considerations
- Validate Supabase schema ↔ SQLModel parity
- Possibly auto-generate SQLModel classes from Supabase schema
- Improve seeding, snapshotting, and test data generation

---

## 3. 🔍 Frontend Queries: Supabase GraphQL

### ✅ Decision
Use **Supabase GraphQL** for querying complex nested data from the frontend.

### 🔎 Rationale
- Great for deeply nested scene → block → milestone → character chains
- Reduces need to write view logic in Python
- Pairs well with static-first frontend model

### 🚫 What We’re Avoiding
- Supabase REST API (too verbose for nested DAGs)
- Client-side GraphQL cache layers (Apollo, urql, etc.)

### 🔮 Future Considerations
- Migrate to richer GraphQL client as needs evolve
- Consider GraphQL for internal tooling if schema remains stable

---

## 4. 🎨 Frontend/UI: Minimal HTML-first

### ✅ Decision
Use **minimal static-first UI**, initially with Jinja templates or basic server-rendered HTML.

### 🔎 Rationale
- Avoid frontend state management
- Avoid React/SPA complexity
- Easy to prototype and test with plain HTML

### 🚫 What We’re Avoiding
- HTMX/Alpine/Hyperscript combos (too brittle in practice)
- Complex frontend build tools (Vite, Tailwind JIT, etc.)

### 🔮 Future Considerations
- Migrate to SvelteKit, Tauri, or native desktop app if needed
- Adopt HTMX *only* for known patterns (e.g., block editing)

---

## 5. 🧠 LLM Integration Strategy

### ✅ Decision
Expose clean, typed FastAPI endpoints for:
- Snapshot retrieval
- Scene rewriting
- Dialogue planning
- Goal fulfillment planning

### 🔎 Rationale
- LLM agents work best with deterministic, strongly-typed endpoints
- SQLModel is perfect for schema clarity

### 🔮 Future Considerations
- Add OpenAPI metadata for auto-discovery of agent tools
- Integrate agent planning loop directly into FastAPI app
- Support embedded model execution (e.g., local llama.cpp or LM Studio)

---

## Summary
We’re optimizing for:
- Low cognitive load
- Minimal moving parts
- Maximal clarity for LLM integration

These decisions form a flexible, incrementally extensible architecture. As complexity grows, we can selectively introduce client-side logic, migrations, auth, or advanced caching — but not until they’re needed.

