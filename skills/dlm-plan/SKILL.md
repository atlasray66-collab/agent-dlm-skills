---
name: dlm-plan
description: Turn a requirement into repository-owned DLM Epics, Subtasks, dependencies, evidence gates, and schema-2 context manifests. Use for new features, refactors, architecture changes, follow-up work, or task scaffolding in any repository that uses or explicitly requests doc_llm. Supports chat-only design and authorized materialization without assuming a specific project.
---

# DLM Plan 7 Portable

## Purpose

Convert a requirement into an executable, verifiable, resumable plan while preserving repository identity and user authority. This personal skill owns planning behavior; the target repository owns every plan file and task state.

## Entry gates

1. Resolve one target repository and read its `AGENTS.md`, `doc_llm/README.md`, and `doc_llm/dlm.json` when present.
2. Run the minimum `dlm-load` Session Init needed to understand project identity, current backlog, constraints, and existing task ownership.
3. Never create task artifacts in the current shell repository merely because it is open; use the repository the user actually targeted.
4. Never put personal skill files, absolute paths, `.agents/skills` copies, sibling repositories, or `..` paths into a project context manifest.
5. If the repository has no DLM and the user asked only for a plan, return a chat plan. Use `dlm-build` only when the user also wants DLM initialized.

## Select a planning mode

| Mode | Trigger | Output |
|---|---|---|
| `design-only` | User asks for analysis/plan but not files | Conversation plan, read-only |
| `materialize-new` | User asks to create/confirm a new DLM task | New Epic/Subtasks and indexes |
| `extend-existing` | Requirement belongs to an existing Epic | New or revised Subtasks without duplicating the Epic |
| `spike` | Key facts are unavailable | Evidence-acquisition task, not speculative implementation |

Explicit authorization to create, upgrade, or materialize the plan covers normal repository-local planning writes. Stop for confirmation only when there is a real scope fork, BRIEF/L0 semantic change, external material copy, destructive migration, or another consequential external mutation.

## Planning depth

- `quick`: ownership, dependencies, acceptance, and source anchors are already clear.
- `standard`: inspect source and domain routing before task decomposition.
- `deep`: cross-domain protocol, persisted formats, safety, hardware, security, or irreversible migration. Include alternatives, rollout, rollback, and field boundaries.
- `spike`: plan only how to establish missing facts and what decision those facts unlock.

Depth follows risk and uncertainty, not a fixed number of files or subtasks.

## Outcome-oriented planning governance

Apply the shared [DLM Outcome Governance](../_shared/references/outcome-governance.md). Its principles (causal relevance, claim-evidence fit, proportional rigor, criterion integrity, no proxy optimization, layer separation, marginal convergence, effort follows expected impact) are the planning rules; they are not restated here. Read the full reference before materializing execution-ready work, defining/freezing a baseline, planning formal audit or a named queue, or preparing delegated/subagent work.

Planning-specific application — for every material Subtask, gate, or process artifact, be able to answer:

1. Which intended system-state change, completion claim, or material risk does this serve?
2. What evidence class fits that claim, and who or what decision consumes it?
3. What material uncertainty remains if this action is omitted?
4. What observable condition makes further work unnecessary?

If these questions have no concrete answer, remove, defer, or convert the item into a narrowly bounded spike. Do not turn this section into a mandatory document, checklist, review ceremony, or artifact quota.

Classify work as `target work`, `substantive assurance`, or `administrative record`. Sequence plans as: one combined target/authority/safety lock, shortest causal implementation path, claim-matched validation, one consumer-driven synchronization pass, then independent review only when its risk benefit is established.

## Planning pipeline

### 1. Establish current truth

- Search existing Epics/Subtasks, source, tests, issues, and evidence before creating new work.
- Determine whether the requested capability is absent, partially implemented, already implemented but unverified, or already planned.
- Route to the existing owner when possible. Do not create a new Epic for a naming variation of existing work.
- Separate verified facts, inferences, user decisions, and unknowns.

### 2. Define scope and authority

Record the observable target state, completion claim, users/consumers, in-scope paths and behaviors, exclusions, dependencies, material risks, data/interaction flow, compatibility, mutation authority, and stopping condition. Separate applicable completion criteria from useful-but-nonblocking indicators. A plan may describe release/commit/deploy steps, but it must not imply those actions are already authorized.

