---
name: dlm-close-release
description: Orchestrate safe DLM closure, optional release verification, and optional exact-path Git commit for any repository. Use when the user asks to close or sediment a task, prepare or verify a release, update versions, or commit the completed scope. Commit, push, tag, deploy, and artifact copying remain separate explicit authorities.
---

# DLM Close Release 7 Portable

## Purpose

Close one verified engineering scope without conflating task completion, knowledge sediment, release production, versioning, Git commit, or deployment. This personal skill orchestrates the lifecycle; repository contracts and child skills retain their technical rules.

## Outcome-governance gate

Read and apply the shared [DLM Outcome Governance](../_shared/references/outcome-governance.md) before any closure write, release/version mutation, formal audit, staging, or commit.

- Keep engineering target state, evidence state, DLM coordination state, release state, Git state, deployment state, and field acceptance separate. Advancing one does not imply another.
- Resolve one Acceptance Baseline for the authorized mode. Before closure writes or release/Git mutation, the Baseline Owner freezes its target, non-goals, Authorized Scope, required evidence, criteria, and stop line once. Hashes, BOM/EOL, checkout representation, and receipts do not freeze or invalidate it.
- Closure/sediment/release records are target work only when requested or consumed by the applicable contract/decision. Pure administrative changes do not reopen unrelated build/test/audit.
- Use one formal full audit at most for a stable target state, and only when the user, accepted contract, or material risk justifies it. After repair, revalidate failed conditions and direct regressions only.

## Select the narrowest authorized mode

| Mode | Allowed actions | Typical intent |
|---|---|---|
| `close-only` | Closure Review, sediment, DLM validation | “关闭任务”“完成沉淀” |
| `release-verify` | close-only plus repository release/version build and artifact metadata verification | “准备发布”“验证发布版本” |
| `release-commit` | release-verify plus exact-path staging and commit | “更新版本并提交 Git” |

Default to `close-only`. A commit request does not authorize push, tag, deploy, publish, or artifact copying. Each is separately authorized. If wording is insufficient to distinguish a Git/version mutation, stop once and ask.

## Repository and contract lock

1. Resolve one Git root and read its `AGENTS.md` and DLM contract.
2. Run the minimum `dlm-load` needed for the task and release profile.
3. Do not copy this personal skill into the repository or add it to a context manifest.
4. Use the repository-declared release profile:
   - `none`: closure only unless the user supplies a procedure;
   - `dotnet`: use `dlm-version-master` in composition mode;
   - `custom`: use the repository-owned version/build/verification contract.
5. In multi-repository or submodule work, use a separate allowlist, validation result, and commit per Git root. Do not claim cross-repository atomicity.

## Phase 0 — Scope snapshot

Before any write, perform this combined writer/scope safety snapshot once:

```powershell
git status --short
git diff --name-status
git diff --cached --name-status
git ls-files --others --exclude-standard
```

Build exact sets for task-owned candidates, pre-existing unrelated changes, and pre-staged files. If ownership cannot be established from user intent, Frozen Authorized Scope, task docs, and diff, stop before mutation. Do not repeat the snapshot merely to manufacture authorization evidence. Never use `git add .` or `git add -A`.

## Phase 1 — Closure Review

Perform targeted Closure Review against the Frozen criteria and claim-matched evidence. Use `dlm-reflect`; formal independent review is optional unless the user requests it, an accepted contract requires it, or material risk justifies it. Continue when the declared completion level is proven, or route a material remaining gap as current-scope work/blocked. Build success alone is not behavior, UI, hardware, migration, safety, or field evidence; equally, a stale administrative index alone does not disprove proven behavior.

## Phase 2 — Sediment

When the user requested sediment, the accepted repository/task contract requires it, or a real loading/release/decision consumer needs synchronization, run `dlm-sediment` once in composition mode. Write only confirmed task/domain knowledge and status. BRIEF/L0 approval gates remain active. Child skills must return exact changed paths and must not stage or commit. If no such trigger exists, record `sediment: not required` and preserve the verified engineering conclusion.

Synchronize once for real task/knowledge consumers and reuse existing evidence. Do not create synonymous receipts or rerun unrelated engineering validation because only coordination records changed.

For `close-only`, run DLM health checks only when the authorized closure includes DLM state or a current contract/consumer claim depends on them, then stop after the closure report. A skipped non-applicable check is not a failure.

## Phase 3 — Release verification

Only for release modes:

1. Resolve the repository release profile and exact output scope.
2. Determine version intent. Major/minor require explicit intent. Patch/auto is allowed only when release intent exists and the repository contract declares that default.
3. Run the repository version/build process serially unless its contract specifies otherwise.
4. Run tests and verify public binary/package metadata and hashes required by the Frozen release criteria/profile; do not add reviewer-preference checks as new release conditions.
5. Add only intentional version state, changelog, release infrastructure, and task-owned source files to the candidate allowlist.

A build, test, hash, or metadata failure blocks commit/release claims when that check is required by the Frozen release baseline, repository profile, or a demonstrated material output risk. Unrelated pre-existing or administrative failures are reported separately and do not silently expand the release criteria.

## Phase 4 — Exact staged-set gate

Only for `release-commit`:

- Normalize the allowlist to repository-relative exact paths.
- Compare current staged files with the pre-staged snapshot.
- Do not unstage user work. If pre-staged files fall outside the allowlist, stop and report.
- If an allowlisted file mixes unrelated pre-existing changes that cannot be safely split, stop and ask.
- Exclude secrets, machine-local configuration, `bin/`, `obj/`, `out/`, logs, captures, publish/staging output, and temporary artifacts unless explicitly requested and appropriate.
- Run whitespace/encoding checks required by the repository.

## Phase 5 — Stage and commit

```powershell
git add -- <exact-paths>
git diff --cached --name-status
git diff --cached --stat
git diff --cached --check
git status --short
```

Require exact equality between staged paths and the approved allowlist. Before the commit, run the pre-commit reviews required by the global AGENTS.md (the `ponytail-review` gate and its guard marker) and by the repository, against this exact staged diff; resolve or explicitly retain each finding as those rules require. If a required review skill or hook is unavailable, stop before committing and report that gap instead of bypassing it. Commit once per Git root using repository conventions. Do not amend unless requested. After commit, inspect `git show --stat --oneline HEAD` and the remaining worktree.

## Failure rules

- A nonzero child command blocks later phases only when it fails a current Frozen criterion, applicable contract, touched-artifact integrity check, or material safety/release boundary. Unrelated pre-existing and administrative failures are reported without becoming new gates.
- A blocked task is not closed; persist its reason, owner, attempts, and release condition.
- Cancelled work may persist cancellation state without pretending successful release.
- Output locks are reported, not force-deleted.
- Unrelated work remains untouched.
- `Baseline invalidation` is reserved for new SSOT conflict, false premise, safety, or data-loss risk. EOL/BOM, clean/smudge, timestamp, display-order, or receipt-only changes do not invalidate or reopen full validation.

## Final report

Report mode, repository/project identity, Acceptance Baseline state/owner/stop line, Closure Review type/verdict, sediment consumers/paths, DLM checks, release profile and version changes, claim-matched verified artifacts, staged allowlist, commit hash if any, Blocking versus Advisory gaps, and unrelated files deliberately untouched. Explicitly state which of commit/push/tag/deploy/artifact-copy were not performed. Stop at the authorized mode boundary; do not automatically activate the next Subtask, work item, Deferred Finding, push, tag, or deployment.
