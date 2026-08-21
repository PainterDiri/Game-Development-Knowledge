# AI 课程知识集生成提示模板

```text
你现在要为本仓库生成一门公开课程知识集。

目标课程：<从 roadmap/course-index.json 选择下一门未完成课程>
课程 slug：<course-slug>
培养方案来源：<培养方案/增补>
目标深度：<D1/D2/D3>
挂接实践：<P0-P5 或指定实验>

必须先做：
1. 读取 AGENTS.md、roadmap/README.md、roadmap/course-index.json；
2. 读取 standards/ 下与生成相关的规范；
3. 根据前置课程的公开出口能力设计一个极短诊断，不依赖个人 progress 文件；
4. 研究官方/一手资料，记录版本、日期、链接和不确定性；
5. 先写 lessons/00-course-map.md，经检查后再写详细章节。

内容要求：
- 面向未来游戏程序员、独立开发者与大厂候选人；
- 以游戏问题驱动，但不牺牲课程原理；
- 每个核心知识点回答定义、机制、取舍、游戏映射、验证；
- 术语首次出现解释中文、英文和缩写；
- D3 包含简化实现、复杂度/内存分析、失败案例、测试和架构取舍；
- 每门课最多 1 个主实践 + 2 个微实验；
- 肉鸽相关时讨论随机种子、数据驱动、道具组合、冲突、存档或可复现；
- 网络相关时讨论信任边界、权威服务器、延迟、复制/预测/插值或回滚；
- 不要求学习者打勾、写作答日志、错题本、决策日志或学习报告；
- 不用前言、目录、鸡汤和重复 API 描述充字数。

必须生成/更新：
- knowledge-sets/<course-slug>/README.md
- lessons/00-course-map.md 与后续章节
- labs/README.md 与实验材料
- labs/solutions.md（折叠提示、参考路线、验收方法、常见失败、替代方案）
- assessments/questions.md
- assessments/answers.md（题号一一对应的提示、答案、推理、边界、验证和游戏迁移）
- assessments/rubric.md
- notes/glossary.md
- references/research-notes.md、bibliography.md
- 必要的 code/ 与 assets/ 说明

生成后必须：
1. 运行 python3 scripts/sync_docs.py、python3 scripts/check_repo.py 和 git diff --check；
2. 按 quality-gates.md 自检并列出未通过项；
3. 更新 course-index.json 的公开内容状态；
4. 给出运行命令、验证结果、学习出口测试和下一步；
5. 完成且用户授权时 commit 并 push；远程不可用时明确说明，不伪造成功。
```
