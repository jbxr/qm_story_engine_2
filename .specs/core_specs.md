# 📘 Core Functional Specification: Story Engine (PoC)

This document defines the foundational, **tech-stack agnostic** functional specifications for the initial version of the QuantumMateria Story Engine. These core specs are intended to support all future extensions — including UI platforms, AI integrations, and authoring workflows — while remaining stable and portable.

---

## 🎯 Project Goals

- Enable structured, consistent storytelling with high continuity and semantic traceability
- Model scenes, characters, events, and knowledge as data-backed entities
- Allow authors to edit and review stories as modular blocks: prose, dialogue, and milestones
- Ensure all features work without relying on client-side state or complex frontend behavior
- Lay the foundation for future AI-assisted querying, editing, and generation

---

## 🧱 Core Feature Set

### 1. **Scene Viewing and Editing**
- Author can load a scene and view all associated content blocks
- Blocks are shown in narrative order
- Author can add new blocks (prose, dialogue, or milestone)
- Author can edit or delete existing blocks
- Author can reorder blocks within a scene

### 2. **Scene Block Types**
Each block in a scene has a `block_type`:
- `prose`: Narrative text (setting, action, etc.)
- `dialogue`: One or more lines spoken by characters
- `milestone`: Key story events that affect the narrative state

Each block is tied to a `scene_id` and has a persistent sort `order`.

### 3. **Reordering**
- Reordering blocks changes their `order` value in the database
- Authors move blocks using simple actions (e.g., move up/down)
- Drag and drop is out of scope for PoC

### 4. **Editing Workflow**
- Each block is displayed in read-only mode by default
- When editing, the block becomes a simple form appropriate to its type
- Saving a block replaces the old version with the updated content
- No client-side state required; each edit hits the backend directly

### 5. **Milestone Semantics**
- Milestones use structured format: `subject` → `verb` → `object`
- Milestones may represent causality, goals, or story progress
- Milestones may later be linked to long-term outcomes or character arcs

---

## 🎨 UX/UI Constraints (PoC)

| Constraint            | Value                      |
|-----------------------|----------------------------|
| Platform              | Desktop only               |
| Theming               | Dark mode only             |
| Responsiveness        | Not required               |
| Modal usage           | Out of scope               |
| Drag-and-drop         | Excluded                   |
| Form interactions     | Plain HTML forms or equivalents |
| State management      | Backend-only               |
| Preview/Live edit     | Not required for PoC       |

---

## 🧪 Testing and Feedback

The implementation should be testable via:
- Direct database inspection (for saved content and order)
- Visual confirmation of block creation, edit, and deletion
- Simple end-to-end tests verifying core flows (view → edit → save → reorder)

Manual testing is acceptable for the PoC.

---

## 📦 Extensibility (Not Required in PoC)

These features are **planned but not required** in the PoC:

- Timeline alignment and timestamping of events
- Per-character knowledge modeling
- Graph view of milestones and goals
- AI-assisted scene generation or milestone planning
- Scene variant comparisons or branching logic

These will build on the foundation laid by the current schema and core feature set.

---

## ✅ Summary

This spec defines the essential features and constraints for a minimal story editing system that balances structure and simplicity. It allows narrative content to be written, edited, and tracked with fidelity — without locking the implementation to any specific technology.

Future layers (AI, timeline, simulation, etc.) will extend from this core.

