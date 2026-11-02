---
name: dlm-sediment
description: Synchronize verified implementation knowledge, task progress, decisions, and traps into repository-owned doc_llm when the user, an accepted contract, or a real future consumer needs it. Use after the target result stabilizes; do not make sediment or independent review a default prerequisite for engineering completion, release, or Git commit.
---

# DLM Sediment 7 Portable

## Purpose

Keep repository knowledge aligned with verified implementation and task outcomes. This personal skill supplies the write-back method; it does not own the repository contract, decide completion, stage Git, create releases, or commit.

## Outcome-governance gate

Apply the shared [DLM Outcome Governance](../_shared/references/outcome-governance.md). Read it before sediment writes, blocking a closure because of knowledge state, or composing with close/release.

- Sediment is target work when the user requested documentation/governance state. Otherwise it is consumer-driven synchronization performed once after the engineering result stabilizes.
- Reuse existing claim-matched evidence. Do not rerun unrelated builds, tests, runtime checks, or full audits merely because task metadata, indexes, timestamps, formatting, or knowledge prose changed.
- A missing/stale DLM record blocks only when an accepted contract or real loading/release/decision consumer depends on it and the current target is materially affected. Administrative sync cannot retroactively invalidate proven engineering behavior.
- Keep target, evidence, coordination, release, and Git state separate. Sediment records a decision; it does not create that higher-level state.

## Entry gate

1. Resolve the target repository and load its `AGENTS.md`, DLM contract, task, and relevant domain routes.
2. Require an evidence-backed completion/blocking decision with the target, applicable criteria, proven facts, gaps, and stop line. Use `dlm-reflect` when the user requests it, an accepted contract requires it, or material risk justifies it; do not require formal independent review merely because work is nontrivial.
3. Explicit user sediment intent, an accepted task contract with a real knowledge consumer, or authorized `dlm-close-release` composition may start writes. Resolve a Frozen synchronization baseline with that trigger/consumer, exact Authorized Scope, knowledge claims, and stop line before writes. Do not treat a conversational hint as permission to rewrite BRIEF/L0.
4. Personal skill files and repository-local skill copies are workflow inputs, not context-manifest or sediment targets.
5. In composition mode, return exact changed paths to the orchestrator and never stage, commit, version, build, publish, or deploy.

## Phase 1 — Harvest objective changes

Use the actual Git root and collect:

```powershell
git diff --cached --name-status
git diff --name-status
git ls-files --others --exclude-standard
```

Restrict analysis to the task-owned scope and preserve unrelated dirty/pre-staged work. Read changed source, tests, configuration, runtime evidence, and task logs. Conversation memory may help navigate but is not implementation evidence.

Map changed paths through global/domain L1 routes and L2 `match_globs`. Mark unmapped durable behavior as a possible new L2 or routing repair; do not force every changed file into documentation. When document dependencies matter, the read-only `dlm-load/scripts/dlm_impact.py` can shortlist direct and transitive candidates from an explicit changed-file list. Inspect the relevant claims before treating a candidate as stale; an impact hint does not invalidate engineering acceptance.

## Phase 2 — Classify impact

| Type | Meaning | Default action | Approval |
|---|---|---|---|
| Task progress | Outcome, evidence, block/cancel/complete state | Update Subtask metadata/log | Project contract |
| L2 behavioral | State machine, data flow, decision, trap, evolution | Precise update or append | Authorized task scope |
| L1 structural | New/renamed module or route | Regenerate/update route index | Authorized task scope |
| L0 constraint | Stable global/domain must/must-not rule | Exact proposal first | Explicit user approval |
| BRIEF evolution | Product/domain purpose, audience, terminology, ownership | Exact proposal first | Explicit user approval |

Do not create “L2 factual” catalogs of signatures or source listings. Code and generated schemas remain the fact source; L2 records knowledge not cheaply recovered by search.

## Phase 3 — Write back

### Task