For execution-ready materialization, create an inline Acceptance Baseline in `Draft` with: applicable SSOT/L0, one target, non-goals, a Baseline Owner, uniquely referenceable acceptance criteria, claim-matched evidence, a stop line, and `Authorized Scope` separated into allowed reads, allowed file writes, allowed external actions, and allowed state/resource mutations (`none` where inapplicable). Do not create a separate authority file, checker, or hash chain unless an existing machine consumer requires it.

Before substantive execution, formal audit, execution-capable delegation, or an external-state mutation, the Baseline Owner must make one `Frozen` decision. `Frozen` is not inferred from hashes, BOM/EOL, checkout form, or metadata. A baseline returns for recalibration only when its target, criteria, scope, dependencies, or stop line changes, or new facts establish SSOT conflict, false premises, safety risk, or data-loss risk. Mark `Verified` and stop when every Frozen criterion passes, required evidence holds, and the stop line is reached.

### Business semantics and task quality

For data or decision features, define only the material semantics: source fact versus plan versus estimate versus confirmed actual; entity identity; unit; reporting period/as-of time; scope; and behavior when evidence is missing. Preserve provenance and explicit human corrections. An import or model inference must not silently become actual work, approval, historical employment or a confirmed demand.

Choose an observable user outcome and a concrete before/after example. Any success metric names its population, numerator/denominator, time window and unknown-data behavior. Identify invariants and negative cases that can falsify the design. Counts of documents, tasks, tests or green checks are supporting evidence, not replacement objectives. Keep this inline and proportional; no extra mandatory artifact is implied.

Use canonical `Epic/Subtask` IDs in new dependencies and cross-task references. Read only current Meta for execution state, and keep baseline state under a separate `验收态` or `基线态` field. Plan immutable archived outputs separately from live recalculation when both are real consumers.

### 3. Define evidence levels

Do not collapse these states:

```text
planned -> implemented -> build/test verified -> runtime/behavior accepted
        -> release verified -> committed -> pushed/deployed/field accepted
```

Each task declares the highest level it must reach and the evidence required. Build success alone is not runtime, UI, hardware, migration, or product acceptance.

Evidence gates must state the claim they support. Engineering evidence, evidence records, and coordination records may reference one another, but they remain separate states; a synchronized task index cannot prove runtime behavior, and a passing runtime test cannot prove release coordination.

When defining evidence for consequential or reusable claims, distinguish the planned check from its observed result and bind the result to the checked target and material environment/configuration. Use existing AC IDs and evidence locations. Repeated ambiguous decisions may use the compact contract in [Evidence and decisions](../_shared/references/evidence-and-decisions.md); ordinary steps need no extra table or model call.

### 4. Decompose work

Each Subtask has one independently verifiable outcome and records:

- stable ID/title and owning Epic;
- status from the repository contract;
- dependencies as an acyclic graph;
- priority as a separate business/risk dimension;
- source and documentation anchors;
- acceptance criteria tied to observable evidence;
- the intended-state contribution or material risk reduced;
- exclusion scope and rollback/recovery boundary;
- a stopping condition that prevents redundant verification after material uncertainty is bounded;
- execution log/resume point;
- follow-up routing when completion reveals new scope.

Order Subtasks by dependency and expected outcome impact. Do not create documentation-only, audit-only, review-only, or metadata-only work unless a named consumer, decision, contract, or material risk makes that work causally necessary.

Use subagents for independently acceptable, nonconflicting units when parallel work has a concrete benefit and current host/tool rules permit it within existing task authority. Follow the shared delegation rules; user-owned Codex task creation remains a separate explicit intent. The task card supplies target, baseline/SSOT, Authorized Scope, prohibitions, deliverables, evidence, stop line, and completion action. Delegates remain read-only unless the task card grants specific writes or already-authorized external actions.

Default status semantics when the project has not declared alternatives:

- `📋 待办`: dependency-ready or waiting in backlog;
- `🔄 进行中`: actively owned;
- `⛔ 阻塞`: has reason, attempts, owner, and release condition;
- `🛑 已取消`: has cancellation reason and replacement route;
- `✅ 完成`: all declared completion gates passed.

Claim/lease work items are optional repository mechanisms. Add them only when the project already uses them or the user requests parallel execution; never invent a second state SSOT beside the task contract.

### 5. Generate context manifest v2

