---
name: dlm-version-master
description: Configure or operate content-hash-based versioned builds for .NET repositories with automatic internal version-bump decisions and mandatory exact-scope Git commit and remote push on every direct invocation. Use for version updates, Release builds, binary metadata verification, changelogs, or version-managed Git commit/push. Discover layouts and policies from each repository's contract.
---

# DLM Version Master 7 Portable

## Purpose

Version, verify, commit, and push .NET repository changes using repository-owned infrastructure without assuming a product name or directory layout. This personal skill provides the generic workflow; each repository declares its projects, release entry point, module map, output paths, and commit policy.

## Outcome-governance gate

Read and apply the shared [DLM Outcome Governance](../_shared/references/outcome-governance.md) before version-state mutation, Release build, artifact verification, staging, commit, or push.

- Establish one Frozen release/version baseline with the authorized scope, required modules/outputs, internal version decision, claim-matched evidence, and stop line. Direct invocation of `dlm-version-master` authorizes internal version evaluation, required build/verification, exact-scope Git commit, and push to the remote branch; it does not authorize artifact copy, publish, tag, deploy, or field rollout.
- A source hash supports the module-change/version-decision claim; an output hash supports byte identity when the profile consumes it. Neither freezes a baseline nor proves runtime, coordination, deployment, or field state.
- Run only profile-required or material-risk checks. Green metadata cannot substitute for behavior evidence, and unrelated administrative failures cannot silently become release criteria.
- Perform one combined identity/scope/pre-staged safety check before mutation, then advance the shortest release path. Do not add receipts, duplicate summaries, or repeated full verification without a real consumer or new material uncertainty.

## Authority and composition

- Every direct invocation of `dlm-version-master` carries standing user authorization to:
  1. decide autonomously via internal rules whether to bump versions (`none` vs. `patch` / `minor` / `major`) unless the user explicitly specifies a bump policy in the prompt;
  2. run the required Release build and binary metadata verification whenever module versions or build-relevant source inputs change;
  3. stage exact allowlisted paths, run required pre-commit reviews (`ponytail-review`), commit to Git with a detailed structured commit message covering **修改范围 (Scope), 对应版本 (Version), 怎么改的 (How), and 为什么改的 (Why)**, and push to the remote repository branch (`git push`).
- Skip commit or push on direct invocation only when the user explicitly instructs not to commit/push in the current turn, or when a concrete safety/verification gate blocks it (failed required build/test/review, mixed unrelated changes in a target file, missing/ambiguous remote, or diverged remote branch).
- Remote repository creation, force-push, tag, deploy, publish, and artifact copy remain separate authorities.
- In `dlm-close-release` composition mode, perform discovery, internal version decision, build, changelog, and metadata verification, then return exact changed paths without staging, committing, or pushing unless the owning orchestrator expressly delegates the shared Git phase.
- Do not copy this personal skill into the repository or reference it from a project context manifest.
- Keep engineering, release evidence, DLM coordination, Git, deployment, and field acceptance as separate states.

## Starting context

1. Resolve one Git root and read its `AGENTS.md`.
2. If the repository uses DLM, load `doc_llm/dlm.json` and the active release task.
3. Read `references/versioned-build-contract.md` and `references/git-sync.md`.
4. Inspect existing `.sln`, `.slnx`, executable/library/plugin `.csproj`, `Directory.Build.*`, repository version scripts, CI/release definitions, and version state before editing.
5. Prefer repository-owned version infrastructure. Create `build/versioning/` only when the user asks to establish versioning and no compatible mechanism exists.

## Resolve the repository profile

Use this order:

1. release/version profile declared in `doc_llm/dlm.json` or repository docs;
2. existing version/build script and version state;
3. user-specified project/solution;
4. unambiguous executable startup project or primary solution;
5. if still ambiguous, report candidates and ask before version mutation.

Do not embed a known product's paths in the personal skill. Project-specific behavior belongs in the repository contract or its scripts.

## Source-hash version decisions (autonomous internal rule)

Whether to bump a version and which bump level to apply are decided automatically by internal rules (unless the user explicitly overrides the level in the prompt). Hash project-owned source inputs, not output binaries.

Include as applicable:

- `.cs`, `.fs`, `.vb`, `.xaml`, `.axaml`;
- `.csproj`, `.fsproj`, `.vbproj`, `.props`, `.targets`;
- project-owned resources, manifests, package/project references, and code-generation inputs.

Exclude:

- `bin/`, `obj/`, `out/`, `publish/`, `artifacts/`, staging, and copied runtime output;
- generated version props, changelogs, and release notes;
- version state itself when computing a module's source hash;
- `.pdb`, `.deps.json`, generated DLL/EXE/package outputs.

Internal decision table:

- **No bump (`none`)**: An unchanged module source-input hash never bumps. If only non-module files (such as docs, DLM records, or repository scripts outside module hash inputs) changed, or if no module source inputs changed since the recorded hash, do not bump versions and do not create an empty version mutation; proceed directly to the Git commit and remote push phase for the actual allowlisted changes in scope.
- **Automatic bump when module source-input hash changed**: Inspect the semantic impact of the module diff and repository rules to select the level automatically without stopping to ask:
  - `major` / `A`: breaking public API, persisted format, plugin discovery, execution, authorization, or deployment contract;
  - `minor` / `B`: backward-compatible feature, new module/plugin/tool, or capability addition;
  - `patch` / `C`: backward-compatible bug fix, layout/accessibility/localization correction, refactoring, performance tuning, logging, or internal maintenance;
  - `auto`: repository-declared default when configured, otherwise evaluate via the `major` / `minor` / `patch` rules above (defaulting to `patch`).

