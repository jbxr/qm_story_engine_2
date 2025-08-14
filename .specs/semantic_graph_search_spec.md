# 🔗 Semantic Graph & Search Spec

This specification defines how semantic relationships — including vector search, knowledge graphs, and directed event chains — support narrative planning, AI assistance, and human author tooling.

It forms the backbone for querying past context, understanding character knowledge, and enabling AI-powered continuity.

---

## 🎯 Goals

- Enable natural language and concept-based search across all story elements
- Represent causal, temporal, and character knowledge via a directed graph
- Let both humans and LLMs traverse the story semantically — not just structurally

---

## 🧱 Core Features

### 1. Semantic Embeddings (Vector Search)

- Store vector embeddings for:
  - Prose blocks
  - Dialogue blocks
  - Milestones
  - Goals (and optionally characters / scenes)
- Embed text via OpenAI, HuggingFace, or custom model
- Store in `pgvector` column (`embedding VECTOR(1536)`) in Supabase

#### Example Use Cases:
- Find all blocks similar to: *"betrayal under pressure"*
- Suggest next scenes based on tone and theme
- Summarize character arc by clustering similar events

---

### 2. Event Graph (DAG Modeling)

Each scene or milestone becomes a **node**. Relationships are **edges**:

- Types of edges:
  - `causes`: Event A leads to Event B
  - `knows_about`: Character gains knowledge
  - `located_at`: Entity appears in location
  - `precedes`: Pure timeline order

Graph features:
- Store in adjacency list or edge table (`edges(source_id, target_id, type)`)
- Optional: weight edges by significance or certainty

#### Example Use Cases:
- "What does Vera know by Scene 12?"
- "Which events led to the bridge collapse?"
- "What’s the shortest path from Dash’s betrayal to Vera’s forgiveness?"

---

### 3. Knowledge Snapshots (Materialized Views)

Each character's perspective can be derived from the graph:

- Compute reachable `knows_about` or `witnessed` nodes at a given `scene_id`
- Cache or materialize as needed
- Can be used in:
  - LLM prompts: *"From Vera’s POV, she knows..."*
  - UI display: *"Knowledge delta" after a scene*

---

### 4. Natural Language Search (Hybrid)

- Combine full-text + vector search
- Query prose and milestone blocks with ranked relevance
- Let authors search with phrases like:
  - *"scenes where Dash manipulates someone"*
  - *"when the ship first shows signs of damage"*

---

## 🧪 Testing & Validation

- Embed and retrieve 10 sample blocks
- Run cosine similarity search and confirm relevance
- Traverse event DAG from known causes → outcomes
- Compute character knowledge at 3 scenes and verify correctness

---

## 🔮 Future Enhancements

- Visual graph UI for scene/milestone flow
- Fine-tune vector model on your own story corpus
- LLM-powered graph editor ("link these nodes")
- Semantic diffing between snapshots (e.g. character arcs)

---

## ✅ Summary

This spec empowers the system to reason about *why* things happen, *who knows what*, and *how we got here*.
It allows both humans and LLMs to interact with story data on a conceptual level — unlocking advanced search, goal tracing, continuity enforcement, and smarter AI planning.

