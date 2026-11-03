# Portable Versioned Build Contract

## Repository-owned profile

The personal skill does not contain product-specific paths. Resolve versioning from repository-owned sources in this order:

1. `doc_llm/dlm.json` release/version profile;
2. repository release/version documentation;
3. existing scripts and version state;
4. user-specified project/solution;
5. generic .NET discovery.

A repository profile should declare or make discoverable:

- startup/primary build entry;
- module-to-project mapping;
- module-to-output mapping;
- version state and hash rules;
- version/build command;
- tests and metadata checks;
- generated changelog/release-note paths;
- commit and artifact policy.

## Generic target files

For repositories without compatible infrastructure, a conventional layout is:

```text
build/versioning/
  versioned-build.ps1
  prepare_versions.py
  generate_changelog.py
  versions.json
  version-rules.json

Directory.Build.props
Directory.Build.targets
```

Use an established repository location instead of creating a parallel system.

## Version state

`versions.json` may serve as the module version/hash SSOT:

```json
{
  "schema": 1,
  "modules": {
    "MyApp": {
      "project": "src/MyApp/MyApp.csproj",
      "output": "artifacts/MyApp.exe",
      "version": "1.0.0",
      "sourceHash": "",
      "lastChangedUtc": ""
    }
  }
}
```

Paths are repository-relative and portable. Do not record local machine paths.

## Bump policy (autonomous internal decision)

Use `A.B.C` and decide automatically via internal rules whether to bump and which level applies (unless the user explicitly overrides):

- `none`: module source-input hash is unchanged -> never bump;
- `major` / `A`: breaking public, persisted-data, plugin, execution, authorization, or deployment contract;
- `minor` / `B`: backward-compatible capability, module, plugin, or feature addition;
- `patch` / `C`: backward-compatible fix, UI/localization adjustment, refactoring, or maintenance;
- `auto`: repository default when configured, otherwise evaluate `major` / `minor` / `patch` from the module diff (defaulting to `patch`).

An unchanged source hash never bumps. When the source hash changed, evaluate `major` / `minor` / `patch` directly from the diff and repository contract without stopping to ask the user.

The source hash answers only whether declared module inputs changed. It is not an Acceptance Baseline state, semantic identity for the entire repository, or runtime proof.

## Hash inputs

Hash project-owned source, project files, build props/targets, package/project references, manifests, resources, and code-generation inputs.

Exclude outputs and self-triggering generated state:

```text
bin/
obj/
out/
publish/
artifacts/
staging/
versions.json
generated version props
generated changelog/release notes
```

Output DLL/EXE/package hashes are evidence after build, not inputs to source-version decisions.

## MSBuild metadata

Generated version properties must be imported before assembly info generation:

```xml
<Version>1.0.0</Version>
<AssemblyVersion>1.0.0.0</AssemblyVersion>
<FileVersion>1.0.0.0</FileVersion>
<InformationalVersion>1.0.0</InformationalVersion>
<IncludeSourceRevisionInInformationalVersion>false</IncludeSourceRevisionInInformationalVersion>
```

Public binary fields must not expose branch, SHA, remote, author/email, commit text, machine path, or repository path.

## Build contract

Prefer a repository-owned script such as:

```powershell
./build/versioning/versioned-build.ps1 `
  -Project src/MyApp/MyApp.csproj `
  -Configuration Release `
  -Bump patch `
  -Reason "Fix public output metadata"
```

If no script exists and setup was not requested, do not pretend ordinary `dotnet build` provides content-hash versioning.

## Commit and push contract

Every direct invocation of `dlm-version-master` authorizes and requires exact-scope Git commit and push to the remote branch after the internal version decision and any required build/test and public metadata verification pass. Stage exact repository-relative allowlisted paths only:

- intentional source/versioning infrastructure;
- version state (when bumped);
- generated changelog/release notes intended for Git.

Never stage unrelated work, secrets, local configuration, build outputs, logs, captures, or temporary files. Tag/deploy/publish/artifact-copy remain separately authorized. Commit messages must follow the four-part structured format in [Git synchronization](git-sync.md) (**修改范围**, **对应版本**, **怎么改的**, **为什么改的**). Remote verification, review gates, and initial remote onboarding also follow [Git synchronization](git-sync.md). When the module source hash is unchanged, do not bump versions or create an empty version commit; commit and push only the actual allowlisted changes in scope with the same four-part structured commit message (or push unpushed verified commits).

## Verification

For every changed public module, verify the expected output identity and version metadata. For Windows .NET binaries, one available check is:

```powershell
(Get-Item <output>).VersionInfo.FileVersion
(Get-Item <output>).VersionInfo.ProductVersion
```

Also run repository tests and hash/package checks declared by the profile or required by a demonstrated material output risk. Missing or mismatched required metadata blocks the affected release claim and prevents Git commit/push. Unrelated pre-existing checks, administrative records, and reviewer preferences do not silently expand the Frozen release criteria.

## Dual-Fingerprint Build Manifest & Binary Archive Contract

- Generate `build/versioning/generated/build-manifest.json` via `scripts/dlm_version_master.py manifest` so both Managed (`.csproj`) and C++ Native (`CMakeLists.txt`) modules expose unified `version`, `sourceRevision`, `isDirty`, `buildId`, `builtAt`, `outputSha256`, and `compatibilityPolicy` fields.
- Keep compiled `.dll`/`.exe`/`.pdb` history in a dedicated Binary Archive repository (`release.binary_archive_repo` in `doc_llm/dlm.json`) synchronized via `scripts/dlm_version_master.py archive`.
