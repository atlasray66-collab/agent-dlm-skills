# Git synchronization (mandatory on direct invocation)

## Standing invocation authority and repository settings

Every direct invocation of `dlm-version-master` carries standing user authorization to perform an exact-scope Git commit and push to the remote branch (`git push`) after the internal version decision and any required build/metadata verification pass. Do not stop to ask for extra commit/push confirmation unless the user explicitly restricted Git actions in the current prompt or a safety check fails.

Resolve the current Git root before reading its own `doc_llm/dlm.json`. Do not borrow a parent, nested, or adjacent repository's policy. When present, the optional `release.git_sync` object provides repository-specific remote/branch constraints:

| Field | Meaning |
| --- | --- |
| `enabled` | Boolean; records repository-level default for orchestrators such as `dlm-close-release`. Direct `dlm-version-master` invocation always enables commit and push unless the user says otherwise. |
| `remote` | Exact Git remote name (defaults to the current branch's tracking remote or `origin` when absent). |
| `url` | Optional credential-free clone URL expected for the remote repository. |
| `allowed_branches` | Optional list of exact local branch names authorized for synchronization; when configured, verify the current branch is listed. |
| `commit_after_verified_build` | Boolean; active by default on direct `dlm-version-master` invocation. |
| `push_after_commit` | Boolean; active by default on direct `dlm-version-master` invocation. |
| `standing_authorization.approved_on` | Optional date record in `YYYY-MM-DD` form. |
| `standing_authorization.scope` | Optional plain-language record of repository/branch/file scope limits. |

Require a named branch (not detached `HEAD`), compliance with `allowed_branches` if configured in `doc_llm/dlm.json`, and an unambiguous remote destination. Missing remote or contradictory policy blocks only the dependent Git action; retain completed build evidence. Commit and push remain separate from tag, release publication, deployment, and artifact copy.

## Initial remote onboarding

1. Inspect existing remotes without exposing credentials. Reuse the intended existing remote after checking its fetch and effective push destinations. Do not overwrite a remote, change repository visibility, or silently redirect pushes when it differs from a declared `release.git_sync.url`.
2. If the remote is absent, first check whether the approved remote repository already exists. Attach it only within the authorized onboarding scope. A name collision or ambiguous access error is not permission to create another repository.
3. Create a remote repository only when the user has authorized the host, namespace/owner, exact repository name, and private visibility in this session or a standing policy. Confirm the authenticated identity can use that namespace. Create it empty, without a generated README/license/ignore commit, then use its returned credential-free clone URL. If any identity or scope is missing, stop before creation and request only that missing decision.
4. Use available authenticated connectors, Git credential helpers, or session-scoped credentials. Never persist credentials in profile files, clone URLs, scripts, reports, logs, or command-line arguments. Never print credential-bearing remote configuration or authentication responses. If no suitable authentication path exists, report the blocker.
5. Check remote history before the first push. Preserve nonempty history; do not force-push, rewrite history, or merge/rebase merely to make onboarding succeed without authorization for that action.

Use existing tools; this workflow does not require a new executable, server, or dependency. Repository creation is one-time onboarding, not a step to repeat on each versioned build.

## Internal version decision -> verified build -> exact-scope commit -> push

1. Preserve the initial status, diff, and pre-staged set. Identify an exact repository-relative file allowlist for this task's source, version infrastructure/state (if bumped), and intended changelog. Exclude secrets, local configuration, outputs, logs, captures, temporary files, and unrelated work. If a file mixes unrelated changes, stop before staging that file until the intended scope can be isolated. Never use `git add .` or a broad directory wildcard.
2. Complete the internal version decision (`none` / `patch` / `minor` / `major`). When a version bump occurs or build-relevant module inputs changed, complete the required build, tests, and output metadata verification before Git mutation. Any required build/verification failure stops staging, commit, and push; preserve the failure evidence and worktree without rolling back unrelated changes. An unchanged module source hash never bumps: skip version mutation, do not create an empty version commit, and continue to step 3 if allowlisted changes remain to be committed (or skip to step 6 if all intended changes are already committed locally and only need to be pushed).
3. Run the globally required pre-commit/pre-push review (the `ponytail-review` gate in the global AGENTS.md) and any repository-required reviews and hooks against the actual current diff/outbound changes; if a required review skill or hook is unavailable, stop the dependent Git action and report the gap. Address each finding or record the explicitly retained reason as the repository requires. Mark a review complete only after actually performing it; do not bypass a hook, fabricate review evidence, or automatically certify a review because the build passed.
4. Stage exact allowlisted paths only when the pre-staged set contains no unrelated work; otherwise leave that index intact and resolve the conflict with the owner. Verify exact equality between intended changed paths and staged paths, including deletions/renames, and inspect staged content. Run `git diff --cached --check` and applicable repository encoding checks. Reconfirm no build-relevant source/version inputs changed since verification; changed inputs require the affected verification again before commit. A path allowlist alone does not prove content ownership.
5. Commit with a detailed structured multi-line commit message grounded in the actual `git diff --cached` and version state (see **Structured commit message specification** below). Single-line commits or vague summaries such as `chore: bump version` / `update files` are forbidden. Verify the resulting commit's file set, content, and structured message match the intended diff and version transitions. Leave unrelated work untouched. Capture the commit ID independently of build and release evidence.
6. Before pushing to the remote, verify the remote destination, target branch, current remote tip, and every commit that will become reachable on the remote. Prior local commits are part of the outgoing scope; do not publish unapproved history just because the newest commit is allowlisted. Stop if the remote has diverged or the destination changed. Run any push-specific required review/hook against the final outbound changes. Push only the intended branch/ref (`git push <remote> <branch>`), without force or automatic tags, then verify the remote branch tip equals the intended commit.

If commit succeeds but push fails, preserve the local commit and report the commit ID plus the concrete push error. Retry only the failed Git phase after its blocker is resolved; do not repeat the version bump or create a duplicate commit. If an uncertain push result may already have succeeded, query the remote tip before retrying.

Composition mode returns the exact changed paths after verified build. When `dlm-version-master` runs as a composed child inside `dlm-close-release`, the owning orchestrator controls when this shared Git phase runs.

## Structured commit message specification (mandatory)

Before running `git commit`, inspect `git diff --cached --stat` and `git diff --cached` for every staged file. Every commit message generated by `dlm-version-master` must be written in clear, direct Chinese technical prose with a Conventional Commit header and four mandatory body sections (**修改范围**, **对应版本**, **怎么改的**, **为什么改的**):

```text
<type>(<scope>): <一句话总结核心改动与版本动作，不超过 50 字>

修改范围：
- 模块/项目：<涉及的模块、项目或子系统名称>
- 关键文件：<本次精确纳入提交的核心相对路径或边界说明>

对应版本：
- 版本决策：<patch | minor | major | none>（<触发或跳过升版的原因，如 sourceHash 变更及语义级别 / sourceHash 未变更>）
- 模块版本：<ModuleA: 1.2.3 -> 1.2.4；ModuleB: 2.0.0（未变更）；若未升版则写 ModuleA: 1.2.3（none，源码哈希未变）>

怎么改的：
- <基于真实 staged diff 提炼的具体实现变更 1：指明入口、类/方法、数据结构、配置或构建脚本怎么调整>
- <基于真实 staged diff 提炼的具体实现变更 2：同步更新的版本状态文件、MSBuild 版本属性或变更日志>

为什么改的：
- <说明本次修改的直接动因：修复的具体缺陷根因、业务/任务需求、兼容性约束或架构收敛目标，以及选择该版本级别的依据>
```

Rules for drafting the commit message:

1. **`<type>` selection**: Use `feat` (new capability / minor bump), `fix` (bug fix / patch bump), `refactor`, `perf`, `docs`, `build`, `chore`, or `release` matching the primary staged change.
2. **Real diff grounding**: Derive **怎么改的** and **为什么改的** from the actual staged code/config diff and task context, not from filenames alone. Do not write filler or generic boilerplate.
3. **Complete version mapping**: Always fill **对应版本** whether versions bumped or not. When multiple modules are in scope, list each changed module's `old -> new` transition explicitly and note unchanged modules when relevant.
4. **Multi-line safe invocation**: Pass the multi-line message via `git commit -F <temp-msg-file>` (UTF-8 without BOM, deleted immediately after commit) or multiple `-m` paragraphs so PowerShell quoting never mangles newlines or Chinese characters.
5. **Post-commit verification**: Run `git log -1 --format=%B` after committing to confirm the recorded commit message is intact and contains all four sections.

