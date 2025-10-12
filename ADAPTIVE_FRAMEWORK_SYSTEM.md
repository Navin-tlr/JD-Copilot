# 🟠 Self-Forming Strategy Engine

> **Strategic intelligence without templates.**
> The analyst designs a bespoke response scaffold for every query—no hardcoded modes, no keyword gates, only context-aware reasoning.

---

## 🟠 Operating Principles
- Sense the question, infer latent intent, and size the stakes before writing.
- Invent the structure that best conveys the answer; sections emerge organically.
- Blend structured data with JD nuance to surface asymmetric advantage.
- Let the framework evolve mid-response if new insights demand a pivot.

---

## 🟠 Living Architecture
- **Conceptual seed:** The system prompt plants strategic lenses (Rapid Recon, Comparative Matrix, Deep Dive, etc.) as inspiration—not mandates.
- **Self-assembly:** The model chooses, fuses, or discards lenses as it responds, naming sections it creates.
- **Evidence discipline:** Every claim anchors to provided snippets or structured facts.
- **Tone mandate:** Aristotle’s clarity, Robert Greene’s strategic realism, Linus’s dry precision.

---

## 🟠 Implementation Snapshot
- Files: `app/rag.py` (unstructured), `app/agent.py` (hybrid).
- Both paths load a common persona prompt that describes principles, not templates.
- All keyword-triggered branching removed; no `_get_framework_structure`, no mode enums.
- Final prompts simply remind the model to self-assemble the scaffold described in the system prompt.

---

## 🟠 Data-Driven Focus
- Single-company emphasis now derives from context (unique company in snippets), not keyword checks.
- Hybrid responses treat structured output as spine and JDs as muscle, without prescribing section counts.

---

## 🟠 Testing Entries
- **Simple ask:** “List marketing companies” → concise reconnaissance with evidence bullets.
- **Comparative ask:** “Honasa vs Sugar positioning?” → model may invent a head-to-head matrix if useful.
- **Strategic ask:** “Craft Honasa advantage playbook” → rich multi-layer analysis built on the fly.
- **Hybrid ask:** “Who leads fintech hiring and why?” → structured counts fused with JD subtext.

Verify that each run produces a fresh structure tailored to the prompt—no recurring boilerplate blocks.

---

## 🟠 Extension Playbook
1. Adjust the inspirational lenses inside the system prompt when new analytical styles are desired.
2. Keep persona commitments consistent across all entry points (rag + hybrid) before introducing variants.
3. Log responses periodically to audit for drift back into rigid patterns.
4. When adding new data sources, surface their affordances inside the persona prompt as optional tools.

---

## 🟠 Guardrails Recap
- Absolute prompt priority: no downstream prompt overrides, no persona stacking.
- Disallow speculation; force clarity on missing data.
- Maintain adaptive structure while preserving dry wit and strategic rigor.

---

**Status:** Production-ready self-forming framework.  
**Last Updated:** 12 Oct 2025
