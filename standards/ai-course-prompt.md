# AI 课程生成提示

```text
请为本仓库生成或重做指定的一门课程，严格只处理这一门课。

执行前：
1. 阅读 AGENTS.md、roadmap/README.md、roadmap/course-index.json 和相关 standards；
2. 确认前置出口、深度、课程角色、零基础诊断和唯一主实践；
3. 研究官方文档、标准、论文、源码和大学教材，核对版本、访问日期、用途、限制与冲突；
4. 先画“前置能力 → 真实问题 → 概念依赖 → 章节产出 → 章末练习 → 主实践”的课程图；
5. 先写 README 课程首页与章节地图，再依照地图逐章生成详细正文。README 是唯一地图入口。

正文要求：
- 每章从可观察任务或失败开始；第一次出现术语、命令、符号、类型或 API 时先用普通话解释，再给正式定义；
- 每个核心知识块讲清机制/不变量、最小示例、逐行解释、故意失败、边界/取舍、验证、游戏映射和下一章用途；
- D3 课程按概念依赖拆出至少 12 个连续知识单元，不能用流水账或名词列表冒充教材；
- 每章结尾放 2–5 道代表性练习。题目、最小提示和完整讲解必须在同一章内，讲解包含推理、边界、常见错误、验证和游戏映射；不要创建独立 assessments、参考书目或研究笔记页面；
- 只保留一个与本课程直接相关的主实践，可用 Unity，但不要求逐课接入最终 RogueSlice；
- 实践必须复制到 `.practice/<course-slug>/` 或仓库外，公开 code 只读；写出 `init_practice.py`、`git check-ignore`、`git status`、禁止强制添加和清理风险；
- Git/协作课程逐条解释命令改变的状态、共享历史风险、验证、恢复和何时选择 merge/rebase/revert/reset/reflog/bisect；
- AI 课程必须区分规则系统、传统机器学习、深度学习、LLM/Transformer 与生成式内容，并解释 data → representation → model → loss → update → evaluation → deployment；
- 游戏映射必须落到运行时、工具、资源、网络或生产中的具体决策，不能只写“可用于游戏”。

生成后验收：
1. 以零基础求知者身份逐章通读，执行命令、尝试练习、寻找跳步和未解释术语；
2. 以专业审查者身份检查机制、边界、复杂度、生命周期、版本、失败和证据；
3. 对发现的讲不透、跑题、重复或可拓展点返工，不得只记录问题；
4. 运行 python3 scripts/sync_docs.py、python3 scripts/check_repo.py、git diff --check 和 mkdocs build --strict；
5. 只有正文、章末练习、唯一主实践、代码、索引和质量门禁全部相符时才标记 completed；未经用户授权不 push。
```
