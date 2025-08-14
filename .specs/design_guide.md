# **QuantumMateria Story Engine – Design Guide**

## 1. **Design Philosophy**

Our approach to UI/UX for the Story Engine balances **narrative immersion** with **editorial efficiency**. The system should feel like a creative workspace built for storytellers who think in **scenes, characters, and world logic**—not just words.

### Core Principles

1. **Clarity over clutter** – Every panel, button, and label must have a clear purpose and minimal cognitive load.
2. **Compact density** – Information should be visible without excessive scrolling. Use collapsible blocks, smaller font sizes, and tighter spacing to fit more in view without feeling cramped.
3. **Seamless flow** – Editing prose, dialogue, and metadata should feel like a single continuous action, not separate workflows.
4. **Progressive disclosure** – Show the essentials up front; advanced tools and rare options should be a click/tap away.
5. **Tactile feedback** – Hover, focus, and active states must feel responsive and “alive” to give confidence during rapid editing.
6. **World-aware context** – UI should surface related world facts, continuity notes, and linked content where it’s relevant—avoiding modal interruptions.
7. **Low-friction iteration** – Story beats, scenes, and elements must be quickly rearranged, duplicated, or deleted without page reloads.
8. **Portable performance** – The interface should run smoothly even with large worlds, long scenes, and many UI components.

---

## 2. **UI Structure**

Our layout is a **three-column workspace**:

| Column                       | Purpose                           | Examples                                                          |
| ---------------------------- | --------------------------------- | ----------------------------------------------------------------- |
| **Left (Navigation)**        | Persistent world structure        | Story goals, scenes list, characters, world entities              |
| **Center (Editor)**          | Primary editing canvas            | Metadata fields, collapsible blocks for prose/dialogue/milestones |
| **Right (Contextual Tools)** | Scene-specific AI tools & queries | Continuity analysis, world query                                  |

### Component Guidelines

* **Collapsible Blocks** (`<details>/<summary>`) for Prose, Dialogue, Milestones
  → Reduces vertical sprawl and keeps related content together.
* **Inline Controls** for block reordering, editing, and deletion
  → Avoids moving hands to a global toolbar.
* **Sticky CTA Bar** at bottom for primary scene actions (e.g., “Check Continuity”)
* **Small, consistent paddings** (\~0.4–0.8rem) for denser data display.

---

## 3. **Color & Typography Tokens**

We’ll maintain a **dark, high-contrast theme** optimized for long writing sessions.

| Token         | Value     | Purpose                           |
| ------------- | --------- | --------------------------------- |
| `--bg-0`      | `#0d0f12` | Main app background               |
| `--bg-1`      | `#121419` | Secondary background (nav, aside) |
| `--bg-2`      | `#171a21` | Panel background                  |
| `--bg-3`      | `#1d2129` | Header & block title background   |
| `--ink-1`     | `#e9eaf0` | Primary text                      |
| `--ink-2`     | `#b6bcc8` | Secondary text                    |
| `--ink-3`     | `#7e8592` | Muted labels                      |
| `--border-1`  | `#272d38` | Neutral border                    |
| `--brand`     | `#6f6af8` | Primary accent                    |
| Font size     | `14px`    | Compact readability               |
| Line height   | `1.42`    | Balanced density                  |
| Border radius | `10px`    | Soft, modern edges                |

---

## 4. **Tooling & Library Decisions**

### **Core Stack**

* **HTML + CSS (PicoCSS)**
  → PicoCSS provides a minimal, semantic-first foundation with almost no runtime cost.
  → Allows progressive enhancement without being tied to a JS framework.
* **Native Web Components (optional)**
  → For encapsulated UI like `<qm-scene-block>`, improving reusability and state handling.
* **No heavy UI frameworks** for the prototype
  → Keeps performance snappy, reduces build complexity, and avoids long dependency chains.
* **Grid & Flexbox** for responsive layout
  → Eliminates the need for a CSS framework’s grid system.

### **Enhancements / Utilities**

* **Custom CSS variables** for all theme tokens → instant theming without rewriting components.
* **SVG icons** (inline or sprite sheet) → crisp on all screen sizes, styleable via `fill`/`stroke`.
* **Native `<details>`** for collapsibles → no JS overhead for expand/collapse.
* **Lightweight drag-and-drop** (if needed later) via a 3–5KB helper like `sortablejs` instead of large frameworks.

---

## 5. **Interaction Patterns**

1. **Inline edits**: Text fields and textareas should be editable in place without switching modes.
2. **One-click add**: Adding prose, dialogue, or milestones never takes you away from the current context.
3. **Keyboard friendly**:

  * `Tab` / `Shift+Tab` to move between editable fields
  * `Cmd/Ctrl+Enter` to commit an edit
4. **Instant feedback**: Changes should persist in the UI immediately, with server sync happening silently in the background.
5. **Context-aware AI**: AI-generated text is injected into the current block, not in a separate modal.

---

## 6. **Future-Proofing**

* **Component extraction**: Once the prototype is validated, migrate repeating structures into reusable components.
* **Framework migration**: If we later integrate with React, Vue, or Svelte, our semantic markup + scoped styles will port easily.
* **Offline-friendly**: Store changes locally (IndexedDB) in case of network drops, sync when online.

---

## 7. **Why This Works for Us**

* **Fast prototyping** without the weight of a framework.
* **Easily themed** with our token system.
* **Performance-friendly** for large stories.
* **Minimal cognitive friction**—writers focus on story, not tool mechanics.

---

## 8. **Design Critique (PoC) and Implemented Improvements**

Strengths observed in the current PoC UI (index.html):
- Clear 3-column layout aligned with the guide (nav / editor / contextual tools).
- Use of native <details>/<summary> for collapsible blocks keeps interactions snappy and accessible.
- Compact, consistent tokens and paddings match the density goals.

Gaps and risks identified:
- Action buttons (move/edit/delete) were purely visual; no low-friction iteration without basic DOM actions.
- No keyboard shortcut for commit; tactile feedback for edits was minimal.
- Expand/Collapse was not global; progressive disclosure could be improved at the scene level.
- Accessibility was missing stronger focus states and ARIA labels for icon buttons.

Changes implemented in this PoC iteration:
- Added data-action wiring and lightweight JS (js/app.js) to support:
  - Up/Down reordering within a scene (no drag-and-drop, per spec).
  - Adding new blocks via + Prose / + Dialogue / + Milestone.
  - Edit button now focuses first editable field; Delete confirms removal.
  - Global Expand/Collapse All toggle.
  - Cmd/Ctrl+Enter commits (blurs) the active input/textarea/select.
- Accessibility & UX polish:
  - Strong :focus-visible outline using brand color.
  - aria-labels on icon buttons; id-based toggle for expand-all with aria-pressed.
  - Reduced-motion media query for friendlier animations.

Rationale (alignment with core principles):
- Clarity over clutter: Kept minimal controls, added semantics with data attributes and ARIA.
- Compact density: Retained small spacing/typography; behaviors added without new chrome.
- Seamless flow: Inline add/edit/reorder without modals or navigation.
- Progressive disclosure: Global expand/collapse respects writer context.
- Tactile feedback: Keyboard commit and tiny saved flash (non-intrusive) improve confidence.
- Low-friction iteration: One-click add, quick reorder, and confirm delete enable rapid editing.
- Portable performance: No frameworks, a few lines of vanilla JS; still fast and portable.

Limitations (by design for PoC):
- No persistence/backend calls; actions are purely in-UI. This matches the PoC spec but should be replaced with backend interactions later.
- Drag-and-drop remains out of scope; up/down arrows suffice for now.

