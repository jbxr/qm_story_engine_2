# 🎯 Functional Spec: Story Goals & Planning

This specification defines how the system models high-level story goals — narrative outcomes we want to achieve — and how those goals inform scene planning, milestone generation, LLM assistance, and continuity enforcement.

---

## 🎯 Purpose

- Explicitly define desired character arcs, plot developments, and major events
- Use goals as planning scaffolding for future scenes
- Track which goals have been achieved
- Let LLMs propose scenes to reach goals not yet fulfilled

---

## 🧱 Core Concepts

### 1. **Story Goal**

A goal is a structured representation of a desired narrative outcome.

Each goal has:

- `goal_id` (UUID)
- `timestamp` (target or expected time)
- `subject_id` (character or entity)
- `verb` (e.g., gains, loses, reveals, confronts)
- `object_id` (another character or entity)
- `description` (optional natural language summary)
- `fulfilled_at` (timestamp when goal is achieved, or null)
- `linked_milestone_id` (optional link to the milestone that fulfills it)

Example:

```json
{
  "subject_id": "dash",
  "verb": "gains",
  "object_id": "vera_trust",
  "description": "Dash earns Vera's trust after betraying her."
}
```

### 2. **Goal Fulfillment**

A goal is fulfilled when:

- A `milestone_block` matches the goal structure (subject, verb, object)
- OR the author manually marks it as complete

### 3. **Goal Planning**

Unfulfilled goals act as prompts for LLM planning or human scene design.

- “What needs to happen between timestamp T0 and T1 to achieve this goal?”
- LLM may propose one or more intermediary milestones, scenes, or interactions

### 4. **Goal Types**

- **Character Arc Goals** (e.g., “Vera forgives Dash”)
- **Plot Point Goals** (e.g., “The Artifact is revealed to be sentient”)
- **World State Goals** (e.g., “Bridge is sealed off from all systems”)

---

## 📋 Functional Requirements

### ✅ Add Story Goal

- Author can define new goals with subject/verb/object
- May be linked to target timestamp or scene

### ✅ View Goal Timeline

- List of all goals, ordered by expected time
- Visual marker for fulfilled vs unfulfilled goals

### ✅ Link Goal to Milestone

- Milestones may fulfill one or more goals
- LLM or author can link a milestone directly to goal ID

### ✅ Generate Scenes to Fulfill Goals

- LLM or author may request suggestions to fulfill an unachieved goal
- Output includes:
  - Scene title
  - Candidate dialogue or prose
  - Suggested milestone(s)

### ✅ Track Goal Completion

- Automatically fulfilled when a matching milestone is added
- Optionally mark goals manually as complete or obsolete

---

## 🧠 Data Model Sketch

| Field                 | Type         | Description                         |
| --------------------- | ------------ | ----------------------------------- |
| `id`                  | UUID         | Goal ID                             |
| `subject_id`          | UUID         | Character or entity                 |
| `verb`                | TEXT         | Action (e.g., learns, loses, gains) |
| `object_id`           | UUID or TEXT | Target character or concept         |
| `timestamp`           | TIMESTAMP    | Expected fulfillment time           |
| `fulfilled_at`        | TIMESTAMP    | When actually achieved (nullable)   |
| `description`         | TEXT         | Optional goal summary               |
| `linked_milestone_id` | UUID         | Optional pointer to milestone       |

---

## 🧪 Testing and Validation

- Create sample goals with and without timestamps
- Add milestones and validate auto-fulfillment logic
- Confirm filtering and timeline display of achieved/unachieved goals
- Evaluate LLM-generated scene proposals

---

## 🔮 Future Extensions

- Nested or chained goals (e.g., “To do X, first Y and Z must happen”)
- Character-driven goal planning: allow each character to have internal goals
- Scene scoring based on progress toward narrative objectives

---

## ✅ Summary

Story goals act as the scaffolding for narrative planning. By modeling high-level intentions (character arcs, plot beats), we enable both humans and AI to build coherent, purposeful scenes that work toward clearly defined story outcomes.

They support continuity checking, character development, and goal-driven prose generation — all while preserving author control over final decisions.

