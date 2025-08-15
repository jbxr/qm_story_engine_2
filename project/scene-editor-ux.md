# Scene Editor UX / Architecture Plan

Last updated: 2025-08-14
Status: IN PROGRESS (T1, T2, T3, T4, T5, T6 complete: Full CRUD operations + robust handling + undo + status UI working)

## 1. Goals
Provide a structured, low-latency writing environment for scenes supporting:
- Mixed content blocks (prose, dialogue, milestone)
- Fast incremental editing & autosave
- Metadata + continuity + world knowledge assistive panels
- Progressive enhancement (no heavy framework yet)
- Future migration path to a component framework if complexity grows

## 2. Current Architecture (Vanilla JS Modular)
Component Layers:
1. Data Access: api.js (REST → FastAPI) + direct Supabase (scenes/entities preload) in app.js
2. Core App Class: StoryEngine (lifecycle, global datasets, navigation integration)
3. Scene Editor Extension: scene-editor.js (prototype augmentation – isolates complex editor logic)
4. State Store: sceneState (current, blocks, entities, dirty flags) – single source for editor
5. Event Bus: sceneBus (lightweight pub/sub for decoupled reactions)
6. Rendering Strategy:
   - Core scene rendering replaced by DOM node construction (renderBlockElement) – no full string reparse
   - Incremental block append (targeted updates) instead of full list re-render (in progress – partial)
7. Autosave:
   - Debounced scene meta (title/location)
   - Per-block debounced content save with preview update
8. Layout:
   - Two-column: main writing area + right sidebar (navigation, metadata, block creation, analysis, world query, save status)
   - Removed breadcrumb → inline prev/list/next links in sidebar
9. Separation of Concerns:
   - app.js retains generic logic (loading scenes, global init)
   - scene-editor.js owns editor state, DOM rendering, event handling, autosave

## 3. Implemented Features
Category | Feature | Notes
---|---|---
Navigation | Inline Prev / List / Next | Index-based over preloaded scenes array
Metadata | Location select + prev/next scene selectors | Populated from existing scenes (no dedicated location entities yet)
Blocks | Create prose/dialogue/milestone | Sends scene_id, order; returns block
Blocks | Autosave (debounced) | 1s per block after input; updates preview only
Blocks | Preview update w/out full rerender | Inline patch (post-save)
Scene | Title inline edit (contenteditable) | Debounced 1.2s save
Scene | Location change auto-save | Immediate save
State | Central sceneState object | Single source of truth
Events | Pub/Sub bus (scene:loaded, block:saved, block:added, block:deleted) | Extensible
UI | Sidebar reorganization | Creation + analysis + world query consolidated
Persistence | Supabase + FastAPI mix | Blocks via API; scenes direct + API updates
Scaffolding | Continuity & World Query stubs | Async placeholders with future integration points
Refactor | Block DOM rendering | renderBlockElement instead of concatenated HTML
Safety | Basic error logging | Console (needs user-facing status channel)

## 4. Rationale / Design Decisions
Decision | Reason | Future Flex Path
---|---|---
Vanilla JS vs Framework | Delay framework lock-in; maintain low bundle & cognitive load | Gradual Svelte “island” if reactivity pressure grows
Prototype Augmentation (scene-editor.js) | Avoid bloating core StoryEngine; maintain discoverable API surface | Later: convert to ES Modules / class composition
Event Bus | Decouple autosave, UI badges, future real-time updates | Replace with state management lib if complexity spikes
DOM Block Rendering | Fine-grained updates; avoid full innerHTML reflows | Compatible with future virtual DOM or morphing libs
Central Sidebar | Reduces primary area cognitive clutter; focuses typing | Could become collapsible / dockable panel
Inline Navigation (Prev/Next) | Faster scene traversal for linear drafting | Replace with timeline/graph navigation later
Milestone inside Blocks | Unified block pipeline; no separate milestone pane | Later: structured milestone editor panel if semantics expand
Autosave Debounce | Balance latency + API load | Tune per block type; introduce batching

## 5. Identified Gaps / Remaining Tasks
Priority Legend: P0 critical, P1 important, P2 enhancement, P3 future.

ID | Priority | Task | Acceptance Criteria
---|---|---|---
T1 | P0 | Fix addBlock incremental path fully (remove any legacy reload assumptions) | ✅ **COMPLETE**: New block appended, state updated, no full reload
T2 | P0 | Reorder (Up/Down) implementation | ✅ **COMPLETE**: Buttons swap DOM + update sceneState + call reorder endpoint; order persists on reload
T3 | P0 | Robust ID/source for new blocks | ✅ **COMPLETE**: Enhanced normalization with validation, robust API response extraction, and comprehensive error handling
T4 | P1 | Block delete (server) | ✅ **COMPLETE**: DELETE endpoint call + optimistic removal + error rollback
T5 | P1 | Undo stack (basic) | ✅ **COMPLETE**: Comprehensive undo for all operations (create, delete, reorder, content) with 10-action history
T6 | P1 | Central status UI | ✅ **COMPLETE**: Unified status component with color-coded states, icons, and loading animations
T7 | P1 | Dirty navigation guard | ✅ **COMPLETE**: Browser-level protection prevents data loss; dirty state detection for scene and blocks working; internal navigation guard architecture implemented
T8 | P1 | Milestone structured persistence | ✅ **COMPLETE**: Structured milestone interface with entity dropdowns, subject_id/verb/object_id persistence, backward compatibility, integrated with T3/T5
T9 | P1 | Dialogue structure | ✅ **COMPLETE**: Structured dialogue with speaker dropdowns, dynamic line management, lines array persistence, preview integration with T3/T5
T10 | P2 | Performance profiling | ✅ **COMPLETE**: Comprehensive performance monitoring system with scene load tracking, block operation timing, memory usage monitoring, global performance reporting functions, and automated stress testing capabilities
T11 | P2 | Batch reorder optimization | Apply multiple moves then send minimal update sequence
T12 | P2 | Accessibility pass | Keyboard navigation for blocks; ARIA roles; focus management on add/delete
T13 | P2 | Status toasts / ephemeral messages | Non-blocking confirmations for saves/errors
T14 | P2 | Command palette (future) | Quick actions: add block, jump to block, analyze continuity
T15 | P3 | Real-time collaboration hooks | Abstract mutation pipeline to support multi-user merges
T16 | P3 | Offline queue | Local queue + retry for saves
T17 | P3 | Plugin hooks | Emission points for AI suggestions / transformations

