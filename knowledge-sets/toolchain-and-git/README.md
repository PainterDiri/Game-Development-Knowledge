# 游戏开发工具链、Git 与可复现工程

<div class="course-meta">
<span class="course-badge">阶段 0</span>
<span class="course-badge">深度 D2</span>
<span class="course-badge">实践 P0</span>
<span class="course-badge course-complete">可学习</span>
</div>

> **适合谁**：默认你是程序初学者。只要会打开文件和安装 Python/Git，就可以从第 1 章开始；课程不会要求你先理解“构建边界”“提交图”或 CI。

## 为什么课程要按这个顺序

最开始只讲“构建系统的边界”会产生跳步：学习者尚不知道命令怎样运行、Git 在记录哪个状态、团队为何需要分支，就被要求分类源码、缓存和 artifact。本课程改为三段递进：

```text
A. 个人能安全工作
文件/终端 → 工作区/暂存区/提交 → 分支/远端 → 合并与恢复

B. 多人能稳定协作
任务 → PR/评审/CI → 合并 → 集成 → 发布候选与回滚

C. 工程能被另一台机器复现
构建输入/缓存/产物 → 环境与随机性 → 测试诊断 → CI 发布
```

上一段是下一段的前置：不知道“提交”和“分支”，无法理解 PR 合并；不知道项目的输入和产物，CI 只会变成一份看不懂的 YAML。

## 学完后的可验证出口

你应能：

1. 在终端中定位项目、运行命令、阅读退出码和区分源文件/运行产物；
2. 解释并正确使用常见 Git 命令，指出它们改变工作区、暂存区、本地提交还是远端引用；
3. 选择 merge、rebase、cherry-pick、revert、reset、reflog 和 bisect，并说明共享历史风险；
4. 把一个团队任务从短分支、PR、review、CI 送入集成构建、发布候选和正式版本；
5. 区分源码、元数据、工具、依赖、缓存、artifact 和证据；
6. 从干净 checkout 运行测试、冷构建、产物冒烟和最小回归；
7. 记录 build ID、content version、seed、run ID、工具版本和回滚 artifact。

## 章节地图

| 顺序 | 章节 | 依赖与核心问题 | 完成证据 |
|---:|---|---|---|
| 1 | [程序、终端与项目](lessons/01-computer-terminal-and-project.md) | 从零建立文件、路径、进程和退出码 | 能逐条解释一次运行命令 |
| 2 | [Git 日常基础](lessons/02-git-daily-workflow.md) | 工作区、暂存区和提交如何连接 | 能只提交一个目的并验证 staged diff |
| 3 | [分支、远端与同步](lessons/03-branches-remotes-and-sync.md) | 多人如何拥有不同历史并交换提交 | 能画出本地/远端引用的移动 |
| 4 | [合并、冲突与恢复](lessons/04-integration-conflicts-and-recovery.md) | 分叉历史怎样整合，误操作怎样恢复 | 能选择 merge/rebase/revert/reset/reflog |
| 5 | [专业团队工作流](lessons/05-professional-team-workflow.md) | 任务怎样经过 PR、测试、集成和发布 | 一份从任务到回滚的交付方案 |
| 6 | [构建系统的边界](lessons/06-build-system-model.md) | 哪些是输入、缓存、产物和证据 | 一张带所有者/生命周期的工程表 |
| 7 | [可复现性与环境](lessons/07-reproducibility-and-environment.md) | 版本、路径、时间、随机和导入为何漂移 | 两次冷构建比较与环境清单 |
| 8 | [测试、构建与诊断](lessons/08-testing-building-and-diagnosis.md) | 怎样把失败缩成可判定证据 | 测试报告、manifest、最小复现/bisect |
| 9 | [CI、发布与回滚](lessons/09-ci-release-and-rollback.md) | 云端怎样执行同一入口并发布同一 artifact | CI 设计、artifact 清单和回滚 runbook |

### 必修与选读

- 第 1–5 章是所有学习者的 Git 与协作主干；
- 第 6–9 章是进入真实 Unity/UE 工程、团队构建和发行前的工程主干；
- Git LFS、Perforce、大型平台矩阵和签名细节属于按项目规模选读，但相关边界必须知道。

## 前置诊断

在终端中尝试：

```bash
python3 --version
git --version
pwd
```

若任何命令不知道在做什么，直接从第 1 章开始。若已能独立完成 `status → diff → add -p → commit → switch -c → push`，可快速浏览第 1–3 章，但不要跳过第 4–5 章的共享历史和团队交付逻辑。

## 唯一主实践与章末练习

- [主实践：可复现 seeded-room 工程](practice.md)：在隔离的 `.practice/toolchain-and-git/` 中完成 Git 基础里程碑、确定性、冷构建和 bisect；
- 每章结尾均有代表性练习、最小提示与折叠讲解，不再设置集中练习题页面；
- 课程中使用的版本敏感资料在相关章节就地标注，不再设置独立书目或研究笔记页。

## 与后续课程的连接

- C、数据结构与数学课程会直接复用终端、测试、分支和小提交；
- 软件工程课程会深化需求拆分、代码评审、测试策略、发布与团队职责；
- Unity/UE 课程会把同一构建模型映射到资产元数据、导入缓存、平台 SDK 和可下载包；
- 发行课程会继续处理签名、商店、兼容、遥测和线上回滚。
