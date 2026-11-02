---
name: dlm-build
description: Create, migrate, validate, or incrementally maintain a repository-owned doc_llm knowledge system. Use when a project needs its first DLM contract, BRIEF/L0/L1/L2/Tasks structure, domain routing, schema migration, or deterministic health checks. The workflow is portable and must not assume a particular repository.
---

# DLM Build 7 Portable

## Purpose

Build a durable, repository-local knowledge and task system without coupling the skill itself to that repository. The personal skill supplies the workflow; each repository owns its `doc_llm`, contract, project identity, release profile, scripts, and task state.

## Outcome-governance gate

Apply the shared [DLM Outcome Governance](../_shared/references/outcome-governance.md). Read it before writes, migration, blocking health decisions, formal audit, or delegated work.

- A DLM knowledge/governance state is target work when the user requested it. Otherwise create or update an artifact only for a real loading/routing consumer, accepted contract, decision, or concrete material risk.
- Health checks, route counts, document sizes, front matter, indexes, hashes, and green status are evidence/coordination signals; they do not substitute for useful knowledge, correct routing, or engineering truth.
- After one combined repository/authority/write-scope check, follow the shortest causal path to the requested DLM state. Do not generate unused scaffolding or consecutive governance artifacts before a useful target advance.
- Existing unrelated or administrative DLM defects are reported separately and do not silently become current completion criteria. Current-scope contract, identity, path-safety, or consumer-breaking defects may block the affected DLM claim.

## Portable-suite invariants

- Resolve one target repository before reading or writing. Prefer the user-specified root, otherwise the nearest unambiguous Git root.
- Read repository `AGENTS.md` and existing `doc_llm/README.md` before changing structure.
- Keep every DLM artifact inside the repository-declared `doc_llm_root`; never copy another project's task state or manifests.
- Do not install or duplicate this personal skill under a repository `.agents/skills` folder. Repository-specific behavior belongs in `doc_llm/dlm.json`, repository docs, or repository-owned validation scripts.
- Personal skill files are workflow instructions, never entries in a repository `context_manifest`.
- Code, configuration, tests, and repeatable runtime evidence are implementation truth. DLM records stable boundaries, topology, decisions, traps, and task state.
- When the accepted target includes hardware-identity configuration behavior, preserve its real UI/consumer round-trip evidence: discovered candidates, stable selection/manual entry, visible echo, and persisted save/reload as applicable. Static bindings, documentation, or DLM health do not prove that behavior. DLM-only maintenance does not itself authorize hardware/UI implementation or a device run; keep framework-specific repair recipes in the relevant UI/machine skill or owning project knowledge.
- Preserve existing history. Prefer compatible, incremental migration over mass rewriting.
- Keep target state, evidence state, and coordination state separate. Sediment or index synchronization cannot prove an implementation outcome, and an implementation outcome does not automatically authorize DLM/release/Git mutations.

## Select an operating mode

| Mode | Use when | Default write boundary |
|---|---|---|
| `audit` | User asks whether DLM is healthy or portable | Read-only |
| `initialize` | Repository has no usable `doc_llm` | Requires explicit creation intent |
| `migrate` | Existing DLM needs a newer contract or isolation rules | Change only migration-owned files |
| `maintain` | Add a domain/module, repair routing, or harden validation | Incremental updates only |

Creating a full knowledge system, changing BRIEF meaning, redefining domains, or changing L0 constraints requires user approval. An already-authorized compatible migration or narrow repair does not require repeated stage-by-stage confirmation.

## Project contract

Prefer `doc_llm/dlm.json` as the repository contract. A portable minimum is:

```json
{
  "schema_version": "7.0",
  "project_id": "example",
  "project_name": "Example",
  "repository_root": ".",
  "doc_llm_root": "doc_llm",
  "manifest": {
    "version": 2,
    "path_base": "repository",
    "allow_absolute_paths": false,
    "allow_external_paths": false
  },
  "task_status": {
    "allowed": ["📋 待办", "🔄 进行中", "⛔ 阻塞", "🛑 已取消", "✅ 完成"]
  },
  "release": {
    "profile": "none",
    "commit_requires_explicit_user_intent": true,
    "push_requires_explicit_user_intent": true
  },
  "health_check": "build/verify-doc-llm.ps1"
}
```

Treat the five statuses as defaults only. If an established repository declares another compatible model, preserve it rather than silently rewriting history. `project_id` and path base are identity boundaries, not cosmetic metadata.

## Knowledge layers

| Layer | Owns | Must not become |
|---|---|---|
| BRIEF | Product/domain purpose, users, scenarios, terminology | Implementation manual |
| L0 | Stable must/must-not constraints | Design discussion or source dump |
| L1 | Topology and routing to domains/L2 | API catalog or implementation body |
| L2 | State machines, trade-offs, traps, evolution, source anchors | Git-log repetition |
| Task | Objective, dependencies, context manifest, evidence, execution log | Reusable architecture knowledge |

Document size is a review signal, not a universal correctness rule. Split content when ownership or loading needs differ; do not pad or truncate to satisfy arbitrary numbers.

## Workflow

