---
name: dlm-load
description: Load the minimum sufficient context from a repository-owned doc_llm before planning, implementation, review, or debugging. Use when the user names an Epic/Subtask, asks to initialize context, or the active repository already uses DLM. Do not borrow state from another repository or trigger for repositories without doc_llm unless explicitly requested.
---

# DLM Load 7 Portable

## Purpose

Lock one repository and load its own contract, constraints, active task, manifest files, and source anchors. This personal skill defines the loading method; repository state remains entirely repository-owned.

## Outcome-governance gate

Apply the shared [DLM Outcome Governance](../_shared/references/outcome-governance.md). Read it before `load-and-continue`, before treating a context gap as blocking, or whenever loading feeds formal review, delegation, release, or another external-state decision.

- Treat loading as one combined identity/scope safety check followed by the minimum facts needed for the next material decision.
- Do not repeat Session Init, refreeze authority, or generate control-plane artifacts when the repository/task identity is already stable.
- `load-and-continue` does not bypass governance: before the first substantive write, execution-capable delegation, external action, or state/resource mutation, confirm the applicable Acceptance Baseline is Frozen by its owner or that equivalent explicit session authorization supplies the same target, criteria, Authorized Scope, evidence, and stop line.
- A context gap blocks only when an applicable contract marks it required and its absence materially prevents the current claim or safe action. Unrelated administrative staleness is reported for consumer-driven closeout, not allowed to delay target work.
- Documentation, source, runtime evidence, and coordination state remain separate; load the layer that fits the decision instead of using one as a proxy for another.

## Repository resolution

1. Prefer a repository root explicitly supplied by the user.
2. Otherwise use the nearest Git root that contains the relevant `doc_llm`.
3. In a monorepo or nested-checkout ambiguity, inspect candidate `doc_llm/dlm.json` identities and ask only if the target still cannot be determined safely.
4. Read the applicable `AGENTS.md`, `doc_llm/dlm.json`, and `doc_llm/README.md` before interpreting paths or statuses.
5. Never load a neighboring project's DLM because it is familiar from memory or a prior conversation.

If the project has a contract, the declared `repository_root`, `doc_llm_root`, `project_id`, statuses, and compatibility rules are authoritative. Personal skill paths are never project context files.

## Intent modes

- `load-only`: the user asked only to inspect, summarize, or assess context. Remain read-only and stop after the context report.
- `load-and-continue`: the user already requested planning, implementation, review, or diagnosis. Load first, then continue the authorized task without asking for a redundant confirmation.

Loading is a workflow phase, not a platform mode and not mutation authority.

## Session init

On first entry, read the contract/README and applicable BRIEF/L0 constraints; reuse them while repository identity and relevant constraints remain stable. For a named or already-locked task, go directly to its Epic/Subtask and required manifest entries. Read the backlog/index only to discover ownership, resolve dependencies, or choose work within an already-authorized queue. An ad-hoc diagnosis or question does not authorize selection or execution of an unrelated backlog item.

When task selection is part of the user request or an already-authorized queue, select deterministically:

1. user-specified Epic/Subtask;
2. task already locked in the current conversation and still active;
3. in-progress task ordered by the repository's backlog/priority/ID rules;
4. dependency-ready planned task using the same order;
5. blocked tasks are reported with their release condition, not treated as executable.

If candidates remain tied after applying repository rules, show the smallest useful candidate set instead of guessing by file timestamps or reading every historical task.

## Current identity and resume

- When the user-supplied project has no Git metadata, lock its explicit directory plus its own DLM contract. Report Git state as unavailable; never adopt a parent or neighboring repository to manufacture an identity.
- Use `Epic/Subtask` as the canonical task identity. Resolve an old short dependency within its owning Epic first, then only if globally unique. A bare ID shared by several Epics needs disambiguation; it must not silently pick the first match.
- The current leading Meta table (or explicit `## Meta` section) is authoritative. Historical logs, archived plans, and an old Frozen entry do not override current status or acceptance. Read historical evidence only when the next decision needs it.
- Prefer an existing repository-owned `next` / `context` command when it provides identity, dependencies, blockers and read order. Do not install a new command merely to load context or treat its output as mutation authority.

## Task deep dive

1. Read the task and locate `<context_manifest>`.
2. For schema 2, require matching `project`, repository-relative `/` paths, and a concrete file per entry.
3. Every `<file>` has `path`, `intent`, and `required`; `section` and `defer` are optional.
4. Reject absolute paths, `..`, directories, sibling repositories, personal skill roots, and `.agents/skills` workflow files as task context.
5. Missing files required by the current task contract block the affected deep dive/claim. Missing optional files, or unrelated administrative records with no current consumer, become warnings.
6. `defer="true"` is valid only with `required="false"`; load it only when the current decision needs it.
7. Read independent files in parallel where useful. Honor `section` by loading the relevant section precisely.

For legacy manifests, follow the repository's compatibility rule and report the gap. Do not silently migrate while loading.

## Decision-focused context and resume

After required inputs, organize further reading around the next material question: applicable constraints, evidence and counterevidence, missing facts, and the next source entry. Relevance alone does not establish sufficiency. On a real resume, preserve the last applicable evidence and excluded failed routes; refresh changed dependencies instead of repeating Session Init.

For evidence reuse, changing L2 knowledge or repeated failure, read the relevant section of [Evidence and decisions](../_shared/references/evidence-and-decisions.md). For a useful set of explicitly identified changes, `scripts/dlm_impact.py --repo-root <repo> --changed-file <repo-relative-file> --json` can return read-only L2 review candidates, including optional `depends_on` propagation. It does not certify knowledge validity or supersede required manifest inputs. Do not run it for every routine read.

## Source anchoring

- Use `rg`, symbol navigation, project files, tests, logs, and generated evidence to locate implementation truth.
- Start with narrow source reads. Read full files when lifecycle, serialization, state-machine, or cross-member behavior makes local excerpts unsafe.
- Distinguish documentation claims, source facts, runtime evidence, and unresolved inference.
- If DLM and source disagree, report the mismatch and continue from current source/evidence unless the task is explicitly documentation-first.

## Ad-hoc loading

During execution, route through global L1/domain L1 to the smallest relevant L2 and source anchors. Do not repeat the whole Session Init when only one domain decision needs more context.

## Validation and output

Run the repository health check when contract/manifest integrity matters to the next decision or the user requested DLM validation. Use the generic doctor as supporting contract evidence, not as a ritual:

```powershell
python -B -X utf8 <skill-dir>/scripts/dlm_doctor.py --repo-root <repo> --require-contract
```

Classify failures against the current target and contract. A relevant contract/path failure can block the affected DLM action; an unrelated pre-existing or administrative warning cannot invalidate otherwise sufficient engineering context.

Report repository/project identity, selected task and selection basis, loaded constraints and source anchors, missing or stale context, the material impact of any blocking gap, and whether the original task will now continue. Once the next decision has sufficient context, stop loading and return effort to that work.

## Optional v2 Ledger brief (`scripts/dlm.py brief`)

When loading an Epic that uses `ledger.json`, run `python -X utf8 <skill-dir>/scripts/dlm.py brief <E> <S>` (or `dlm.py status`) to render the task brief, active obligations, unresolved hypotheses, and prior checkpoint state alongside `dlm_impact.py`.
