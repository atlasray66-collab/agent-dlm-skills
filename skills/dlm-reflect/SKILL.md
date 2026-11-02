---
name: dlm-reflect
description: Challenge a requirement, plan, design, or completed implementation when the user requests review, an accepted contract requires it, or material consequence and uncertainty justify it. Use Design Grill before planning or Closure Review against an accepted baseline; do not treat independent review as a default completion ceremony.
---

# DLM Reflect 7 Portable

## Purpose

Act as the proportionate DLM challenge layer. It sharpens consequential proposals and tests completion claims against their accepted criteria without inventing new completion conditions. The user outcome, Frozen/accepted baseline, repository contract, and actual artifacts—not this personal skill or reviewer preference—define blocking gates.

## Outcome-governance gate

Read and apply the shared [DLM Outcome Governance](../_shared/references/outcome-governance.md) before a Closure Review, formal audit, blocking Finding, or delegated review.

- Ordinary tasks default to targeted acceptance by the implementer. A formal independent audit is admitted only when the user explicitly requests it, an accepted task/release contract requires it, or consequence, uncertainty, irreversibility, and blast radius demonstrate actual value.
- Review measures the intended outcome and existing Acceptance Baseline; it does not optimize report completeness, reviewer comments, artifact counts, or “zero findings.”
- Keep target state, evidence state, and coordination state separate. A stale index may be a coordination gap without invalidating proven behavior; passing tests cannot prove release coordination.
- One stable target state gets at most one formal full audit. After repair, retest original FAIL conditions and direct regressions only. Do not audit the audit or reopen full review for administrative/EOL-only changes.

## Choose one mode

- `Design Grill`: challenge a requirement, proposal, architecture, or execution plan that has not yet been implemented.
- `Closure Review`: challenge a just-completed implementation or documentation result before closure.

If the target is “what should we build,” use Design Grill. If it is “is this really done,” use Closure Review. Do not apply implementation-evidence requirements to a design that has not been executed.

For Closure Review, declare whether it is `targeted acceptance` or `formal audit` and state the admission basis. Deep/Anchored work alone is not an admission basis.

## Portable-suite invariants

- Resolve the target repository/task and load its DLM context when it exists.
- Project statuses, acceptance rules, safety gates, and release procedures come from repository contracts.
- Personal skill files are not project context artifacts and must not be added to task manifests.
- Ask the user only for decisions that cannot be established from source, docs, evidence, or existing constraints.
- Challenge the weakest consequential premise first; do not dump an indiscriminate questionnaire.
- Stop when the critical premises are proven, disproven, or explicitly blocked with a minimal release condition.
- Suggestions outside applicable SSOT, accepted/Frozen criteria, and material safety boundaries are Advisory. They cannot block or force a switch between otherwise valid implementations.

## Mode A — Design Grill

1. Restate the intended outcome, consumer, constraints, and current proposal.
2. Read `references/grilling-protocol.md` and use the design claim type.
3. Identify the single unknown most likely to change scope, architecture, compatibility, cost, or acceptance.
4. Investigate locally first. If a product/authority choice remains, ask one focused question and use the answer to challenge the next weak premise.
5. Convert conclusions into testable success criteria and explicit exclusions.
6. Route to continued grilling, `dlm-plan`, an evidence spike, or blocked.

Use `templates/design_grill_template.md` for a materialized design review when the repository task calls for one.

## Mode B — Closure Review

### Re-anchor scope

- Read the task/Epic, context manifest, user authorization, repository rules, and accepted/Frozen baseline.
- Confirm the Baseline Owner, uniquely referenced criteria, Authorized Scope, required evidence, and stop line. A formal audit cannot start against Draft unless the owner freezes it.
- Capture current `git status`, tracked diff, staged diff, and untracked files for the relevant Git root.
- Build the actual changed-file set and compare it with the declared task scope.
- Preserve unrelated dirty work and pre-staged files.

### Review implementation and evidence

Read `references/reflect-phases.md`, then evaluate relevant lenses from `references/scenario-lenses.md`. Distinguish:

```text
source changed
build passed
tests passed
runtime behavior observed
product/UI/hardware acceptance passed
release artifact verified
commit created
push/deploy/field acceptance completed
```

One level never proves a higher level. For every completion premise, record `proven`, `disproven`, or `unknown` with evidence or the smallest next check.

Use semantic task/source identity by default: UTF-8 text without BOM, LF-normalized line endings, and repository-relative `/` paths. Use raw byte hashes only when the Frozen criterion makes exact bytes evidence. EOL/BOM/clean-smudge-only differences do not invalidate a Frozen baseline or consume another full-audit budget.

