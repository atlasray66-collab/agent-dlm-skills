---
name: multi-llm-lease
description: 为可并行、可多重入的任务场景接入 claim/lease 执行模型（Gemini 4 分级适配 + Codex 多对话并行开发 + 自动触发 $dlm-reflect 验证与 $dlm-sediment 证据写回）。Use when 用户希望多个 Codex 独立对话并行消费共享任务清单、避免撞单、支持同一 worker 多重入、在每次新任务开启前打印 `S001 1/58 3D平面拟合导入` 进度标识，并在子任务完成后自动调用 `$dlm-reflect` 验证与 `$dlm-sediment` 写回证据。
---

# multi-llm-lease

> **用途**: 把“共享任务清单 + claim/lease + heartbeat + 超时回收 + Gemini 4 任务分级 + Codex 独立新对话并行分发 + `$dlm-reflect` 验证 + `$dlm-sediment` 证据写回”稳定接入可并行工程场景。

## 定位

这个 skill 分成三层:

1. **通用 Lease 核心**
   - lease 状态机: `claim -> heartbeat -> complete -> refresh`
   - claim 校验契约: `resolved_worker`、`claim_file`、`claim_verified`
   - 可重入语义: 同一 `worker` 重入时返回原任务
   - 进度与横幅契约: 自动计算队列全局进度并输出 `task_banner`（如 `S001 1/58 3D平面拟合导入`）
   - 显式配置: `worker_env_var`、`column_map`（含 `title`/`tier` 列映射）、`note_messages`
2. **Gemini 4 任务分级适配层**
   - 主力模型家族切换为 `Gemini4`，按子任务复杂度分级 (`D0` / `D1` / `D2` / `D3`) 自动匹配模型档位、思考深度与推荐并发会话数:
     - `D0`（机械/脚手架/样板同步）: `gemini-4-flash` (`thinking=low`, 推荐并发 `6`)
     - `D1`（常规独立算子/模块导入与单测闭环）: `gemini-4-pro` (`thinking=medium`, 推荐并发 `4`)
     - `D2`（跨模块契约/复杂3D算法/高风险状态机）: `gemini-4-thinking` (`thinking=high`, 推荐并发 `2`)
     - `D3`（架构级改造/安全边界/底座重构）: `gemini-4-ultra` (`thinking=high`, 推荐并发 `1`)
   - 支持从任务表 `分级` 列精确读取，或在未提供分级列时按任务描述保守推断（默认 `D1`），也支持在 `work_item_runtime.json` 的 `tier_profiles` 中覆盖。
3. **Codex 多对话并行与 Reflect/Sediment 自动闭环层**
   - **默认采用多对话并行 (`codex_new_thread`)，替代多子代理 (subagents)**: 多子代理容易割裂代码与 DLM 上下文联系；每个独立子任务统一通过 Codex `create_thread` 创建独立新对话执行，并在主会话通过 `wait_threads` 跟踪。
   - **新任务开场强制任务横幅**: 每次新任务开启前及新对话首行必须指明当前任务与全局进度，格式固定为：
     `S001 1/58 3D平面拟合导入`（外加 `总任务 58 项 | 已完成 2 项 | 进行中 1 项 | 待开发 55 项 | 阻塞 0 项`），让用户一眼看清共有多少任务、当前是第几个、已完成多少。
   - **子任务完成后自动验证与沉淀闭环**:
     1. 子任务开发与自测完成后，**自动调用 `[$dlm-reflect]`** 对照验收契约进行 Closure Review 验证；
     2. `[$dlm-reflect]` 验证通过后，**自动调用 `[$dlm-sediment]`** 将验证证据、关键结论与陷阱写回仓库 `doc_llm` 文档体系；
     3. 证据写回完成后，调用 `complete_work_item.py --status done` 释放锁并更新完成计数。

## 铁律红线（强制新对话并行 & 唯一同名 Skill）

1. **全系统仅保留唯一一个 `multi-llm-lease` Skill**:
   - 唯一权威路径固定为 `<codex-home>/skills/multi-llm-lease/SKILL.md`。
   - **严禁**在任何仓库 `.agents/skills/multi-llm-lease/` 或其他技能根目录下创建/保留重复的 `SKILL.md`、`SELF-DESCRIPTION.md` 或 `agents/openai.yaml`（若历史命令引用 `.agents/skills/multi-llm-lease/scripts/*.py`，仅允许保留无 `SKILL.md` 的脚本目录，确保技能列表中永远只有一个 `multi-llm-lease`）。
