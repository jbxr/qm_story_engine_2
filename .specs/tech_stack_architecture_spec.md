# 🧱 Tech Stack & Architecture Spec

This document defines the guiding principles and optional technologies for implementing the story engine. It is designed to be **tech-stack agnostic**, with just enough constraint to ensure maintainability, performance, and creative focus.

---

## 🎯 Goals

- **Author-first**: Fast, intuitive UI/UX for writing, reviewing, and navigating story content
- **Low complexity**: No frontend state management unless absolutely necessary
- **Composable data model**: Clear schemas to support timeline continuity, character arcs, and goal tracking
- **LLM-ready**: Native support for embedding, search, and prompt grounding
- **Adaptable**: Stack should allow migration to desktop apps (e.g. Swift, Tauri), or headless backend APIs

---

## ✅ Core Technology Commitments

| Layer      | Technology        | Rationale |
|------------|-------------------|-----------|
| DB         | **Supabase** (Postgres) | Hosted, scalable, real-time, built-in auth and pgvector support |
| Search     | **pgvector**      | Semantic similarity, vector search, and embedding storage |
| Embeddings | **OpenAI or Groq API** | High-quality embeddings for semantic graph + LLM grounding |
| Hosting    | **Supabase**      | Immediate prototyping with room to grow |

> All other layers remain **flexible** and should follow the principles below.

---

## 🤖 Backend Options (Evaluated)

### ✅ Python (FastAPI or Flask)
- Familiar, fast to prototype
- Rich ecosystem for AI, LLMs, and scientific tooling
- Works well with Jinja2 if staying server-rendered
- **Cons:** State management and templating can get unwieldy without strong discipline

### ✅ SvelteKit (Web or Desktop via Tauri)
- Great DX, small bundle size, simple reactivity
- Pairs well with Tailwind
- Easy transition to Tauri for a MacOS/Windows-native writing tool
- **Cons:** JS/TS knowledge required; limited SSR control if using Tauri frontend-only

### 🔄 Rust (Tauri Backend or Fullstack w/ Leptos/Yew)
- Blazing fast, native-ready, low-level control
- Ideal for long-term performance and offline mode
- **Cons:** High barrier to entry, slow iteration, limited LLM ecosystem support

### 🚫 PHP (Laravel/TALL)
- Not under consideration

### 🟡 Go
- Great for performant backend services
- Fast compile times, static binaries, and good for CLI tooling
- **Cons:** Minimal templating and UI support; not a fit for UI-heavy authoring app unless paired with something like Svelte frontend

---

## 🎨 Frontend Principles (Regardless of Stack)

- **Desktop-first layout**, assuming widescreen usage
- **Dark mode by default**
- **No frontend routing or state management libraries**
- **Minimal JS**: all interactions should be progressive-enhancement-friendly
- **Reactivity only where helpful**: dialogue editing, goal linking, etc.

---

## 📦 Current Stack (Prototype)

| Area        | Tech         | Notes |
|-------------|--------------|-------|
| Frontend    | HTMX + Jinja | Simple, declarative; struggling with layout/state |
| Enhancements| Alpine.js, Hyperscript | Added complexity, unclear ROI |
| Backend     | FastAPI      | Good but tightly coupled to Jinja flow |
| Deployment  | Supabase + Replit | Quick iterations, but not ideal long-term |

This setup is **under active evaluation** and may be replaced.

---

## 🔁 Migration Flexibility

The specs are written to support:
- Server-side HTML rendering OR client-side apps
- Static layout OR Tauri-powered desktop experiences
- Dynamic scene generation via LLM OR deterministic editing

---

## 📌 Recommendation

Stick with Supabase as your data and auth layer. Then:

- ✅ Finalize data modeling and core CRUD logic first
- 🟡 Pick either **SvelteKit** or **Python (FastAPI/Flask)** for early MVP
- ❌ Avoid mixing HTMX, Alpine, Hyperscript unless you strictly constrain how they're used

Once core features are stable, revisit Tauri/SvelteKit for long-term desktop authoring UI.

---

## 🧭 Next Steps

- Confirm backend choice (Python or Svelte)
- Scaffold scene blocks UI using current stack, while following new UX simplifications
- Maintain tech-agnostic spec format to preserve portability

