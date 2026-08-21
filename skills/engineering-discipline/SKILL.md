---
name: engineering-discipline
description: MANDATORY GLOBAL SOP for ALL work. Every project/workflow decomposes into PHASES that run continuously and automatically IN SEQUENCE. A phase may NOT be marked complete or advance to the next phase until it passes the mandatory PHASE GATE (TEST -> VERIFY -> AUDIT -> DEBUG -> FIX -> ENHANCE -> CONFIRM), each step producing evidence. Continuity is compaction-proof via auto-checkpoint + auto-resume. Owns the lifecycle, phase-gate, and LESSONS.md memory; delegates all token-saving mechanics (dedup/compression/checkpoint tooling) to the unified token-savings skill with ZERO duplication. Load at the start of ANY task, before compaction, and after any fix.
agent_created: true
---

# Engineering Discipline — The Mandatory Global SOP

This is not advice. It is the operating procedure for **every** piece of work we do.
It converts "talent" into "a loop that never drops state, never ships unverified,
and never re-derives from scratch." The loop is the product.

> Token mechanics (dedup, compression, safe-mode, hygiene, the checkpoint tool)
> are NOT restated here. Apply them from the unified `token-savings` skill inside
> every phase. Re-stating them would create drift between two skills. This skill
> owns the **phase model, the gate, continuity, and LESSONS.md** — nothing else.

---

## 0. Authority & scope (NO OPT-OUT)

- Applies to **ALL** projects, workflows, and tasks: code, docs, research, data,
  builds, reviews. There is no exempt category.
- It **cannot be skipped**. If a phase looks trivial, the gate still runs — as a
  fast check — but is never omitted. "Too small to verify" is a failure mode, not
  a valid shortcut.
- **Default mode is AUTO-ADVANCE.** The agent drives phases through the gate and
  into the next phase **without waiting to be re-prompted**. It stops ONLY for:
  1. a genuine decision only the user can make,
  2. an external/blocking dependency it cannot resolve,
  3. a gate failure the user must explicitly accept risk on.
  Everything else advances on its own. This is what "continuous and automatic
  in sequence" means in practice.

---

## 1. Phase decomposition (do this FIRST, every task)

Split the work into **PHASES** before doing the work.

- A **phase** = one coherent unit of work with a clear **EXIT CRITERION**.
- Each phase carries: **ENTRY** criteria → the work → the **GATE** → **EXIT** criteria.
- Capture phases in the task list so progress is visible at all times.
- Granularity rule: a phase is small enough to fully gate, large enough to be
  meaningful. If you can't write an exit criterion, the phase is undefined — define it.

---

## 2. The phase loop (continuous, automatic, in sequence)

For each phase, **in order, without pausing**:

1. **Do the work** — Study → Synthesize → Implement → Monitor.
2. **Run the GATE** (Section 3).
3. **Gate PASSES** → mark phase **COMPLETE** → **auto-advance** to the next phase's ENTRY.
4. **Gate FAILS** → Debug → Fix → re-run the failing gate steps (loop *inside* the
   phase). **Do NOT advance** until it passes.

The loop only ends when the final phase is gated and complete, or a stop condition
in Section 0 is hit.

---

## 3. The PHASE GATE (mandatory, evidence-backed, in order)

Every gate step MUST produce **evidence** (command output, diff, audit note, test
log). "Not run" is NOT "pass". A claim without an artifact is a failure.

| # | Step | What it does | Evidence required |
|---|------|--------------|-------------------|
| 1 | **TEST** | Execute the phase's defined tests/checks. | Raw output (command, diff, result, pass/fail). |
| 2 | **VERIFY** | Confirm outputs meet the phase's acceptance criteria. Verify the *artifact*, not the intent. | Mapping of criterion → observed result. |
| 3 | **AUDIT** | Independent review: correctness, assumptions, risks, edge cases, token/quality impact. | Audit note; for code, run `token-savings` crl + quality gate. |
| 4 | **DEBUG** | If TEST/VERIFY/AUDIT found issues, diagnose **root cause** (never symptom). Re-attempting the same failing action is forbidden. | Root-cause statement. |
| 5 | **FIX** | Apply root-cause fix. Add a **guard** so it cannot silently return. Write the LESSONS.md row *as part of the fix*. | Diff + LESSONS row + guard description. |
| 6 | **ENHANCE** | Improve **only** what audit/monitoring proves weak. No gold-plating before the baseline works. | Before/after note; scope justification. |
| 7 | **CONFIRM** | Re-run verification after fixes. Only then mark COMPLETE and auto-advance. | Final green check. |

**Gate PASS rule:** all steps PASS, or are explicitly **WAIVED** with a documented,
approved reason. Any step NOT RUN → gate is OPEN → the phase **cannot advance**.

---

## 4. Continuity — auto-resume across turns & compaction

The loop survives context loss. This is what makes "continuous" real across sessions.

- **End-of-turn checkpoint:** emit `RESUME.md` via the `token-savings` checkpoint
  mechanism (`toks` cli `checkpoint` / `resume.py`), recording: current phase,
  gate status per step, open questions, next phase, lessons. Fire on the
  **observable** trigger — end-of-turn with open work — never on an invisible
  "before compaction" event.
- **Auto-resume:** on resume or after compaction, parse the checkpoint **FIRST**,
  then continue the gate/phase. Never re-derive from scratch.
- **Task list mirrors phases** for live visibility; update status as the gate moves.

---

## 5. LESSONS.md carry-over (the compounding memory)

Every fix gets a row. Append-only, never overwrite:

| Date | Context | Symptom | Root cause | Fix / prevention |
|------|---------|---------|------------|------------------|

- Write the row **as part of the fix**, not later. If you can't, the fix isn't done.
- When a cheap path (deterministic rule, cache, guard) would have caught a bug the
  expensive path found, **add the cheap path** — don't just widen the search.
- Project-specific lessons live in `<project>/.workbuddy/memory/`; cross-project
  principles live in `~/.workbuddy/MEMORY.md`.
- This file IS the "monitor our learning" artifact — the loop gets sharper each cycle.

---

## 6. Quality gates & anti-patterns (delegated — see token-savings)

- **Protected zones:** `[[KEEP]]…[[/KEEP]]` survive every compression.
- **"not run" is not "pass":** if a check didn't execute, report NOT RUN, never "clean".
- **stale cache is a silent failure:** fingerprint inputs; auto-rebuild on change.
- **verify the artifact, not the intent:** test regexes/logic against real input.
- **safe-mode:** never compress secrets/stack traces/errors into oblivion.

**Anti-patterns this SOP kills:**
- Marking a phase complete without a passing gate.
- Re-attempting the same failing action (root-cause first).
- Pausing to ask "should I continue?" when no decision is needed.
- Gold-plating before the baseline works.
- Treating "no error" as "correct" when the check never ran.
- Silently dropping context at compaction.

---

## 7. Integration

- **token-savings** (mandatory companion): apply its unified rules inside every
  gate step; use its checkpoint tool for continuity. Single source of token truth.
- **rag-engineering** (companion when retrieval-augmented): apply token-savings
  compression/safe-mode to retrieved context.
- **Trigger:** load this skill at the start of any multi-step task, before
  compaction, and keep LESSONS.md updated after every fix. It is the default
  operating mode for all work — no separate activation needed.