2. **并行任务必须且只能通过创建独立 Codex 新对话执行，绝对禁止使用子代理 (`multi_agent_v1` / `spawn_agent`)**:
   - 任何并行开发子任务**严禁**调用 `multi_agent_v1` / `spawn_agent` 子代理执行。
   - 若宿主环境直接调用 `mcp__codex_app` 返回不可用，**严禁**以此为借口退回子代理或单对话串行！必须使用本 skill 内置的命名管道桥接器 `scripts/codex_thread_bridge.mjs`（通过 Node 连接当前进程环境变量 `process.env.CODEX_APP_TOOLS_PIPE_PATH`，需带 `sandbox_permissions: "require_escalated"`）直接调用 Codex Desktop 宿主的 `create_thread`、`send_message_to_thread` 与 `wait_threads`。
3. **`create_thread` + `send_message_to_thread` 双步必达机制（Gemini 4 防停滞经验）**:
   - Codex Desktop 在 `create_thread` 时会将初始 `prompt` 封装在 `<codex_delegation><input>...</input></codex_delegation>` 的孤立 `function_call_output` 中，而 `gemini-4-argon-*` 模型会忽略无配对 `function_call` 的孤立 `function_call_output`，导致新对话首轮仅看到 `AGENTS.md` 并回复 `I am ready...` 后立即结束首轮。
   - 因此，使用 `scripts/codex_thread_bridge.mjs create-and-send <payload.json>` 创建新对话时，桥接器会在 `create_thread` 返回 `threadId` 并完成首轮初始化后，自动追加一次 `send_message_to_thread` 将完整任务指令作为真实跟进消息推入新对话，确保新对话 100% 启动实质开发。
   - 主对话在创建新对话后，必须在最终回复中逐行输出 `::created-thread{threadId="..."}`。

## 并行拓扑选择（默认多对话并行）

1. **Codex 独立新对话并行 (`codex_new_thread`，默认主力方式)**
   - 适合多任务并行开发，每个子任务拥有完整独立的上下文窗口，自行加载仓库、DLM、技能与局部源码，彻底避免多子代理上下文断层。
   - 协调器先运行 `prepare_codex_thread_dispatch.py`（或 `claim_next_work_item.py`）原子领取明确 work item，拿到 `task_banner`（如 `S001 1/58 3D平面拟合导入`）、`progress`、`gemini4_routing` 和 `new_thread_dispatch`。
   - 协调器先向用户播报当前任务横幅与完成进度，再调用 `create_thread` 创建新对话，并在最后输出 `::created-thread{threadId="..."}`。
2. **当前会话顺序执行 (`inline`)**
   - 适合单步调试、强耦合前置底座任务或仅剩 1 个收尾任务的场景。
   - 同样必须在开启前打印 `task_banner`（如 `S001 1/58 3D平面拟合导入`），并在完成后依次执行 `$dlm-reflect` 与 `$dlm-sediment`。

> **严禁把核心开发子任务拆给多子代理 (multi-agent subagents)**: 子代理缺少完整长程上下文联系，除非是纯只读检索，否则并行开发一律走 Codex 新对话 (`create_thread`)。

本地文件 lease 要求所有对话看到同一个 `work_items.md` 和同一个 `claims_dir`：
- 让新对话运行在同一个本地仓库目录，并严格按子任务拆分允许写入的文件范围；
- 若必须使用不同 worktree，需将 `work_items_path` / `claims_dir` 指向共享外部协调目录。

## 每次新任务开启前的标准播报格式

无论是协调器分发新对话，还是新对话开场第一行，都必须展示以下信息：

```text
【当前任务】S001 1/58 3D平面拟合导入
【全局进度】总任务 58 项 | 已完成 2 项 | 进行中 1 项 | 待开发 55 项 | 阻塞 0 项
【模型与分级】Gemini4 | 分级 D2 (跨模块契约/复杂算法/高风险状态机) | 推荐模型 `gemini-4-thinking` (thinking=high)
【租约校验】worker=codex-thread-S001 | claim_verified=true
```