```xml
<context_manifest schema="2" project="{project_id}" task="S001" epic="E001">
  <file path="doc_llm/00_Global/L0_global_redlines.md" intent="global constraints" required="true" />
  <file path="doc_llm/Tasks/E001_example/README.md" intent="epic boundary" required="true" />
  <file path="src/Example.cs" intent="implementation anchor" required="true" />
  <file path="doc_llm/Domains/1_example/L2_Modules/runtime.md" intent="runtime traps" required="false" defer="true" />
</context_manifest>
```

Requirements:

- repository-relative `/` paths based on the contract;
- concrete files only;
- matching project identity;
- every entry includes `path`, `intent`, and `required`;
- `defer="true"` only with `required="false"`;
- no absolute, traversal, directory, external-repository, personal-skill, or repository-local skill-copy paths.

External sources may be recorded as provenance outside the manifest. Copy them only with explicit authorization and a clear maintenance/sensitivity boundary.

### 6. Materialize and index

Create or update only the needed Epic README, `plan/`, `audit/`, `subtasks/`, `references/`, and backlog/index entries. Subtask metadata is the status SSOT; generated Epic/backlog views are indexes.

Use the deterministic indexer after task changes:

```powershell
python -B -X utf8 <skill-dir>/scripts/sync_epic_index.py <epic-dir> --repo-root <repo>
```

Read these references only when relevant:

- `../_shared/references/outcome-governance.md` — mandatory detailed rules for execution-ready baselines, formal audit, named queues, or delegation;
- `references/pipeline-phases.md` — detailed planning stages;
- `references/special-scenarios.md` — migration, cancellation, spike, and multi-repo cases;
- `references/validation-and-tooling.md` — validators and index tooling.

## Validation

Before reporting materialization complete:

1. Confirm the plan states an observable intended outcome, material uncertainties, applicable completion criteria, and a stopping condition.
2. Confirm every material action is causally relevant, its evidence fits its claim, and rigor is proportional to risk and blast radius.
3. Validate project identity, manifest schema/path safety, required file existence, status legality, and dependency acyclicity.
4. Run the repository DLM health check when its contract/path claims apply to the materialized scope.
5. Run generic `dlm_doctor.py --require-contract` when available and when it adds a current contract/path claim not already established by equivalent repository validation.
6. Run the Epic indexer in preview/normal mode when the changed index has a current task/coordination consumer.
7. Inspect the exact diff and confirm no other repository, user work, release state, or unrelated task was changed.

A validator failure blocks materialization only when it violates the current baseline, applicable DLM contract, touched artifact integrity, or a demonstrated material safety boundary. Report unrelated pre-existing or administrative failures separately; they cannot silently become completion criteria. A green validator proves only the contract claim it measures, not the intended engineering outcome.

For one stable target state, plan at most one formal full audit. After fixes, revalidate the failed conditions and direct regressions only; administrative changes do not reopen unrelated validation. Report the selected mode/depth, repository identity, baseline state/owner, created or reused task IDs, key decisions, claim-matched evidence gates, validation results, stopping condition, and the next highest-impact executable entry point.

## Dual-engine routing, mechanical inventory (`dlm inv`), and v2 ledger

In addition to DLM 7 Markdown planning (`sync_epic_index.py`), `dlm-plan` includes the shared deterministic CLI (`python -X utf8 <skill-dir>/scripts/dlm.py`):

- **Fast-track vs. Ledger track**: Keep `Lite`/`Medium` tasks on the lightweight DLM 7 Markdown path unless the repository already uses `ledger.json`. Use the full v2 Ledger (`dlm.py epic create`, `task create`, `plan-check`, `adopt`) or Mechanical Inventory (`dlm.py inv`) when the task is `High`/`Max`/`Ultra`, involves full-set parity/migration, or coordinates multi-session lease queues.
- **Mechanical inventory (`dlm inv`) & lease bridge**: Whenever the user asks for full coverage, 1:1 parity, or an exhaustive module/operator audit, follow [inventory.md](references/inventory.md) and [slicing.md](references/slicing.md) to mechanically enumerate the population (`inv new`, `inv source --kind glob|grep|cmd`, `inv diff`, `inv export-lease`, `inv sync-lease`, `inv report --gate`).
- **Limits (`product` | `budget` | `resource-fact`) & Reopen causes**: Follow [records.md](references/records.md) and [epic-sizing.md](references/epic-sizing.md). Executor-chosen implementation `budget` limits must never set `on_exceed=reject` to reject valid business inputs or silently shrink user goals. Reopening obligations must classify the exact cause (`regression` | `omission` | `new-requirement` | `superseded` | `evidence-lost`).
