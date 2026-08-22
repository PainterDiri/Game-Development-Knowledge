# 游戏开发工具链与可复现工程

<div class="course-meta">
<span class="course-badge">阶段 0</span>
<span class="course-badge">深度 D2</span>
<span class="course-badge">实践 P0</span>
<span class="course-badge course-complete">可学习</span>
</div>

这门课解决一个具体问题：**当项目从“我电脑上能跑”变成团队、CI 和发行环境都要可靠时，如何知道输入是什么、命令是什么、产物是什么，以及失败时从哪里查起。**

## 先走这条路径

<div class="grid cards" markdown>

-   :material-map-outline: **先看课程地图**

    [00 · 课程地图](lessons/00-course-map.md)解释章节依赖、前置诊断、实践 checkpoints 和验收证据。

-   :material-book-open-variant: **按问题读正文**

    从[源到产物](lessons/01-source-to-artifact.md)开始，依次学习环境、Git、资产协作、构建、调试和 CI。

-   :material-hammer-wrench: **边学边做主实践**

    [主实践说明](labs/README.md)把每章知识接到一个可以反复构建的 seeded-room 小游戏；不用先安装 Unity 或 Unreal。

-   :material-help-circle-outline: **最后做高价值题**

    [题目与折叠答案](assessments.md)放在同一页。先独立作答，再按需展开提示和解析；没有为了凑数的主观题。

</div>

## 可验证出口

完成后，你应能从一个干净 checkout：

1. 说明源码、元数据、工具、缓存、产物和证据的边界；
2. 用 Git 的提交图、分支、合并、回退和二分定位一次游戏回归；
3. 把代码版本、内容版本、工具版本、依赖、平台、随机种子和构建命令列入可检查输入；
4. 在 Unity 或 Unreal Engine 中判断哪些目录应提交、哪些目录必须可再生，并把编辑器操作迁移为自动化入口；
5. 运行测试、构建、冒烟检查并保留 manifest、日志和可回滚 artifact；
6. 解释 CI 中缓存、artifact、权限、密钥和发布环境的不同边界。

## 章节地图

| 顺序 | 教学页面 | 这一页解决的可验证问题 | 完成证据 |
|---:|---|---|---|
| 1 | [源到产物](lessons/01-source-to-artifact.md) | 项目里的文件为什么不能一律提交或一律忽略？ | 能画出一次构建的输入/输出边界 |
| 2 | [环境与依赖](lessons/02-environment-and-dependencies.md) | 为什么锁版本仍可能无法复现？ | 能写出最小环境清单和冷启动命令 |
| 3 | [Git 协作](lessons/03-git-model-and-collaboration.md) | 提交、分支、冲突和回退到底改变了什么？ | 能安全回退共享历史并解释代价 |
| 4 | [游戏资产协作](lessons/04-game-assets-and-engine-workflows.md) | Unity/UE 的资产引用、二进制和缓存如何进入工程边界？ | 能设计资产提交、锁定和恢复规则 |
| 5 | [构建与测试](lessons/05-build-test-and-manifest.md) | 如何把“能打开编辑器”变成可验收构建？ | 能生成确定性 manifest 和测试报告 |
| 6 | [调试与回归](lessons/06-debugging-and-regression.md) | 如何把“某个 seed 坏了”变成最小可判定实验？ | 能用最小复现和 bisect 定位回归 |
| 7 | [CI、发布与回滚](lessons/07-ci-release-and-rollback.md) | CI 如何提供证据而不是制造另一台神秘机器？ | 能设计门禁、artifact 和旧版本回滚 |

## 主实践的三个 checkpoint

实践不要求一次完成全部内容，按以下顺序推进：

- **Checkpoint A：确定性**：固定 seed，测试同一输入产生同一房间序列；
- **Checkpoint B：可重建**：清理 `dist/` 后从源码重建，生成稳定 manifest；
- **Checkpoint C：可诊断**：故意引入 seed=7 的回归，用测试、日志和 Git 历史定位，再保留回归测试。

每个 checkpoint 都有运行命令、预期结果、故意失败和最小版本；不要求写学习日志或实验报告。

## 前置、环境和版本边界

不要求先会 C#、C++ 或引擎。需要能运行 Python 3.11+、Git 2.x 和基本终端命令。Unity 与 Unreal Engine 章节讲跨版本不变量；涉及 Editor/Engine CLI、Package/插件格式、action 版本或平台 SDK 时，必须按项目锁定版本复核官方文档。

## 课程内资源

- [主实践题面](labs/README.md) · [实践提示、路线和失败诊断](labs/solutions.md)
- [题目与折叠答案](assessments.md)
- [术语表](notes/glossary.md)
- [研究笔记](references/research-notes.md) · [完整书目](references/bibliography.md)
- [可运行实践代码](code/repro-game/README.md)
