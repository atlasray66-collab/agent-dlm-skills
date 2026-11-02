# Multi-LLM Lease Skill（Gemini 4 & Codex 多对话并行升级版）

## 1. 核心升级概览

1. **主力模型切换为 Gemini 4 并内置任务分级适配 (`D0`~`D3`)**
   - `D0` -> `gemini-4-flash` (`thinking=low`, 推荐并发 6)
   - `D1` -> `gemini-4-pro` (`thinking=medium`, 推荐并发 4)
   - `D2` -> `gemini-4-thinking` (`thinking=high`, 推荐并发 2)
   - `D3` -> `gemini-4-ultra` (`thinking=high`, 推荐并发 1)
2. **全面采用 Codex 多对话并行 (`codex_new_thread`) 替代多子代理**
   - 解决多子代理上下文割裂问题；每个子任务通过 `prepare_codex_thread_dispatch.py` 领取后，由 `create_thread` 创建独立 Codex 新对话承载完整上下文。
3. **新任务开启前强制打印进度横幅 (`task_banner`)**
   - 自动计算总任务数、当前任务序号、已完成数、进行中数、待开发数，生成标准横幅如 `S001 1/58 3D平面拟合导入`。
4. **子任务完成后自动触发 `$dlm-reflect` 验证与 `$dlm-sediment` 证据写回**
   - 新对话提示词与 SOP 内置强制闭环：`编码与自测 -> $dlm-reflect 验证 -> $dlm-sediment 写回验证证据 -> complete_work_item.py 释放锁`。
