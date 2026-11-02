# E{NNN}: {Epic 标题}

## Meta

| 字段 | 值 |
|------|---|
| 象限 | 🔴 / 🟡 / 🔵 / ⚪ |
| 涉及领域 | D{N} ({领域名}) |
| 创建日期 | YYYY-MM-DD |

> Epic 不维护聚合状态；Subtask Meta 是状态 SSOT。

## 目标

{目标}

## 背景

{背景}

## 范围

- 包含：{范围}
- 排除：{范围}

## 上下文构建协议

```xml
<context_manifest schema="2" project="{project_id}" task="E{NNN}" epic="E{NNN}">
  <file path="doc_llm/00_Global/L0_global_redlines.md" intent="全局红线" required="true" />
  <file path="doc_llm/Tasks/E{NNN}_{短名}/plan/execution_plan.md" intent="执行规划" required="false" />
</context_manifest>
```

## 子任务索引

> 由 `sync_epic_index.py` 生成。

| ID | 子任务 | 优先级 | 状态 | 依赖 | 文件 |
|:---:|------|:---:|:---:|:---:|------|

## 连续执行队列（可选）

> 仅当 Baseline Owner 对一个具名、有序且边界明确的队列作出一次性授权时填写。每个 Subtask 仍保留独立 Acceptance Baseline、Authorized Scope 和写集；本节不合并权限，也不允许并发跨越 collision group。

| 队列名 | 顺序 | 每项进入/退出条件 | 依赖顺序 | 共同停止门 | Collision Group / 写集约束 | 授权状态 |
|--------|------|-------------------|----------|------------|-----------------------------|----------|
| {queue-name} | S{NNN} -> S{NNN} | {条件} | {依赖} | {人工门禁 / 队列完成 / invalidation} | {互斥组或互不重叠写集} | Draft / Authorized |

> 任一项的目标、验收条件、Authorized Scope、写集、外部动作、依赖或停止线变化时，该项回到 `Draft` 并退出连续执行，等待 Baseline Owner 重新定标。

## 关键产出物

| 类型 | 文件 | 说明 |
|------|------|------|