## 子任务完成后的自动闭环流水线 (`Reflect -> Sediment -> Complete`)

每个子任务在完成代码实现与定向自测后，不得直接标记完成，必须按顺序执行：

1. **阶段 A：自动调用 `[$dlm-reflect]` 独立验证**
   - 对照该子任务的验收契约（Frozen AC / 目标与边界），构造至少一个直接反例或边界检查，核验实现、测试与回归输出是否真实闭环。
   - 若验证未通过，立即在当前对话内修复并重跑验证；若遇真实外部阻塞，转入 `--status blocked`。
2. **阶段 B：自动调用 `[$dlm-sediment]` 写回验证证据**
   - 在 `[$dlm-reflect]` 验证通过后，立即调用 `[$dlm-sediment]` 将已验证的证据路径、命令结果、关键设计决策与陷阱同步写回仓库 `doc_llm`（如任务表证据列、Subtask/Epic 进展或 L1/L2 文档）。
3. **阶段 C：释放租约并结项**
   - 运行 `complete_work_item.py --config <runtime.json> --worker <worker_id> --item-id <id> --status done --note "reflect+sediment verified: <evidence_path>"`。

## 最小工作流

1. 先读 [references/integration-snippets.md](references/integration-snippets.md)。
2. 运行 `refresh_work_items.py` 刷新超时锁并获取当前队列全局进度（`progress.summary_cn`）。
3. 运行 `prepare_codex_thread_dispatch.py` 领取下一个子任务并生成新对话载荷：
   ```powershell
   python -B -X utf8 scripts/prepare_codex_thread_dispatch.py `
     --config path/to/work_item_runtime.json `
     --item-id S001 `
     --worker codex-thread-S001
   ```
4. 核对返回的 `task_banner`（如 `S001 1/58 3D平面拟合导入`）、`progress`、`gemini4_routing`、`claim_verified=true` 与 `new_thread_dispatch.starter_prompt`。
5. 调用 Codex `create_thread` 工具创建独立新对话，将 `new_thread_dispatch.starter_prompt` 作为新对话初始提示词，并通过 `wait_threads` 监控完成状态。
6. 需要生成项目接入文档与配置模板时，运行 [scripts/render_lease_snippets.py](scripts/render_lease_snippets.py)。


### Codex Desktop 侧边栏项目列表可见性同步（防 `source='exec'` 过滤）

- **根因**：通过 `codex.exe exec` 启动后台独立新对话时，rollout jsonl 首行 `session_meta.payload.source` 与 `~/.codex/state_5.sqlite` 的 `threads.source` 默认被写为 `'exec'`；而 Codex Desktop（`app.asar` 的 `gh(e)` 目录扫描函数）硬编码了 `if (n == null || n.kind === 'exec' || !Number.isFinite(e.updatedAt)) return null;`，会将 `source='exec'` 的会话从 `~/.codex/sqlite/codex-dev.db` 的 `local_thread_catalog` 表中过滤掉，导致项目侧边栏无法展示新对话且 `move_thread_to_project` 报 `"The task's source project could not be safely determined."`。
- **强制同步步骤**：每次通过 `codex.exe exec` 启动或完成独立新对话时，必须同步执行以下 4 步使新对话在项目侧边栏立即可见：
  1. 将 `~/.codex/sessions/YYYY/MM/DD/rollout-*<threadId>.jsonl` 首行 `session_meta` 中的 `"source":"exec"` 替换为 `"source":"vscode"`；
  2. 将 `~/.codex/state_5.sqlite` 的 `threads` 表对应行更新为 `source='vscode', thread_source='user', name=<title>, title=<title>`；
  3. 向 `~/.codex/sqlite/codex-dev.db` 的 `local_thread_catalog` 表执行 `INSERT ... ON CONFLICT(host_id, thread_id) DO UPDATE`（设置 `source_kind='vscode', thread_source='user', display_title=<title>, missing_candidate=0`）并递增 `local_thread_catalog_metadata.catalog_revision`；
  4. 通过 `CODEX_APP_TOOLS_PIPE_PATH` 调用 `set_thread_title` / `move_thread_to_project` 触发 Electron 侧边栏刷新，并在主对话最终回复中输出 `::created-thread{threadId="..."}`。

## 重试终态任务

默认 `claim_next_work_item.py` 会跳过 `✅` 和 `❌` 终态。若需重做某个终态任务，先使用 `scripts/reopen_work_item.py` 将指定 `--item-id` 重开为 `⬜`，再走正常 claim/lease。

## 强约束

- `work_items.md` 只做展示层，活跃占用状态的唯一事实源在 `claims/*.json`。
- 每次开启新任务前必须明确指出当前任务横幅（如 `S001 1/58 3D平面拟合导入`）以及总任务数与当前已完成数。
- 每次子任务完成后必须经过 `$dlm-reflect` 验证 -> `$dlm-sediment` 写回验证证据 -> `complete_work_item.py` 结项。
- runtime 脚本支持并返回:
  - `task_banner`（如 `S001 1/58 3D平面拟合导入`）
  - `progress`（`item_index`、`total_count`、`position_fraction`、`completed_count`、`active_count`、`open_count`、`blocked_count`、`summary_cn`）
  - `gemini4_routing`（`tier`、`model`、`thinking_level`、`max_parallel_threads`）
  - `new_thread_dispatch`（`thread_title`、`starter_prompt`、`post_task_pipeline`）
  - `resolved_worker`、`claim_file`、`claim_file_exists`、`claim_verified`
- 回归测试：`python -B -X utf8 -m unittest discover -s tests`（在本 skill 目录运行）。

## 资源

- 文案与协议模板: [references/integration-snippets.md](references/integration-snippets.md)
- runtime 脚本:
  - [scripts/prepare_codex_thread_dispatch.py](scripts/prepare_codex_thread_dispatch.py)
  - [scripts/claim_next_work_item.py](scripts/claim_next_work_item.py)
  - [scripts/heartbeat_work_item.py](scripts/heartbeat_work_item.py)
  - [scripts/complete_work_item.py](scripts/complete_work_item.py)
  - [scripts/reopen_work_item.py](scripts/reopen_work_item.py)
  - [scripts/refresh_work_items.py](scripts/refresh_work_items.py)
  - [scripts/work_item_lease_lib.py](scripts/work_item_lease_lib.py)
- 模板生成脚本: [scripts/render_lease_snippets.py](scripts/render_lease_snippets.py)
- 回归测试: [tests/test_lease_lib.py](tests/test_lease_lib.py)

5. **一键同步脚本（含 `app.asar` 白名单动态识别与 IPC 重试兜底）**：
   可直接执行 `python -X utf8 <skill-dir>/scripts/sync_codex_sidebar_threads.py --thread-id <THREAD_ID> --retry-ipc 3`（或 `--cwd <REPO_ROOT>`）自动完成上述 4 步并处理 IPC 命名管道瞬时离线重试。

## Enhanced queue capabilities (merged superset)

In addition to the `S001 1/58 ...` progress banner, `Gemini4` D0-D3 routing, and `codex_thread_bridge.mjs` dispatch, the lease runtime supports:

- **Priority-tier claiming (`priority_order`)**: Configure `priority_order` in `work_item_runtime.json` with a `优先级` column in `work_items.md` so workers claim higher-priority series first.
- **Static `备注` column vs. dynamic `运行备注`**: Preserve static per-item guidance in `备注` (updatable via `--remark` / `--append-remark`) separate from runtime lease notes in `运行备注`.
- **Targeted module claim & atomic reopen (`--module`, `--reopen`, `--force-active`)**: Claim or reopen by `--item-id` or `--module` with `--user-authorization-ref`, and atomically reopen + claim via `reopen_work_item.py --claim` or `claim_next_work_item.py --reopen`.
- **Same-worker expired lease auto-renewal**: Re-entering `claim`, `heartbeat`, or `complete` from the same worker when no other worker claimed the expired item automatically renews the lease.
- **Mechanical inventory bridge (`dlm.py inv export-lease` / `sync-lease`)**: Generate `work_items.md` and `work_item_runtime.json` directly from a `dlm inv` population and sync completed/blocked states and `V#` evidence back after parallel execution.
