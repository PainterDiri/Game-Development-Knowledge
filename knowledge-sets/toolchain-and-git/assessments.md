# 题目与折叠答案

默认流程：先心答或纸答；卡住时只展开最小提示；最后展开完整解析并重新解释。题目只保留能检验边界、机制、诊断和迁移的高价值问题。

### TOOLCHAIN-Q1 · 源、缓存、产物和元数据

一个 Unity 项目提交了 `Assets/`、`ProjectSettings/`、`Packages/`、`Library/` 和 `Build/`。请分类，并解释为什么“删掉后能重建”比“大家通常这么做”更重要。再给出 UE 的对应思路。

<details>
<summary>最小提示</summary>

问：它是人维护的输入，还是可由提交中的输入再生成？`.meta` 为什么不能和 `Library/` 等同？
</details>

<details>
<summary>完整解析</summary>

`Assets/` 是主要内容输入，资产旁的 `.meta` 是稳定引用所需的元数据；`ProjectSettings/` 与 `Packages/` 是项目配置和依赖声明；`Library/` 是导入缓存，通常可删除后重新生成；`Build/` 是产物目录，通常不作为源提交。关键不是背目录表，而是做冷启动验证：在干净 checkout、安装声明版本的 Unity 和平台模块后，删掉 `Library/` 是否还能导入和构建。

UE 的思路相同：提交 `.uproject`、源码、`Config/`、内容和插件配置；通常不提交 `Binaries/`、`Intermediate/`、`Saved/`、`DerivedDataCache/` 等可再生目录。例外必须写进项目约定并经过冷构建验证。

**推理**：删掉后不能重建的“缓存”其实是未声明输入；提交缓存会放大仓库、增加冲突并掩盖环境缺失。`.meta` 参与资产引用稳定性，因此不能简单忽略。

**边界**：具体 Unity/UE 版本、插件和团队策略可能有例外；例外不应靠习惯，而应靠恢复实验确认。

**常见错误**：把所有二进制都提交；忽略 `.meta`；把“编辑器能打开”当作构建成功。

**验证方法**：复制干净 checkout，删除生成目录，运行最小测试/构建，保存日志和 manifest。

**游戏映射**：场景 GUID 丢失会让 prefab 引用断裂；错误提交缓存会让肉鸽房间在另一台机器失效。
</details>

### TOOLCHAIN-Q2 · 环境与可复现性

两次相同提交、相同 seed 的构建中，`game.py` 相同，但 `build-manifest.json` 一次写入当前时间，一次写入绝对工作区路径。这个构建能否称为可复现？如何修复，同时保留调试信息？

<details>
<summary>最小提示</summary>

区分“确定性输出”和“来源追踪信息”。不是所有有价值的信息都必须参与确定性比较。
</details>

<details>
<summary>完整解析</summary>

如果把整个 manifest 当成确定性构建输出，两次内容不同，就不能声称它完全可复现。修复方式是把字段分层：`deterministic` 只放提交、工具版本、seed、相对输入路径、哈希和配置；`provenance` 放构建开始时间、CI run ID 和 runner 信息，并明确它是非确定元数据。绝对路径应归一化为仓库相对路径或稳定标识，避免泄露用户目录。

**推理**：可复现要求相同输入得到等价确定结果；来源追踪要求知道“哪一次构建、哪台 runner”。两者可以通过字段边界并存，不能把非确定字段伪装成内容哈希的一部分。

**边界**：若发布系统必须对整个文件做哈希，可只对 deterministic 区域计算内容哈希，另存 provenance，或定义明确的比较器。不可声明地忽略差异不合格。

**常见错误**：把当前时间作为随机种子；只删时间却保留绝对路径；说“manifest 不重要所以可以不同”。

**验证方法**：两次构建分别比较 deterministic/provenance；改变 seed 或版本，确认只发生预期变化。

**游戏映射**：肉鸽报告要保留 run seed 和内容版本；构建时间用于追踪发布，但不应改变房间生成。
</details>

### TOOLCHAIN-Q3 · Git 共享历史回退

提交 B 已推送并被其他人拉取，随后发现玩家无法移动。为什么不应优先 `reset --hard` 后强推？比较 `revert`、`merge` 和 `rebase` 的作用，并给出最小验证命令。

<details>
<summary>最小提示</summary>

共享历史的约束是：其他人已经引用 B。修复目标是恢复行为，同时保留可追踪历史。
</details>

<details>
<summary>完整解析</summary>

不应优先强推，因为它会移动远端引用并改写他人已经基于 B 工作的历史，造成丢提交和协作分叉。`git revert B` 产生新提交 C，抵消 B，适合主分支安全回退；`merge` 把两条历史合并，不是专门的回退命令；`rebase` 改写提交父关系，适合尚未共享的本地整理，不应作为已共享主线的默认修复。

