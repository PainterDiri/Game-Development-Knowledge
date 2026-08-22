# 游戏开发工具链与可复现工程

<div class="course-meta">
<span class="course-badge">阶段 0</span>
<span class="course-badge">深度 D2</span>
<span class="course-badge">实践 P0</span>
<span class="course-badge course-complete">可学习</span>
</div>

> **这不是 Git 命令课。** 这是一门交付工程课：你要学会把一个游戏项目的输入、转换、验证、产物和失败证据连成一条可以重建的链。

## 先建立一个总模型

一个可交付的游戏构建可以写成：

```text
artifact = Build(
    source_snapshot,
    asset_metadata,
    engine_and_compiler,
    locked_dependencies,
    target_platform,
    build_config,
    declared_random_inputs
)
```

如果构建脚本还偷偷读取了本机缓存、用户目录、当前时间、网络上的最新包或编辑器里未保存的设置，那么它仍然可能“在我电脑上成功”，但不能称为可复现工程。

本课程围绕一个反复出现的诊断问题组织：

> **当两个构建结果不同，差异究竟来自源码、资产、工具、环境、随机输入、缓存，还是发布流程？**

## 课程地图：一页完成定位、地图与学习顺序

### 你将完成的交付能力

学完后，你应能从全新 checkout 完成并解释：

1. 把项目路径分为源、元数据、工具、依赖、缓存、产物和证据，并为每一类写清所有者与生命周期；
2. 用“显式输入 + 受控环境 + 稳定命令 + 可观察证据”定义可复现，而不是把“版本号相同”当作证明；
3. 解释 Git 的提交对象、引用和工作区状态，并选择合适的合并、回退、清理和二分策略；
4. 在 Unity 与 Unreal Engine 中判断 `.meta/GUID`、序列化资产、插件、派生缓存和平台 SDK 的工程边界；
5. 设计分层门禁：静态检查 → 测试 → 资产/导入检查 → 构建 → 产物冒烟 → 发布；
6. 把一个 seed 回归压缩为最小测试，保留日志、manifest、构建 ID 和可回滚 artifact；
7. 解释 CI cache、artifact、release、密钥和权限为什么不能混为一谈。

### 章节路线与完成证据

| 顺序 | 章节 | 核心问题 | 你要留下的证据 |
|---:|---|---|---|
| 1 | [构建系统的边界](lessons/01-build-system-model.md) | 哪些东西是输入，哪些东西只是缓存或结果？ | 一张带所有权/生命周期的工程边界表 |
| 2 | [可复现性与环境](lessons/02-reproducibility-and-environment.md) | 为什么锁版本仍会失败，随机和资产导入如何进入输入？ | 两次冷构建比较与一份环境清单 |
| 3 | [Git 与资产协作](lessons/03-git-and-asset-collaboration.md) | Git 记录了什么，文本/二进制资产怎样安全协作？ | 一次可审查回退或冲突恢复演练 |
| 4 | [测试、构建与诊断](lessons/04-testing-building-and-diagnosis.md) | 怎样把“能打开编辑器”变成可定位的工程证据？ | 测试报告、manifest、最小复现与 bisect 结果 |
| 5 | [CI、发布与回滚](lessons/05-ci-release-and-rollback.md) | 怎样让云端执行本地已验证的流程，并可安全回滚？ | 最小 CI 设计、artifact 清单和回滚决策 |

章节不是工具清单，而是从**边界 → 输入 → 历史 → 证据 → 发布**逐层收紧。每章都先看一个失败现象，再建立模型，最后用实践代码或引擎映射验证。

### 前置诊断

不要求先会 C#、C++ 或 Unity/UE。只需：

- 能运行 Python 3.11+、Git 2.x 和基本终端命令；
- 知道文件、目录、进程和退出码的基本含义；
- 如果完全不了解 Git，先在第 3 章的“工作区—暂存区—提交”小实验中补齐。

若下面三句话中有两句无法解释，先读第 1 章的“失败构建”部分，不要急着做主实践：

- 删除 `Library/` 或 `DerivedDataCache/` 后，为什么项目仍应能恢复？
- 为什么一个可执行文件不能证明它来自哪个提交？
- 为什么 `seed=42` 必须出现在失败报告中，而不是只出现在开发者记忆里？

## 一条主实践，贯穿五章

[主实践：可复现 seeded-room 工程](practice.md)把章节知识收束到同一个最小项目。题面、解法、命令、参考代码入口和迁移到 Unity/UE 的说明放在同一页，避免在“实践、解法、代码”之间来回跳转。

实践按三个里程碑推进：

- **A 确定性**：固定 seed，验证行为不变量；
- **B 可重建**：清理产物后重新构建，比较确定性 manifest；
- **C 可诊断**：制造一个有固定 seed 的回归，写最小复现并用 Git 历史定位。

运行代码入口：

- [`game.py`](code/repro-game/src/game.py)：确定性房间生成器；
- [`build.py`](code/repro-game/src/build.py)：清理构建、计算输入哈希并写 manifest；
- [`test_game.py`](code/repro-game/tests/test_game.py)：性质测试和边界测试；
- [`Makefile`](code/repro-game/Makefile)：统一命令入口。

## 练习题

[练习题](assessments.md)采用“先答题，再展开提示/解析”的单页形式。只保留能检查机制、不变量、取舍、诊断和迁移的题，不要求写泛泛的学习感想。

## 版本、来源与边界

正文优先讲 Git、可复现构建和引擎工程中跨版本稳定的原则；涉及 Unity Editor、Package、Unreal Engine、插件、平台 SDK 或 GitHub Actions 版本的命令，只能作为入口示例，实际项目必须按锁定版本复核官方文档。

来源记录保留在课程目录的 `references/` 中，主要用于维护与审计，不作为主学习路径。术语在首次出现的章节中直接解释，不要求额外背诵术语表。
