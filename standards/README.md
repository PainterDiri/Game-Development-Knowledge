# 维护与生成规范

这里服务于课程维护者和 AI 生成流程。规范的目标是阻止跳步、注水、不可复现和误提交个人实践，不是让所有课程套同一目录。

## 最常用文件

1. [内容质量规范](knowledge-generation-spec.md)：教材式深度、章节证据和生成后验收；
2. [课程生成流程](generation-workflow.md)：研究、课程地图、逐章生成、求知者复查和发布；
3. [实践设计](practice-design.md)：每课一个主实践及 Git 隔离；
4. [质量门禁](quality-gates.md)：何时能标记为完成。

## 按需查阅

- [文件职责与可变结构](course-folder-template.md)
- [研究与就地引用](research-and-citation.md)
- [命名与架构](naming-and-architecture.md)
- [AI 课程提示](ai-course-prompt.md)

## 当前结构原则

- 练习题放在所依赖章节的结尾，题后就地提供折叠提示与讲解；
- 不创建独立练习题页、研究笔记页或参考书目页；
- 每门课只设计一个与该课直接相关的主实践，不要求逐课接入最终项目；
- 公开代码只读，个人修改进入被 Git 忽略的 `.practice/<course-slug>/`；
- 完整肉鸽项目由后续 Unity 生产与毕业项目课程集中推进。