```bash
git pull --ff-only
git revert <bad-commit>
python3 -m unittest discover -s knowledge-sets/toolchain-and-git/code/repro-game/tests -v
git diff --check
git push
```

**边界**：涉及密钥或必须从历史移除时，revert 不够，还要做历史清理和凭据轮换。

**常见错误**：把 revert 说成删除提交；冲突时直接 reset；只验证编译不验证玩家移动。

**验证方法**：确认 C 在 B 之后、回归测试通过、远端没有被强制改写。

**游戏映射**：发布线优先回滚到已验证 artifact；主线用新提交撤销坏的输入或碰撞改动。
</details>

### TOOLCHAIN-Q4 · Unity/UE CI 门禁

团队说：“Unity/UE 项目太大，CI 不需要跑游戏，只要编辑器能打开即可。”请从工具链不变量、测试层次和失败成本三个角度限定或反驳这句话，并设计最小门禁。

<details>
<summary>最小提示</summary>

编辑器打开只覆盖导入路径，不覆盖目标平台构建、关键资产、插件、输入映射和产物启动。
</details>

<details>
<summary>完整解析</summary>

打开编辑器不能证明版本控制中的源、元数据、依赖、SDK 和构建命令能产生产物；测试层次至少应包含脚本/单元测试、资产引用/导入检查、Development 构建和目标平台冒烟。越晚发现缺场景、插件或输入映射，返工成本越高。

“每个 PR 都跑所有平台的完整 Shipping 构建”可以被成本约束，但不能省略低成本门禁：

1. 干净 checkout，锁定 Unity/UE 和依赖；
2. 快速单元/自动化测试；
3. 无交互构建测试配置；
4. 启动或加载最小场景，检查退出码和关键日志；
5. 上传 manifest、日志、测试报告；夜间或 release job 再跑完整矩阵。

**验证方法**：删除缓存后运行门禁，故意删一项依赖，确认非零退出码阻断。

**游戏映射**：Addressables/场景引用、UE 插件、输入映射和肉鸽内容表都应在玩家发现前失败。
</details>

### TOOLCHAIN-Q5 · Seed 回归定位

只有 `seed=7` 的第 3 个房间没有出口。请设计从报告到修复的诊断路径，必须包含最小复现、日志字段、`git bisect` 的前提和最终回归测试。

<details>
<summary>最小提示</summary>

把整局缩成 `generate_room(seed=7, room_index=3)`，再问 good/bad 提交能否稳定判定。
</details>

<details>
<summary>完整解析</summary>

1. 提取提交、平台/工具、内容版本、seed、房间索引和输入序列；
2. 写最小复现并断言出口存在；
3. 日志记录 seed、room index、generator version、入口/出口坐标、随机流状态/步骤计数和 build ID；
4. 区分算法、资产、工具、缓存和输入数据；
5. 只有中间提交可构建、测试稳定、工作树干净、外部依赖固定时，才运行 `git bisect`；不可判定提交用 `skip` 并降低结论强度；
6. 修复后保留 `seed=7, room=3` 回归测试，并检查其他 seed 的不变量。

如果生成算法允许多解，测试应断言可达、出口存在、无重叠等性质，而不应硬编码唯一地图。

**游戏映射**：房间、掉落、敌人波次都应保留最小 seed；不要要求玩家上传整台机器。
</details>

### TOOLCHAIN-Q6 · CI 证据与权限

CI 中有缓存步骤和 artifact 上传步骤。有人建议“把缓存当构建产物上传，并给所有 job 写权限，方便排错”。指出至少三处问题，并给出更安全的最小权限/证据策略。

<details>
<summary>最小提示</summary>

问三个问题：缓存是否可删除？它是不是交付品？每个 job 是否真的需要写权限？
</details>

<details>
<summary>完整解析</summary>

缓存是加速数据，可失效、可重建，不应冒充发布 artifact；上传缓存会放大存储、泄露路径/依赖并让人误以为它是可运行产物。所有 job 写权限违反最小权限原则，来自 fork 的不可信代码可能获得生产能力。排错应依靠 manifest、日志、测试报告、崩溃转储和符号索引，而不是扩大权限。

更安全的策略是：默认 `contents: read`；构建 job 使用缓存但只上传本次构建的 artifact；受保护分支的独立 deploy job 才拥有 Pages/发布权限；秘密通过平台 secret 注入且不打印；第三方 action 固定并审查版本。

**验证方法**：检查 workflow 权限块；确认测试 job 无写权限仍能完成；下载 artifact 检查没有秘密且包含构建 ID、manifest、日志和报告。

**游戏映射**：Unity `Library/`、UE `DerivedDataCache/` 只加速；构建包、符号和测试报告必须可追踪、可下载、可回滚。
</details>