## Binary metadata

For SDK-style projects, ensure public version values flow into generated outputs:

```xml
<Version>1.2.3</Version>
<AssemblyVersion>1.2.3.0</AssemblyVersion>
<FileVersion>1.2.3.0</FileVersion>
<InformationalVersion>1.2.3</InformationalVersion>
<IncludeSourceRevisionInInformationalVersion>false</IncludeSourceRevisionInInformationalVersion>
```

Do not place branch, commit SHA, remote URL, author/email, commit message, machine path, or repository path in public binary version fields. Git provenance belongs in Git/CI/release logs.

## Build and verify

When internal rules bump one or more modules (or when build-relevant module inputs changed), use the repository script when present; otherwise build the selected scope serially:

```powershell
dotnet build <project-or-solution> -c Release -m:1
```

Do not force-delete locked output. Report the locking process and stop unless the user authorizes a safe process shutdown.

After build, validate only the claims required by the Frozen release baseline and repository profile:

1. run affected tests and repository release checks;
2. verify at least one output for every changed public module;
3. read file/product/assembly/informational version through appropriate tooling;
4. verify expected output path and, where required, SHA-256/package metadata;
5. ensure unchanged modules did not bump;
6. generate the repository's concise changelog/release summary when the release profile or a real release/decision consumer requires it.

If required metadata, tests, hashing, or output identity cannot be verified, the corresponding release claim is incomplete and blocks the Git commit/push phase. Report unrelated pre-existing or administrative failures separately; they do not invalidate a compliant output unless material impact is demonstrated.

## Dual-Fingerprint Build Manifest & Dedicated Binary Archive Repository

To prevent source repository bloat while keeping full historical binary rollback and "About" dialog introspection (Managed + C++ Native Engine):

1. **Build Manifest (`build/versioning/generated/build-manifest.json`)**:
   - Generate or refresh `build-manifest.json` via `scripts/dlm_version_master.py manifest` after version evaluation or build verification.
   - Each module entry records: `module`, `displayName`, `description`, `category` (`Core & Workbench`, `Native Engine`, `Plugins`, `VTools`, `Canvas`), `kind` (`managed` / `native`), `artifact` filename, `version` (`A.B.C`), `builtAt`, `sourceRevision` (short hash `abc...def0`), `isDirty` (boolean flagging local working-tree modifications), `buildId` (`408...5a54`), `outputSha256`, and `compatibilityPolicy` (e.g., `buildInfoApi=1, abiPolicy=major-minor` or `semver=major-minor`).
   - Supports one-click UI inspection, "Copy All", and diagnostic export without embedding private machine paths or emails inside public PE binary headers.

2. **Dedicated Binary History Archive Repository (`release.binary_archive_repo`)**:
   - Never store compiled `.dll`, `.exe`, `.pdb`, or large binary outputs inside the primary source repository.
   - When `release.binary_archive_repo` is configured in `doc_llm/dlm.json` (or `version-rules.json`), invoke `scripts/dlm_version_master.py archive` after verifying build outputs to copy verified binaries + `build-manifest.json` + `versions.json` into the dedicated Binary Archive repository and record a matching 4-part structured log.

## Mandatory Git commit and remote push phase

Follow [Git synchronization](references/git-sync.md) on every direct invocation of `dlm-version-master` (unless explicitly suppressed by the user or running as a composed child without Git delegation):

1. Execute the internal version decision -> verified build (when bumped or build-relevant inputs changed) -> pre-commit review (`ponytail-review` and repository hooks) -> exact-scope `git commit` -> `git push` to the remote branch.
2. Every commit created by `dlm-version-master` must use a detailed structured multi-line commit message grounded in the actual `git diff --cached` and version transitions (never a one-line summary or vague "bump version" / "update files"). It must explicitly include all four required sections:
   - **修改范围 (Scope)**: changed modules/projects/subsystems and key allowlisted files or boundaries;
   - **对应版本 (Version)**: bump level (`none` / `patch` / `minor` / `major`) and each affected module's `old -> new` version transition (or current version with `none (sourceHash unchanged)` when no module bumped);
   - **怎么改的 (How)**: concrete technical implementation derived from the staged diff (entry points, data/control flow, algorithm/UI/config/build adjustments);
   - **为什么改的 (Why)**: root cause, requirement/task driver, defect trigger, or architectural/compatibility reason for both the code change and the version decision.
3. When internal rules decide **not** to bump versions (unchanged module source hashes), skip version mutation and do not create an empty version commit; still stage, review, commit (with the same four-part structured commit message), and push any intended allowlisted repository changes in scope, or push existing unpushed verified commits on the current branch.

## Output

Report repository profile source, Frozen release baseline/stop line, internal version decision (`none` / `patch` / `minor` / `major`) and rationale, build scope and commands (when executed), module hash/version transitions, unchanged modules, claim-matched tests, verified output metadata/hashes, changelog consumer/path, changed-file allowlist, full structured commit message (修改范围 / 对应版本 / 怎么改的 / 为什么改的), commit hash, verified remote branch push result, and Blocking versus Advisory gaps. Keep higher evidence levels distinct from build and Git synchronization success.
