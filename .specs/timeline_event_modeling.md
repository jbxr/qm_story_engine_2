# ⏳ Functional Spec: Timeline & Event Modeling

This specification defines the foundational behavior and data structure for modeling **timelines**, **events**, and their associated **temporal metadata** in the QuantumMateria Story Engine.

This layer builds directly on the core spec and enables continuity validation, causal reasoning, and time-aware narrative tools.

---

## 🎯 Purpose

To provide authors (and automated agents) the ability to:

- Track *when* a scene or event takes place within the story
- Capture major plot milestones in structured form
- Align narrative content along a master timeline or multiple character timelines
- Support “snapshot” queries (e.g. what Dash knew at time X)
- Enable downstream LLM tasks like consistency checks, gap-filling, and foreshadowing analysis

---

## 🧱 Key Concepts

### 1. **Timestamps**
- All scenes and blocks can optionally have a `timestamp`
- Timestamps define ordering at story-level and enable temporal querying
- Format can be human-readable (`'Day 4 - Morning'`) or numeric (`ISO 8601`, `T+006:12`) depending on the project context

### 2. **Events**
- An event is a meaningful story moment that occurs at a specific timestamp
- Events can be standalone or linked to a scene block (esp. milestones)
- Each event should support:
  - `who`: subject(s)
  - `what`: verb/action
  - `to/with`: object(s)
  - `when`: timestamp
  - `where`: optional location or scene
  - `weight`: degree of narrative impact (optional)

### 3. **Milestone Integration**
- Milestone blocks create or reference events
- All milestones must have a timestamp (inherited from scene or explicitly set)
- Events created from milestones become part of the global event graph

### 4. **Scene-to-Timeline Mapping**
- Each scene is placed on the timeline
- If a scene contains multiple timestamps (e.g., flashbacks), each block may have its own timestamp
- The engine must maintain a canonical timeline from all timestamped items

---

## 📋 Core Functional Requirements

### ✅ Add Timestamps to Scenes or Blocks
- Author can assign a timestamp when creating or editing a scene or block
- Timestamps can be changed later and automatically reorder content if applicable

### ✅ Visualize Timeline (PoC Optional)
- Provide a linear list or visual view of events and scenes in timestamp order
- Allow filtering by character, location, or type

### ✅ Normalize Timeline Data
- Backend should resolve timestamp conflicts (e.g., multiple blocks with same time) using order metadata
- Ensure all milestones and events link to a valid timestamp

### ✅ Query by Time
- Allow LLM or developer queries like:
  - "What happened before/after this?"
  - "Where was character X at this moment?"
  - "Did any goals begin or resolve here?"

---

## 🧠 Assumptions & Constraints

| Constraint                  | Note |
|-----------------------------|------|
| Temporal granularity        | Flexible (e.g. hours, days, chapters)
| Timezones / relativity      | Out of scope for PoC
| Multiple timelines          | Possible via tags (e.g., character timeline)
| Retroactive event injection | Supported via backdated timestamps
| Branching timelines         | Out of scope for PoC, may be added later

---

## 🧪 Testing & Validation

- Ensure scenes sort properly by timestamp
- Ensure milestone and event views reflect accurate temporal placement
- Validate correct linking of events to blocks and characters
- Provide exportable timeline view for authors

---

## 🔮 Future Extensions

- Visual timeline editor (drag/drop blocks by time)
- Branching/alternate timelines
- Temporal anomaly detection (e.g. character in two places at once)
- Predictive timeline simulation (AI-generated futures)

---

## ✅ Summary

This layer introduces story-aware time modeling without requiring any specific frontend behavior. It enables downstream features like causality graphs, knowledge snapshots, and time-consistent storytelling without overloading the author with complexity.

This spec assumes we will continue using the current relational schema, extended with timestamp fields where needed.

