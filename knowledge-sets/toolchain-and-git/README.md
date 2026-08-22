# 游戏开发工具链与可复现工程

<div class="course-meta">
<span class="course-badge">阶段 0</span>
<span class="course-badge">深度 D2</span>
<span class="course-badge">实践 P0</span>
<span class="course-badge course-complete">已完成</span>
</div>

把环境、版本控制、构建、调试和自动检查变成可靠的日常工作流。

## 可验证出口

交付一个能从全新环境复现构建、测试和发布的最小游戏工程，并能解释 Unity、Unreal Engine 与专业团队在源、缓存、产物、资产协作和 CI 边界上的共同原则与差异。

## 你会完成什么

- 用“源—工具—配置—缓存—产物—证据”分析工具链，而不是背菜单；
- 用提交、分支、合并、回退和二分定位游戏项目回归；
- 让随机种子、内容版本、构建命令和工具版本成为可检查输入；
- 设计一个能在干净 checkout 上运行的 CI/发布门禁；
- 在 Unity/UE 项目中判断哪些文件该提交、哪些目录必须可再生。

## 前置与推荐路径

不要求先学 C#、C++ 或引擎。需要会运行 Python 3.11+、Git 2.x 和基本终端命令。先读[课程地图](lessons/00-course-map.md)，然后按顺序阅读 5 个问题导向的课程页面；实践和题目可以穿插完成。

## 实践入口

- [主实践：可复现的 seeded-room 小游戏](labs/README.md)
- [实践解法与失败诊断](labs/solutions.md)
- [题目](assessments/questions.md) / [答案](assessments/answers.md)
- [术语表](notes/glossary.md)
- [研究笔记](references/research-notes.md) / [完整书目](references/bibliography.md)

## 版本边界

课程中的 Git、GitHub Actions、Unity 和 Unreal Engine 资料按 2026-08-22 查阅的官方文档整理。正文讲跨版本不变量；涉及编辑器命令行、Package/插件格式、action 版本或平台 SDK 时，必须以项目实际锁定版本的官方文档复核。