When scope drift, cross-layer coupling, shared protocol changes, or ownership ambiguity is plausible, read `references/boundary-audit.md` and perform the boundary audit.

### Route the result

Read `references/routing-rules.md` and choose exactly one primary route:

- `stop-verified`: declared outcome is complete, the stop line is reached, and no accepted contract or real consumer requires knowledge synchronization;
- `sediment`: declared outcome is complete and the user, accepted contract, or real consumer requires reusable knowledge/state synchronization;
- `continue-current`: missing work belongs to the same task;
- `dlm-plan`: new scope needs a new or revised task;
- `dlm-build`: knowledge/domain structure is stale;
- `blocked`: evidence or authority cannot currently be obtained.

Follow-up signals are not tasks until `dlm-plan` or the current execution log persists them.

## Execution checkpoints and evidence reuse

For repeated failures, contradictory evidence, changed assumptions, or a completion claim, use the relevant part of [Evidence and decisions](../_shared/references/evidence-and-decisions.md). These are bounded decisions within the current task, not automatic formal audits. Keep the existing primary routes. Tie actual AC results to the checked target and material conditions; evidence from an older target remains historical until applicability is established.

When the DLM workflow itself is being changed, [behavior evaluation](references/behavior-evaluation.md) supplies scenario checks and a bounded comparison method. Do not run that evaluation as a ritual for ordinary engineering work.

## Required constraints

- Never accept “the main path works” as complete without checking declared negative, persistence, lifecycle, accessibility, migration, safety, or field boundaries that apply.
- Never turn a Closure Review into a test-result paraphrase.
- Never infer code changes from conversation memory when a diff is available.
- Never invent missing evidence or silently lower the task's acceptance level.
- Never mark blocked/cancelled work complete merely to enable sediment.
- A blocking Finding must identify the violated Frozen criterion or SSOT clause, direct evidence/counterexample/failure, actual impact on the current outcome, and proof that it lies within Authorized Scope. Otherwise classify it as Advisory/Deferred.
- Out-of-scope discoveries do not enter the current repair loop. Escalate only safety, data-loss, false-premise, or SSOT-foundation failures as `Baseline invalidation` for owner recalibration.
- Do not continue because more optimization is possible. When all Frozen criteria pass, required evidence holds, and the stop line is reached, mark the baseline `Verified` and stop.
- A positive Closure Review may end as `stop-verified`. State `是否允许进入 sediment: yes` only when a user/contract/consumer trigger exists; sediment eligibility is a knowledge-synchronization route, not proof of a higher release/Git/deployment state.

## Output

Design Grill verdict:

```markdown
### [Design Grill Verdict]
- 方案主张:
- 已锁定决策:
- 被推翻或修正的假设:
- 剩余关键未知项:
- 可验证成功标准:
- 下一步路由: continue / dlm-plan / spike / blocked
```

Closure Review:

```markdown
### [Closure Review]
- 任务判定: complete / partial / drifted / blocked
- 复核类型与准入依据: targeted acceptance / formal audit
- Baseline: Draft / Frozen / Verified; owner; stop line
- 声明范围与实际改动:
- 已验证事实:
- 验证缺口:
- Blocking Findings / Advisory:
- 遗漏场景与边界风险:
- 证据等级:
- 后续路由:
- 是否允许进入 sediment: yes / no
```

Use `templates/closure_review_template.md` when the result must be persisted.

## Deterministic inventory, evidence-scope, and limit checks (`scripts/dlm.py`)

When reviewing full-coverage/parity tasks or v2 Ledger Epics, combine `dlm-reflect` with `python -X utf8 <skill-dir>/scripts/dlm.py`:

- **Evidence scope fidelity (`full` | `partial` | `sample` | `proxy`)**: `sample`, `partial`, or `proxy` evidence only establishes `implemented`, never terminal `verified` for a `coverage=full` obligation.
- **Full-population parity gate**: Run `dlm.py inv report <name> --gate` (or `dlm.py check`) to verify `total / pass / fail / gap / na / blocked / pending`. Any non-zero `pending`, `fail`, or `gap` blocks completion claims.
- **Limits vs. implementation budgets**: Verify that any hard cap is backed by a user `product` decision or verified `resource-fact`, never an executor `budget` that rejects valid inputs (`on_exceed=reject`).
- **Deterministic reopen classification**: Route defects by cause (`regression`, `omission`, `new-requirement`, `superseded`, `evidence-lost`); missing/expired evidence files (`evidence-lost`) mark obligations `stale` without presuming code failure.
