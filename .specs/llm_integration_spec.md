# 🤖 Functional Spec: LLM Integration Layer

This specification defines how the system will integrate large language models (LLMs) to support creative authoring, continuity checking, goal fulfillment, and prose generation within the QuantumMateria story engine.

LLMs are not the source of truth — the structured data is. This integration enables intelligent use of LLMs *without compromising deterministic continuity*.

---

## 🎯 Purpose

- Provide AI assistance to authors without losing narrative control
- Support continuity-aware rewriting, planning, and dialog generation
- Leverage structured schema as the ground truth, using LLMs to:
  - Fill gaps in prose
  - Propose connective scenes
  - Identify inconsistencies
  - Expand shorthand into full language

---

## 🧱 Key Integration Modes

### 1. **Snapshot-Aware Analysis**
- LLM receives a scoped view of the story world at time T:
  - Timeline events up to that point
  - Character knowledge snapshots
  - Location and scene context
  - Goals and milestones (fulfilled or pending)

- Enables time-specific tasks:
  - “How would Vera react *at this moment*?”
  - “Does this line contradict what Harris knows?”

### 2. **Goal-Oriented Scene Generation**
- Input: Unfulfilled narrative milestone (e.g., “Dash gains Vera’s trust”)
- LLM is tasked with:
  - Proposing 1–3 scene ideas that lead to the milestone
  - Writing candidate prose or dialogue

- Can operate in 2 modes:
  - Outline-only (just propose events or beats)
  - Full prose (generate actual scene blocks)

### 3. **Shorthand Expansion**
- Input: Structured or shorthand text
  - E.g., `c:dash “You’re out of line.” emotion=angry`
- Output: Fully formatted dialogue block, optionally styled to match character voice or tone
- Supports keyboard macros or editor integrations

### 4. **Continuity Review Tasks**
- Author flags a block for review
- LLM checks for:
  - Character voice/tone mismatch
  - Timeline/knowledge inconsistencies
  - Unclear or weak scene transitions

### 5. **Rewrite Suggestions**
- Optional feature: LLM suggests alternate versions of a scene or block
- Input: Full scene block + optional prompt (e.g., “make more suspenseful”)
- Output: Rewritten prose, dialogue, or milestone phrasing

---

## 📋 Functional Requirements

### ✅ Scoped Query Generation
- System constructs clean input context for each LLM call
- Includes only necessary characters, events, goals, etc.

### ✅ Output Mapping
- LLM-generated results must be mappable back to valid schema objects
- E.g., A generated milestone becomes a valid `milestone_block` with subject, verb, object, timestamp

### ✅ LLM Assist Controls
- Authors can:
  - Flag blocks for rewrite
  - Request goal completions
  - Expand shorthand into full prose

### ✅ Safe Context Management
- Avoid hallucinated facts or assumptions
- Optionally verify output against known schema before commit

---

## 🧪 Testing and Validation

- Validate correct parsing and mapping of LLM outputs into block structures
- Test prompt quality and output accuracy for:
  - Gap-filling
  - Goal planning
  - Dialogue expansion
- Monitor LLM recall vs hallucination in known fact queries

---

## 🛠 Integration Points

| Feature Area        | LLM Use                     |
|---------------------|-----------------------------|
| Scene Authoring     | Goal completion, rewrites   |
| Dialogue Blocks     | Voice matching, expansion   |
| Milestones          | Suggest phrasing or chain   |
| Timelines           | Detect gaps, suggest links  |
| Character Knowledge | Predict evolution, test consistency |

---

## 🔮 Future Extensions

- Multi-agent character simulations
- Live prompt tuning per character or genre
- RAG (Retrieval-Augmented Generation) with custom embeddings from schema
- Automatic summary generation of timeline or arcs
- “Narrative health checks” using LLM + rule engine

---

## ✅ Summary

The LLM integration is an *assistive layer* built atop deterministic story state. It enables structured, continuity-aware authoring that blends human creativity with machine suggestion — without letting the AI become the sole storyteller.

