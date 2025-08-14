# 🧭 Feature Dependency Map

This document outlines the directional dependencies between core features of the story engine project. It guides implementation order, parallelization, and identifies architectural bottlenecks.

---

## 🧱 Core Dependency Graph

```text
[Entity & Relationship Layer]       [UI Scaffolding & Layouts]
            ↓                               ↓
       [Scene Blocks UI] ←──────────────→ [Scene Blocks]
            ↓
        [Milestones]
            ↓
       [Story Goals]
            ↓         ↘
[Semantic Graph & Search] ← [Dialogue Modeling]
       ↓             ↓
[Knowledge Snapshots]   [LLM Integration]
```

---

## 🔹 Explanations

### 0. **Entity & Relationship Layer**

Defines characters, locations, artifacts, timelines, and the core relational schema that powers everything.

- Must exist before: `Scene Blocks`, `Milestones`, `Dialogue`
- Supports: search, validation, references, continuity

---

### 0. **UI Scaffolding & Layouts**

Base authoring UX: static layout, minimal state, dark mode, desktop-first.

- Enables all frontend interaction with the system
- Keeps UX complexity low for POC

---

### 1. **Scene Blocks**

Foundation for all narrative structure. Prose, dialogue, and milestone events are all structured as scene blocks.

- Depends on: `Entity Layer`, `UI Scaffolding`
- Must exist before any higher-order modeling

---

### 2. **Milestones**

Structured events (who did what to whom, when) extracted or entered into scenes.

- Depends on: `Scene Blocks`
- Required for: `Story Goals`, `Semantic Graph`, `Snapshots`

---

### 3. **Story Goals**

Desired narrative outcomes, fulfilled by Milestones.

- Depends on: `Milestones`
- Used by: `Semantic Graph`, `LLM Planning`

---

### 4. **Dialogue Modeling**

Structured line-by-line character dialogue (speaker, listeners, emotion, etc.)

- Depends on: `Scene Blocks`
- Optionally linked to `Milestones`
- Supports: `LLM`, `Semantic Search`

---

### 5. **Semantic Graph & Search**

Embeds story elements, links them causally/semantically, and enables DAG traversal.

- Depends on: `Milestones`, `Story Goals`, `Dialogue`
- Supports: `LLM`, `Knowledge Snapshots`, `Search`

---

### 6. **Knowledge Snapshots**

Materialized views of what characters/entities know at a point in time.

- Depends on: `Semantic Graph`, `Milestones`
- Used by: `LLM`, `Continuity Checks`

---

### 7. **LLM Integration**

Enables natural language planning, prose rewriting, goal fulfillment, scene suggestions.

- Depends on: `Semantic Graph`, `Snapshots`, `Dialogue`, `Goals`

---

## ✅ MVP Build Order (Recommended)

1. Entity & Relationship schema
2. UI scaffolding and static layout
3. Scene Blocks CRUD
4. Milestone modeling
5. Story Goal scaffolding
6. Dialogue system
7. Semantic Graph engine (pgvector + DAG)
8. LLM integration basics
9. Knowledge Snapshots / timelines

---

## 🏗 Future Extensions

- Visual graph of event flow
- Agent-driven scene generation based on goals
- Editable timelines with what-if branching
- Real-time feedback on continuity gaps

---

## Summary

This map helps ensure we implement foundational pieces before relying on them downstream — enabling robust test coverage, clean spec-driven development, and flexibility in backend/frontend integration.

