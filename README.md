# Agent DLM Skills (`agent-dlm-skills`)

**Outcome-Governed Documented LLM Memory (DLM), Multi-Agent Lease Queue & Content-Hash Release Skill Suite for AI Coding Agents (Codex / Claude Code / Gemini)**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](#环境要求)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20Third--Party-success.svg)](#环境要求)
[![Tests](https://img.shields.io/badge/Tests-260%20Passed-brightgreen.svg)](#4-运行全量自测套件)

`agent-dlm-skills` 是一套专为 AI 编程智能体（OpenAI Codex、Claude Code 等）打造的**工程化知识记忆（`doc_llm` / `docs-llm`）、任务结果治理、多会话并发认领/租约调度与内容哈希版本发布**技能集。

它解决了大模型在长周期、多模块、多智能体并行开发中最常见的四大痛点：
1. **上下文迷失与文档腐化**：改了代码忘改文档，或每次对话把几万行过期文档塞进上下文。
2. **多对话撞单与进度失控**：开启多个 Agent 窗口并行推进同一 Epic 时，互相覆盖文件、重复劳动、缺乏统一进度横幅与租约回收。
3. **虚假结项与“差不多先生”**：口头声称“已完成”，却漏掉分母中的边界模块或用局部测试冒充全量验收。
4. **Git 提交日志敷衍与版本失序**：提交信息只有一句 `update` 或 `fix bug`，无法追溯**修改范围、对应版本、怎么改的、为什么改的**。

---

## 目录

- [核心特性](#核心特性)
- [包含的 8+1 核心技能](#包含的-81-核心技能)
- [下载与安装指南](#下载与安装指南)
- [快速上手：5 分钟跑通完整闭环](#快速上手5-分钟跑通完整闭环)
- [统一 CLI (`dlm.py`) 命令速查](#统一-cli-dlmpy-命令速查)
- [目录结构](#目录结构)
- [支持与致谢（求 Star）](#支持与致谢求-star)

---

## 核心特性

### 1. 双轨自适应知识与任务治理（Markdown 快速轨 + `ledger.json` 确定性轨）
- **轻量快速轨（`Lite / Medium`）**：日常单点修复或中小型迭代直接走 Markdown 轨（`dlm_doctor.py` + `sync_epic_index.py` + `sync_l1_route.py`），零冗余命令开销。
- **确定性账本轨（`High / Max / Ultra`）**：大型重构、跨模块迁移或高风险交付启用 `ledger.json` 单一事实源，内置 6 类确定性实体：
  - `P#`（不可违背原则）
  - `D#`（绑定用户原话的正式决议）
  - `O#`（履约义务）
  - `N#`（机械盘点出的全集母体项）
  - `V#`（分级验证证据：`full / partial / sample / proxy`）
  - `L#`（诚实限制披露：`product / budget / resource-fact`）并支持五分类重开（`regression / omission / new-requirement / superseded / evidence-lost`）。

### 2. 机械全集盘点与多智能体并发租约双向打通（`dlm inv` <-> `multi-llm-lease`）
- **机械全集盘点（`dlm inv`）**：直接通过 `glob`、`grep` 或命令扫描真实源码生成全集分母 `N#`，杜绝手写清单漏项。
- **一键导出并发队列（`dlm inv export-lease`）**：将待办母体一键导出为 `work_items.md` 与 `work_item_runtime.json`。
- **多会话安全并发（`multi-llm-lease`）**：
  - 支持文件锁保护下的原子认领（`claim`）、心跳续租（`heartbeat`）、回填完结（`complete`）与重开（`reopen`）；
  - 支持优先级分档（`priority_order`）、静态 `备注` 列无损保留、指定模块认领（`--module`）；
  - 每次开启子任务前自动生成标准进度标识（如 `S001 1/58 模块导入`）与模型分级路由建议（`D0-D3`）；
  - 完成后通过 `dlm inv sync-lease` 自动回填 `V#` 验证证据并闭合 `N#`。

### 3. 知识库腐化检测与传递影响分析（`dlm kb stale` / `kb map` / `dlm_impact.py`）
- **`L1 -> L2` 确定性路由编译**：基于 `L2` 文档 Frontmatter（`domain`、`summary`、`keywords`、`match_globs`、`depends_on`）自动生成 `L1` 路由表与 `ReadSnapshot`。
- **文档腐化检测（`dlm kb stale`）**：自动对比 `L2` 文档 `last_updated` 与 `match_globs` 命中的最新 Git 源码提交时间，精准揪出落后于代码的过期文档。
- **传递影响分析（`dlm_impact.py`）**：根据变更文件路径或模块名，自动向上追溯 `depends_on` 依赖链，给出最小充分必读集合。

### 4. 内容哈希自动升版与四要素结构化 Git 提交（`dlm-version-master`）
- **内容哈希版本判定**：递归计算模块源码 SHA-256（排除 `bin/`、`obj/` 等构建产物），结合改动语义自动判定 `none / patch / minor / major` 升版。
- **四要素结构化中文 Commit 门禁**：强制基于 `git diff --cached` 真实改动，生成包含以下四要素的多行中文提交说明，彻底告别模糊日志：
  1. **修改范围**：按模块/文件列出本次暂存区涉及的具体范围与职责；
  2. **对应版本**：记录改动前后的版本号对比（如 `1.4.2 -> 1.4.3`）及升版依据；
  3. **怎么改的**：结合真实 Diff 说明核心实现机制、接口或状态流变更；
  4. **为什么改的**：说明业务背景、修复的根因或架构演进动机。

---

## 包含的 8+1 核心技能

| 技能目录 | 触发命令 / 技能名 | 核心职责说明 |
|---|---|---|
| `skills/dlm-build` | `$dlm-build` | 初始化、迁移、校验知识库骨架（`BRIEF` / `L0` / `L1` / `L2` / `Reference` / `SOP`），编译 `L1` 路由表，运行 `kb stale` 与 `kb map` |
| `skills/dlm-load` | `$dlm-load` | 按任务或变更路径加载最小充分上下文（支持 `<context_manifest schema="2">`、`dlm_impact.py` 与 `dlm.py brief`） |
| `skills/dlm-plan` | `$dlm-plan` | 将需求拆解为 Epic / Subtask、验收基线、机械全集盘点（`dlm inv`）与租约队列导出 |
| `skills/dlm-reflect` | `$dlm-reflect` | 执行设计质询（Design Grill）与结项复审（Closure Review），校验 `full/sample/proxy` 证据、全集闭合率与反例边界 |
| `skills/dlm-sediment` | `$dlm-sediment` | 将已验证的实现事实、关键决议与陷阱写回 `L2` 与任务账本，同步路由与索引 |
| `skills/dlm-close-release` | `$dlm-close-release` | 编排安全结项、沉淀、可选 Release 构建校验与精确路径 Git 提交 |
| `skills/dlm-version-master` | `$dlm-version-master` | 内容哈希版本判定、Release 元数据验证、精确白名单暂存与四要素结构化 Git Commit/Push |
| `skills/multi-llm-lease` | `$multi-llm-lease` | 多会话并发 claim/lease 队列运行时（支持进度横幅、优先级分档、原子重开与 Codex 独立新对话派发桥接） |
| `skills/_shared` | 共享内核 | 共享结果治理契约（`outcome-governance.md`）、`dlm.py` 统一 CLI 内核、不变量检查器与中英双语视图模板 |

---

## 环境要求

- **Python**: `3.10` 及以上（仅使用 Python 标准库，**无需 `pip install` 任何第三方依赖**）
- **Git**: `2.25` 及以上
- **支持平台**: Windows (PowerShell / CMD)、macOS、Linux

---

## 下载与安装指南

### 第一步：克隆下载本仓库

```bash
git clone https://github.com/atlasray66-collab/agent-dlm-skills.git
cd agent-dlm-skills
```

### 第二步：选择安装方式（三选一）

#### 方式 A：安装到全局技能目录（推荐，所有项目通用）

将技能包安装到 Codex / Agent 的全局技能目录中，并运行 SHA-256 完整性校验：

```powershell
# Windows PowerShell
python -X utf8 install.py --skills-dir "$HOME/.codex/skills/skills"
python -X utf8 install.py --skills-dir "$HOME/.codex/skills/skills" --check
```

```bash
# macOS / Linux
python3 install.py --skills-dir "$HOME/.codex/skills/skills"
python3 install.py --skills-dir "$HOME/.codex/skills/skills" --check
```

#### 方式 B：安装到单个业务仓库（项目级隔离安装）

如果你希望将这套技能随某个业务仓库一起分发（安装到目标仓库的 `.agents/skills/` 与 `.claude/skills/`）：

```bash
python -X utf8 install.py --host "/path/to/your-project"
python -X utf8 install.py --host "/path/to/your-project" --check
```

#### 方式 C：免安装直接通过根级 CLI 调用

无需复制文件，直接通过本仓库根目录的 `dlm.py` 指向任意目标仓库即可工作：

```bash
python -X utf8 dlm.py --root "/path/to/your-project" --help
```

---

## 快速上手：5 分钟跑通完整闭环

### 1. 在对话中直接唤起技能（Prompt 方式）

安装完成后，你可以在 Codex 或 Claude Code 对话框中直接通过自然语言或技能名调用：

- **初始化知识库**：`使用 $dlm-build 帮当前仓库初始化 doc_llm 知识库骨架并生成 L1 路由表`
- **加载任务上下文**：`使用 $dlm-load 加载 E001 相关的上下文与受影响模块`
- **规划任务与并发队列**：`使用 $dlm-plan 为本次重构建立 Epic，盘点全部目标模块并导出 multi-llm-lease 队列`
- **多窗口并行领单开发**：`使用 $multi-llm-lease 认领下一个待办工作项，完成后自动执行 $dlm-reflect 验证与 $dlm-sediment 写回`
- **结项审查**：`使用 $dlm-reflect 对 E001 S001 进行结项复审，检查是否有未闭合的边界条件`
- **升版与结构化提交**：`使用 $dlm-version-master 执行版本判定、构建校验，并按四要素格式提交推送到远端`

### 2. 使用命令行工具驱动（CLI 方式）

```bash
# 1) 在目标仓库初始化知识库并体检
python -X utf8 dlm.py --root "/path/to/repo" init --lang zh-CN
python -X utf8 skills/dlm-build/scripts/dlm_doctor.py --repo-root "/path/to/repo"

# 2) 创建 Epic 并机械盘点源码母体 (Inventory)
python -X utf8 dlm.py --root "/path/to/repo" epic new --slug core-refactor --goal "核心模块重构" --scope High
python -X utf8 dlm.py --root "/path/to/repo" inv add --epic E001 --id N1 --target "src/core.py" --category module --source glob --locator "src/*.py"

# 3) 一键导出为多智能体并发租约队列
python -X utf8 dlm.py --root "/path/to/repo" inv export-lease --epic E001

# 4) 认领工作项 -> 完成工作项 -> 回填账本证据
python -X utf8 skills/multi-llm-lease/scripts/claim_next_work_item.py --task-dir "/path/to/repo/doc_llm/Tasks/E001_core-refactor" --session-id worker-01
python -X utf8 skills/multi-llm-lease/scripts/complete_work_item.py --task-dir "/path/to/repo/doc_llm/Tasks/E001_core-refactor" --session-id worker-01 --item-id N1 --summary "完成重构" --verification "pytest passed" --evidence-ref "tests/test_core.py"
python -X utf8 dlm.py --root "/path/to/repo" inv sync-lease --epic E001

# 5) 同步 L1 路由表与检查过期 L2 文档
python -X utf8 skills/dlm-build/scripts/sync_l1_route.py --repo-root "/path/to/repo"
python -X utf8 dlm.py --root "/path/to/repo" kb stale
```

### 3. 运行全量自测套件

本仓库内置 **260 项自动化单元测试**（涵盖共享内核、路由编译、传递影响分析、租约并发锁、链接完整性与隐私防泄漏校验）：

```bash
python -X utf8 scripts/test_all.py
```

---

## 统一 CLI (`dlm.py`) 命令速查

| 子命令 | 作用说明 |
|---|---|
| `dlm.py init` | 初始化项目 `doc_llm` / `docs-llm` 目录与基础模板 |
| `dlm.py adopt` | 扫描现有业务仓库并生成存量接入报告与知识骨架 |
| `dlm.py brief` | 生成当前活跃 Epic 的精简恢复摘要（Context Brief） |
| `dlm.py check` | 运行 10 项确定性不变量检查（Invariants Gate） |
| `dlm.py epic` / `subtask` | 创建、激活、推进 Epic 与 Subtask 状态机 |
| `dlm.py rec` | 向 `ledger.json` 写入 `P / D / O / V / L` 记录 |
| `dlm.py inv` | 机械全集盘点（`add / scan / verify / reopen / export-lease / sync-lease`） |
| `dlm.py kb` | 知识库治理（`route` 路由生成、`stale` 腐化检测、`map` L2 质量扫描） |
| `dlm.py render` | 从 `ledger.json` 确定性渲染 Markdown 视图 |

---

## 目录结构

```text
agent-dlm-skills/
├── dlm.py                      # 仓库根级统一 CLI 入口
├── install.py                  # 跨平台安装与 SHA-256 完整性校验工具
├── scripts/
│   └── test_all.py             # 一键运行全部 260 项单测与安装端到端自检
└── skills/
    ├── _shared/                # 统一确定性内核、结果治理规范与多语言模板
    ├── dlm-build/              # 知识库构建、迁移、路由编译与腐化检测
    ├── dlm-load/               # 最小充分上下文加载与传递影响分析
    ├── dlm-plan/               # 任务拆解、机械盘点与并发队列导出
    ├── dlm-reflect/            # 设计质询与结项复审
    ├── dlm-sediment/           # 知识沉淀、账本写回与索引同步
    ├── dlm-close-release/      # 安全结项与精确路径发布编排
    ├── dlm-version-master/     # 内容哈希升版与四要素结构化 Git 同步
    └── multi-llm-lease/        # 多智能体并发认领/续租/完结/重开调度器
```

---

## 支持与致谢（求 Star）

如果 `agent-dlm-skills` 帮你的 AI 编程工作流告别了**上下文腐化、多窗口撞单、虚假结项与敷衍的 Git 提交日志**，请移步仓库右上角点亮一颗 **Star** 支持我们！

你的每一颗 **Star** 都是我们持续打磨多智能体工程化治理与自动化工具链的最大动力：
- 欢迎 **Star** 收藏本仓库，方便随时同步最新技能升级；
- 欢迎 **Fork** 并提交 Issue / Pull Request，一起共建更强大的 Agent 工程基础设施！
