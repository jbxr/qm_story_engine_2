# 🧠 Functional Spec: Character Knowledge & Snapshots

This specification defines how the story engine will model **character knowledge**, memory, and awareness at different points in time. It enables queries about what each character knows, believes, or has experienced at any moment in the timeline — and how that knowledge evolves.

---

## 🎯 Purpose

- Track character knowledge and beliefs over time
- Allow inspection of what a character knows at a given timestamp
- Support AI-assisted continuity, motivation checking, and goal-driven narrative planning
- Lay groundwork for mystery, misinformation, and reveal-based storytelling

---

## 🧱 Core Concepts

### 1. **Knowledge Assertions**
- Each character can have a set of knowledge facts
- A knowledge fact links a **subject (the character)** to a **claim about the world**
- Example: `Dash knows Vera is alive` or `Harris believes the artifact is sentient`
- Knowledge is represented with:
  - `character_id`
  - `timestamp`
  - `predicate` (e.g. knows, believes, suspects, misunderstands)
  - `fact_subject` (e.g. Vera)
  - `fact_verb` (e.g. is alive)
  - `fact_object` (e.g. Artifact #1)

### 2. **Knowledge Snapshots**
- A snapshot is a computed view of what a character knows at a specific timestamp
- Can be used for consistency checks (e.g. “does Dash act on info he hasn’t learned yet?”)
- Snapshots are built from:
  - All prior `knowledge assertions`
  - All `milestones` where the character was involved
  - Events the character witnessed (via scene participation)

### 3. **Knowledge Flow**
- Facts can be added via:
  - Dialogue blocks (character is informed)
  - Milestones (character discovers something)
  - Explicit author input (manual assertions)
- Facts can be retracted or changed with newer assertions
- Beliefs and misunderstandings are tracked like knowledge

### 4. **Visualization**
- (Optional) Graph of what each character knows when
- Compare knowledge between characters or before/after events
- Flag conflicts, gaps, or narrative inconsistencies

---

## 📋 Functional Requirements

### ✅ Add Knowledge Assertion
- Author or system can add a new knowledge fact to a character
- UI may support natural language entry (e.g. “Dash learns the ship is failing”)

### ✅ Compute Knowledge Snapshot
- System can generate a list of all facts known by a character at time T
- Includes:
  - Direct assertions
  - Events witnessed
  - Scene participation

### ✅ Query Character Knowledge
- Support queries like:
  - “What does Vera know about Artifact 1 by Chapter 9?”
  - “Has Dash ever learned the truth about Luna?”
  - “Does Harris believe X is guilty before the trial?”

### ✅ Track Conflicting Knowledge
- Characters may hold incorrect, outdated, or conflicting facts
- Mark knowledge as `true`, `false`, or `uncertain`

---

## 🧠 Data Structure Considerations

| Field                | Type            | Description                           |
|----------------------|------------------|---------------------------------------|
| `character_id`       | UUID             | Who holds this knowledge              |
| `timestamp`          | TIMESTAMP        | When they acquired it                |
| `predicate`          | TEXT             | knows / believes / doubts / forgets   |
| `fact_subject`       | TEXT or UUID     | Entity the fact is about              |
| `fact_verb`          | TEXT             | The action or state (e.g. is dead)    |
| `fact_object`        | TEXT or UUID     | Optional additional target            |
| `certainty`          | ENUM             | true / false / uncertain              |
| `source_block_id`    | UUID (optional)  | Link to scene/dialogue that revealed it |

Snapshots would be materialized on request, not stored persistently (at least for PoC).

---

## 🧪 Testing and Validation

- Create test scenes with differing character exposures
- Assert expected knowledge snapshots at different timestamps
- Validate propagation or withholding of information

---

## 🔮 Future Extensions

- LLM-assisted suggestion of knowledge shifts (e.g., “should Dash have figured this out yet?”)
- Integration with story goal graphs (e.g., “character X needs to learn Y before Z”)
- Parallel knowledge timelines for reader and narrator
- Real-time contradiction detection

---

## ✅ Summary

Character knowledge is modeled as a time-evolving set of beliefs and truths. This structure supports fine-grained narrative reasoning, AI-driven continuity enforcement, and interactive features (e.g., mystery solving, reader omniscience). It works seamlessly with the existing schema and timeline model.