## 6. Technical Debt / Risks
Area | Risk | Mitigation
---|---|---
Prototype Augmentation | Harder static analysis | Migrate to ES module imports once stable
Mixed API Layers | Divergent error handling (direct vs API) | Unify via adapter wrapper (normalize responses)
Scene Ordering Logic | Depends on array index (timestamp drift) | Introduce explicit ordering & recalc utilities
Milestone Data Model | Using generic block fields only | Map to dedicated fields early (T8) to prevent migration complexity
Undo Strategy | Not yet instrumented | Introduce action log before complex transforms (reorder, delete) ship

## 7. Near-Term Implementation Sequence (Suggested)
Sprint A (Stability): ✅ T1, T2, T4, T6, T5 **COMPLETE** (Full CRUD + robust handling + status + undo)
Sprint B (Semantics): T7, T8, T9 (dirty guard, milestone structure, dialogue structure)
Sprint C (UX Polish): T10, T12, T13, minor perf fixes
Sprint D (Advanced): T11, T14, exploratory for T15–T17

## 8. API & Data Model Considerations
Aspect | Current | Planned
---|---|---
Reorder Endpoint | Single-block new_order PUT | Bulk reorder (list) for batch moves (T11)
Milestone Fields | block.subject_id/verb/object_id unused in UI | Surface selectors + structured save
Dialogue | Stored as content | Transition to JSON lines for multiple speakers (lines field)
Metadata | location_id only | Extend with tags / pacing / viewpoint later

## 9. Migration Path to Framework (If Needed)
Trigger Conditions: Complex derived state (filters, search, AI suggestions), multi-user, heavy conditional UI.
Steps: (1) Wrap current renderBlockElement in adapter → (2) Introduce Svelte component for block → (3) Gradually replace sidebar modules → (4) Remove prototype augmentation.

## 10. Definition of “Complete” (Phase 1)
Must have:
- Create / edit / reorder / delete blocks (prose, dialogue, milestone)
- Structured milestone + dialogue support
- Reliable incremental saves with status feedback
- Undo (single-level at minimum) for block content/delete
- Dirty-state navigation guard
- Basic accessibility (keyboard traversal + ARIA labels)

Stretch (Optional for Phase 1 sign-off):
- Batch reorder operations
- Improved analysis (continuity actual logic integration)
- Dialogue speaker/entity linking

## 11. Open Questions
Topic | Question
---|---
Dialogue Model | Use entity IDs for speakers? Need entity selection UI.
Continuity Scope | Per scene only or cross-scene narrative coherence?
Milestone Weight | Editable now or deferred?
Location Handling | Promote locations to managed entity type UI?

## 12. Immediate Action Items (Next Commit)
- ✅ **COMPLETE**: Implement T1 & T2 concurrently (ensure addBlock no reload, enable up/down reorders)
- ✅ **COMPLETE**: Add global status emitter (hook block:saved & scene:loaded → update #scene-global-status)
- ✅ **COMPLETE**: Prepare data normalization util for block responses (id, block_type, order, content, subject, verb, object)
- ✅ **COMPLETE**: Implement T5 (Undo stack basic) - Last N block content/order operations reversible
- ✅ **COMPLETE**: Implement T3 (Robust ID/source) - Robust block normalization and API response extraction
- ✅ **COMPLETE**: Implement T4 (Block delete server sync) - Optimistic deletion with server sync and error rollback
- ✅ **COMPLETE**: Implement T6 (Central status UI) - Enhanced status component with color-coded states and animations
- ✅ **COMPLETE**: Implement T7 (Dirty navigation guard) - Browser-level protection preventing data loss, internal navigation guard architecture complete
- ✅ **COMPLETE**: Implement T8 (Milestone structured persistence) - Structured milestone interface with entity dropdowns, backend persistence integration
- ✅ **COMPLETE**: Implement T9 (Dialogue structure) - Structured dialogue editor with speaker selection, dynamic line management, and structured data persistence
- **NEXT**: Implement T10 (Performance profiling) or T11 (Batch reorder optimization) - Next priority scene editor features

---
Document Owner: Dev Toolkit (auto-generated assistance)
Update Procedure: Amend sections 5–7 as tasks complete; keep timestamp current.

