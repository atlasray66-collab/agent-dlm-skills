# DLM Plan 7 Validation and Tooling

## Required Checks

- The plan identifies one intended outcome, Draft/Frozen baseline state, Baseline Owner, Authorized Scope, acceptance criteria, claim-matched evidence, and stop line when it is execution-ready.
- Every material action is target work or substantive assurance with a causal link; administrative records are marked nonblocking unless a real consumer or accepted contract requires them.
- Every new Subtask has Meta, goal, schema-2 `context_manifest`, plan, checkpoints and execution log.
- `project` matches `doc_llm/dlm.json`.
- Manifest paths are repository-relative concrete files; no absolute paths, traversal, directories or external roots.
- Every entry has `required`; `defer=true` implies `required=false`.
- Dependencies are acyclic and statuses are contract-valid.
- Backlog, Epic README and Subtask SSOT are consistent.

## Commands

```powershell
python -B -X utf8 <skill-dir>/scripts/sync_epic_index.py <epic-dir> --repo-root <repo>
python -B -X utf8 <dlm-build-dir>/scripts/dlm_doctor.py --repo-root <repo> --require-contract
```

Indexers share current-Meta parsing, prepare all selected changes, check for observed source/target changes and replace each output atomically. Keep the existing single-writer discipline: snapshot comparisons are not a lock or an atomic compare-and-swap, and a multi-file batch is not a transaction. On an I/O failure, report any completed writes rather than claiming the whole batch rolled back. The generic doctor checks contract/path structure; task dependency acyclicity and actual AC outcomes still need their appropriate checks.

Use `--preview` before index writes in a dirty worktree. Run the repository-specific health check as authoritative contract evidence for the rules it actually measures.

A nonzero result blocks a successful materialization claim only when it violates the current/Frozen baseline, applicable contract, touched artifact integrity, or a demonstrated material safety boundary. Classify unrelated pre-existing and administrative failures separately instead of turning them into new acceptance criteria. A green check cannot stand in for runtime, product, release, or field evidence.
