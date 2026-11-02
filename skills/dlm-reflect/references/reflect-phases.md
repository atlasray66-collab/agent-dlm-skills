# Reflect Phases

本文件只定义 `Closure Review` 的 6 个阶段。`Design Grill` 使用 [grilling-protocol.md](grilling-protocol.md), 不伪装成已有实现的闭环复检。Closure Review 默认是实现者的定向验收; 只有用户要求、合同要求或实质风险收益成立时才升级为正式独立审计。

## R1. Re-anchor

回到原始任务定义。

检查点:

- 当前目标到底是什么
- 明确写过的约束有哪些
- 哪些内容本轮本来就不该做
- 当前任务的完成标准是什么
- Acceptance Baseline 是否为 Draft / Frozen / Verified, Owner、Authorized Scope、验收条件与停止线是什么

输出:

- 一句任务目标
- 一句非目标边界
- 一组声明范围入口

## R2. Inspect Result

只看真实产物, 不看记忆。

先确认客观改动面:

```bash
git diff --cached
git diff
git ls-files --others --exclude-standard
```

如果工作区还有其他无关修改, 应限制到当前任务涉及的文件或目录, 避免把别人的改动误判成本轮结果。

然后做一次声明范围对照:

- 从 Task 目标、`context_manifest` 源码文件、claim/work item、用户明确允许的入口中整理“声明范围”
- 将 diff 文件集逐项标记为:
  - 声明内改动
  - 合理支撑改动
  - 可疑越界改动
- 出现“可疑越界改动”时, 不要直接合理化, 必须在边界审计阶段解释它为什么不算 scope drift

检查点:

- 这轮到底改了哪些文件 / 配置 / 文档 / 数据
- 改动是否直接对应原始目标
- 哪些内容已验证, 哪些只是已改未证
- 当前状态更像完成、部分完成、偏移, 还是阻塞

输出:

- 实际改动摘要
- 声明范围对照
- 已验证事实
- 验证缺口

## R3. Simulate Scenarios

只在 Frozen 条件或具体实质风险需要时从主路径退出来检查次路径。不得为了展示严谨而固定凑场景数量。

检查点:

- 正常路径之外还有哪些状态
- 输入异常、依赖失败、顺序错位时会怎样
- 状态切换、回退、重入、重复执行是否稳定
- 当前技术栈是否有典型风险面尚未覆盖

读取 [scenario-lenses.md](scenario-lenses.md), 但只挑能证实/证伪当前声明或防止具体风险的 lens。

输出:

- 遗漏场景列表
- 高风险未证场景

## R4. Grill the Closure Claim

不要把“看起来完成”当结论。读取 [grilling-protocol.md](grilling-protocol.md), 把完成声明拆成关键前提并逐条施压。

检查点:

- 当前完成结论依赖哪些事实和推论
- 哪一条前提证据最弱、最可能让结论翻转
- 当前证据证明的是实际行为, 还是仅证明文档、计划、脚手架或代表样例存在
- 是否存在一个可信反例能击穿当前结论
- 失败、回滚、重入或恢复路径是否只是被假设为成立

输出:

- 关键前提及 `proven / disproven / unknown` 状态
- 最薄弱前提及其证据
- 仍需补证或向用户追问的单一问题

## R5. Audit Boundaries

检查这轮是不是悄悄越界了。

检查点:

- 是否超出了当前 Task 的原始 scope
- 是否把职责混在一起
- 是否引入新的隐式耦合
- 是否破坏既有层级或契约边界

有疑问时再读 [boundary-audit.md](boundary-audit.md)。只有能定位违反 Frozen 条件/SSOT、直接证据、当前影响和 Authorized Scope 的边界问题才是 blocking Finding; 其余为 Advisory/Deferred。

输出:

- 边界风险
- scope 漂移信号

## R6. Decide Routing

不要只给诊断, 还要给分流结论。

检查点:

- 当前结果是否应 `stop-verified`, 或存在真实触发条件进入 `dlm-sediment`
- 是否需要继续当前 Subtask
- 是否需要新增后续任务
- 是否需要回 `dlm-plan` 或 `dlm-build`

读取 [routing-rules.md](routing-rules.md) 做最终判定。

输出:

- routing 结论
- 是否允许进入 sediment