1. **Discover once** — perform one combined repository/authority/write-scope safety check, then inspect the minimum source, tests, docs, boundaries, consumers, and health scripts needed for the requested DLM decision. Separate verified facts, inferences, and proposed structure.
2. **Propose and baseline** — describe the intended DLM state, real consumers, domains, global constraints, routes, migration compatibility, material risks, validation claims, exact Authorized Scope, and stop line in a Draft Acceptance Baseline. Obtain approval where the selected mode requires it; the Baseline Owner freezes the baseline once before initialization/migration/maintenance writes.
3. **Establish only needed layers** — create or repair `dlm.json`, README/load protocol, BRIEF, global L0/L1, domains, and Tasks only where the target or a real consumer requires them; do so in dependency order.
4. **Generate routes** — derive L1 routing from L2 front matter where practical. Use `scripts/sync_l1_route.py` with `--preview` before write.
5. **Harden tasks** — new task manifests use schema 2, repository-relative `/` paths, concrete files, explicit intent, and project identity. Absolute, parent-traversal, personal-skill, and external-repository paths are invalid unless the project contract explicitly permits a read-only external source outside the manifest.
6. **Validate claim-fit** — run repository health checks and the generic doctor when their contract/path claims matter to the requested DLM state:

```powershell
python -B -X utf8 <skill-dir>/scripts/dlm_doctor.py --repo-root <repo> --require-contract
```

7. **Audit the write boundary** — verify no unrelated project, user work, or external path was modified. This is a substantive safety check, not a formal independent audit. Do not commit unless separately authorized.

A validator failure blocks the DLM build/migration claim only when it violates the current accepted baseline, applicable contract, touched artifact integrity, or a demonstrated safety/consumer boundary. Report unrelated pre-existing or administrative failures separately. A green doctor proves only the contract/path properties it measures.

## Validator and migration behavior

- Validate schema-2 manifests as complete XML, including nesting, attributes, project identity and any supplied Epic/Subtask identity. Matching only an opening tag is not structural validation.
- Normalize CRLF/LF for parsing while preserving the file's original BOM and newline style on writes. Shared task parsing gives explicit `## Meta` precedence over legacy leading metadata; historical sections are never current state. Indexers prepare all selected outputs and input snapshots before writing, reject observed input/target changes, and replace each changed file through a same-directory temporary file. `--check` and `--preview` are read-only. This is not a multi-file transaction or a substitute for the existing single-writer/lease rule; if a later replacement fails, report partial progress and regenerate after resolving the cause.
- Regression evidence should cover current Meta versus historical entries, duplicate short task IDs, malformed XML, unsafe paths, idempotence, and no writes after an input error. Test custom statuses from the target contract rather than imposing a project's vocabulary on all repositories.
- Keep DLM 7 / schema 2 when compatible repairs suffice. New templates reference only layers that actually exist. Leave legacy manifests and accepted historical logs under the declared compatibility boundary; migrate them when a real consumer needs it.
- A user-named project without Git remains a valid DLM root. Record the absent Git state and use an exact file backup when the accepted change needs rollback; do not initialize Git as a side effect.

## Incremental maintenance

- New module: update or add the owning L2, then regenerate the L1 route.
- New domain: update contract-aware root routing, BRIEF/L0/L1/L2, and validation.
- New stable constraint: propose the exact L0 change and obtain approval.
- Protocol migration: declare the compatibility boundary and leave historical execution logs intact.
- Repository-specific release/build behavior: record it in the repository contract or owned scripts, not in this personal skill.

## Resources

- Use `templates/` only for the relevant layer; do not copy unused scaffolding.
- Use `scripts/sync_l1_route.py` for deterministic route compilation.
- Use `scripts/dlm_doctor.py` for portable contract and path validation. It does not verify AC outcomes, execute behavior checks, or certify dependency readiness.
- For optional evidence bindings, L2 dependencies and review triggers, read [Evidence and decisions](../_shared/references/evidence-and-decisions.md). These conventions extend existing Markdown only where useful; they do not require migrating old tasks or changing schema 2.

Final reporting must name the repository/project identity, operating mode, intended DLM state, changed paths, consumers served, compatibility boundary, validation claims/results, stopping condition, and remaining warnings. Stop when the requested state and material uncertainty are sufficiently resolved; do not add more governance merely because further cleanup is possible.

## Extended knowledge-base CLI (`scripts/dlm.py kb`)

Alongside `dlm_doctor.py` and `sync_l1_route.py`, use `python -X utf8 <skill-dir>/scripts/dlm.py kb` for lifecycle hygiene (see [l2_writeback_contracts.md](../_shared/references/l2_writeback_contracts.md) and [l2-audit-rubric.md](references/l2-audit-rubric.md)):

- `dlm.py kb stale [domain]`: compare `L2` `match_globs` and `last_updated` against Git source history to detect stale `L2` modules.
- `dlm.py kb map <target> [--json]`: audit `L2` documents for size bloat, changelog accumulation, layer leaks, and glob overlap.
- `dlm.py kb sediment [paths...]`: list candidate `L2` / `Reference` / `SOP` documents matching changed paths.
- `dlm.py kb scaffold ...`: scaffold project/domain `BRIEF`, `L0`, `L1`, `L2`, `Reference`, and `SOP` files from Chinese templates.