- Append the outcome, evidence, material gaps, sediment paths, and the relevant resume/stop point. Include Closure Review or a follow-up route only when one was actually used; do not create a review or next task merely to fill an execution-log field.
- Apply only statuses allowed by `doc_llm/dlm.json` or legacy project contract.
- `⛔ 阻塞` includes reason, owner, attempts, and release condition.
- `🛑 已取消` includes cancellation reason and replacement path.
- `✅ 完成` is allowed only when the task's declared evidence level passed.
- Treat Subtask metadata as SSOT; generated Epic/backlog tables are indexes.
- If engineering criteria are already satisfied but a nonblocking administrative index is stale, preserve the engineering conclusion and report/synchronize the coordination gap without reopening unrelated validation.

Regenerate the Epic index with the personal skill script:

```powershell
python -B -X utf8 <skill-dir>/scripts/sync_epic_index.py <epic-dir> --repo-root <repo>
```

### L2

- Update only durable state machines, trade-offs, traps, compatibility boundaries, and evolution.
- Prefer precise append/update over full rewrites. Fix stale contradictory text rather than stacking a second truth beside it.
- Add source/navigation anchors, not copied implementations. For knowledge that can drift, record material applicability conditions, supporting evidence and review triggers; use optional repository-relative L2 `depends_on` only when a real consumer needs propagation. Preserve historical results and identify replacement conclusions. See [Evidence and decisions](../_shared/references/evidence-and-decisions.md) for the shared conventions.
- Split only when ownership or loading behavior improves; do not use arbitrary size thresholds as completion gates.

### L1

- Update module/domain routing and interaction topology when ownership changes.
- Prefer deterministic route generation from L2 metadata:

```powershell
python -B -X utf8 <skill-dir>/scripts/sync_l1_route.py <domain-dir> --repo-root <repo> --preview
```

Run without `--preview` only after reviewing the proposed changes.

### L0 and BRIEF

Present each semantic change as an exact proposal with target file, before/after text, reason, evidence, and impact. Apply only approved items. A task that discovered an unapproved constraint can record the proposal and remain blocked without rewriting L0.

## Phase 4 — Validate

1. Run project DLM health checks and generic doctor when their contract/path claims apply to the touched sediment scope.
2. Validate status legality, project identity, schema-2 manifests, required paths, route/index synchronization, and task completion gates.
3. Inspect the exact diff and confirm no unrelated repository or personal skill files were changed.
4. A nonzero result blocks a successful sediment claim only when it violates the accepted baseline, applicable DLM contract, touched artifact integrity, or a demonstrated consumer/safety boundary. Report unrelated pre-existing and administrative failures separately.

Validation of sediment proves only knowledge/coordination claims. Do not reopen a stable engineering build/test/audit unless the sediment change altered semantic source, an accepted task contract, required executable configuration, or byte-exact evidence.

## Output

Report trigger task, completion-decision source (and Closure Review only when used), real consumers served, exact Task/L2/L1/L0/BRIEF paths changed, approvals applied or deferred, validation claims/results, Advisory follow-ups, and whether the DLM synchronization itself remains blocked or complete. State engineering status separately, and state that no staging/commit/release occurred unless an authorized orchestrator reports those later phases. Stop after the needed synchronization; do not automatically execute the next task or Deferred Finding.

## Extended knowledge-base CLI (`scripts/dlm.py kb`)

Alongside `dlm_doctor.py` and `sync_l1_route.py`, use `python -X utf8 <skill-dir>/scripts/dlm.py kb` for lifecycle hygiene (see [l2_writeback_contracts.md](../_shared/references/l2_writeback_contracts.md) and [l2-audit-rubric.md](references/l2-audit-rubric.md)):

- `dlm.py kb stale [domain]`: compare `L2` `match_globs` and `last_updated` against Git source history to detect stale `L2` modules.
- `dlm.py kb map <target> [--json]`: audit `L2` documents for size bloat, changelog accumulation, layer leaks, and glob overlap.
- `dlm.py kb sediment [paths...]`: list candidate `L2` / `Reference` / `SOP` documents matching changed paths.
- `dlm.py kb scaffold ...`: scaffold project/domain `BRIEF`, `L0`, `L1`, `L2`, `Reference`, and `SOP` files from Chinese templates.
