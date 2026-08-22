# 练习题

做法：先遮住解析，先用纸或心答；再展开“最小提示”和“完整解析”。每题都要求给出可验证证据，而不是只说“应该规范一点”。

### TOOLCHAIN-Q1：工程边界分类

一个 Unity 项目把 `Assets/`、`.meta`、`Library/`、`Packages/`、`Build/`、`Editor.log` 和 `build-manifest.json` 混在一起。请为每项标注类别、是否通常进入版本控制、删除后的恢复方式，并解释为什么“自动生成”不等于“可以忽略”。

<details>
<summary>最小提示</summary>

先按“源、元数据、工具/依赖、缓存、产物、证据”分类，再问删除后是否改变引用或语义。
</details>

<details>
<summary>完整解析</summary>

`Assets/` 通常是源输入，应提交；`.meta` 是维持资产身份和引用的元数据，通常与资产一起提交；`Packages/` 中的项目声明和锁文件是依赖输入，应提交，缓存不应代替锁文件；`Library/` 通常是可再生缓存，不提交，删除后由固定 Editor 和包版本重新导入；`Build/` 通常是产物，不作为源提交，但应上传与提交/构建 ID 绑定的 artifact；`Editor.log` 是诊断证据，按构建/事故需要保留，不应把本机路径和隐私直接公开；`build-manifest.json` 是来源证据，若随 artifact 生成则不一定进源仓库，但必须与产物一同保存。

推理关键是生命周期和语义：`.meta` 虽可能由工具生成，但删除可能改变 GUID 和引用，因此不能按“生成文件”一律忽略；`Library/` 若删除后冷导入仍能恢复，才符合缓存边界。验证包括干净 clone、删除缓存、重新导入、构建和加载关键场景。游戏映射是：资产引用、Addressables/插件、场景加载和包体身份都依赖边界正确。

常见错误：把所有生成文件都忽略；把 Build 当备份；认为 `.gitignore` 能清理历史中的密钥；只验证编辑器打开，不验证冷导入和产物启动。
</details>

### TOOLCHAIN-Q2：可复现性的反例

两次构建使用同一提交、同一 Unity 版本和同一 seed，但 manifest 不同。第一次写入了 `PROJECT_ROOT` 和当前时间，第二次文件列表顺序不同。请指出至少三个独立原因，并给出修复与验证顺序。

<details>
<summary>最小提示</summary>

把“用于比较的确定性字段”和“用于追踪执行的 provenance 字段”分开。
</details>

<details>
<summary>完整解析</summary>

独立原因包括：用户绝对路径随机器变化；当前时间每次不同；文件系统遍历顺序未定义。修复顺序是：先把路径归一化为仓库相对路径，再对文件列表排序，再把时间移到 provenance 区域或从确定性摘要排除。之后用相同提交、同一工具和同一 seed 删除缓存并运行两次构建，比较确定性字段和最终产物；再单独改变 seed、版本和源码，确认差异只出现在预期字段。

边界是：跨平台可执行文件可能不能字节级相同，目标应改为内容或行为等价并声明例外；但不能用这个边界掩盖未排序、绝对路径和当前时间这类本可修复的问题。常见错误是比较时随意忽略所有字段，导致真正的输入差异被隐藏。游戏映射：同一 seed 的房间、掉落和敌人波次应能复现，失败报告应包含 seed、内容版本和生成器版本。
</details>

### TOOLCHAIN-Q3：随机流与回归

一个肉鸽生成器先生成房间，再生成敌人。为了增加视觉抖动，开发者在两者之间加入一次随机调用，结果所有后续房间都变了。请解释机制，并提出一种能降低这种耦合的设计；说明它的代价。

<details>
<summary>最小提示</summary>

共享 RNG 的状态由“调用次数和顺序”决定；改变任何一次消费都会改变后续序列。
</details>

<details>
<summary>完整解析</summary>

共享随机流本质上是一个可变状态机：每次调用推进状态，后续值依赖前面消耗了多少次。因此新增视觉随机调用会改变敌人和房间的随机值。可按 run、room、系统或事件派生独立随机上下文，例如 `Random((run_seed * constant) ^ room_index ^ system_id)`，或把随机事件显式记录后重放。

取舍是：独立流降低跨系统耦合、便于局部复现，但需要定义 seed 派生协议、版本化 system_id，并防止不同系统意外使用同一上下文；完全记录随机事件则提高回放能力，但增加日志/存档体积和兼容成本。验证方法是固定 seed，在加入视觉随机调用前后比较敌人生成；若设计目标是玩法稳定，敌人结果不应改变。游戏映射：回放、玩家 bug 报告、联网确定性和肉鸽种子分享都受此影响。
</details>

### TOOLCHAIN-Q4：共享主线回退

提交 B 引入了错误碰撞规则，已经被多人基于 B 开发。请比较 `revert`、`reset --hard`、`rebase` 和强推，并给出主线修复路径。

<details>
<summary>最小提示</summary>

其他人已经引用 B，所以优先选择不移动共享引用的方案。
</details>

<details>
<summary>完整解析</summary>

主线优先 `git revert B`，产生一个新提交抵消 B，保留历史并让其他人的引用仍有共同基础；随后运行碰撞测试、场景冒烟和 `git diff --check`，再推送。`reset --hard` 会移动本地引用并可能丢工作；若强推远端，会让他人分支失去预期父提交。`rebase` 会重写提交 ID，适合尚未共享的分支整理，不是已共享主线默认回退。强推只有在明确的受保护流程和协作协调下才可能合理。

边界：若 B 含密钥或必须从历史移除，revert 不足，还需凭据轮换和历史清理。常见错误是把 revert 说成删除提交，或只验证编译不验证玩家实际碰撞。验证是确认新提交在 B 之后、坏行为消失、远端没有被重写。游戏映射：代码回退与线上旧 artifact 回滚是两个层次，不能混为一谈。
</details>

### TOOLCHAIN-Q5：资产冲突与恢复

两个分支分别移动同一个 Unity 资产并修改一个 UE 二进制内容包。文本冲突解决后项目能打开，但运行时出现丢引用和旧材质。请设计恢复流程。

<details>
<summary>最小提示</summary>

“文件能解析”不等于“引用和导入语义正确”。
</details>

<details>
<summary>完整解析</summary>

先冻结合并结果，确认两边意图、资产负责人、GUID/引用关系和二进制版本。Unity 侧检查资产与 `.meta` 是否成对移动，做冷导入、引用扫描、关键场景加载和材质/预制体测试；若无法可靠合并，回到一个明确版本并重新应用另一边的意图。UE 侧对二进制内容包不能假设文本三方合并，按团队策略选择锁定/签出、负责人确认或从已知 artifact 恢复，再运行 Automation/加载地图/材质冒烟。

验证必须包括：干净 checkout 获取真实 LFS 对象、删除派生缓存后重新导入、关键引用存在、目标构建包含正确资产、产物启动。常见错误是只看冲突标记、只打开编辑器、把 LFS 当备份。游戏映射是场景、材质、输入映射和插件注册都可能在“无文本冲突”下语义损坏。
</details>

### TOOLCHAIN-Q6：分层门禁

团队说：“Unity/UE 项目太大，CI 只要编辑器能打开就行。”请设计一个成本递增的最小门禁，并指出每层能证明什么、不能证明什么。

<details>
<summary>最小提示</summary>

编辑器打开只覆盖导入的一部分；把失败尽可能提前，把昂贵测试放到需要的分支或夜间矩阵。
</details>

<details>
<summary>完整解析</summary>

最小门禁可以是：1）格式、包锁、插件和配置静态检查；2）脚本/单元/确定性测试；3）资产引用和导入检查；4）Development 构建；5）产物启动、加载最小场景和关键日志检查；6）受保护分支或夜间任务执行 Shipping/平台矩阵。每层都返回明确退出码并上传 manifest、日志和报告。

编辑器打开能证明部分项目导入路径可用，不能证明目标平台 SDK、插件、输入映射、构建链接、产物启动或随机内容不变量。边界是成本：不一定每个 PR 都跑所有平台 Shipping，但不能因此删除低成本门禁。验证方法是删除缓存运行一次、故意移除插件或场景引用，确认 CI 非零退出并保留证据。游戏映射：让玩家发现问题前在 Addressables、场景、输入、敌人生成和包体层失败。
</details>

### TOOLCHAIN-Q7：seed 最小复现与 bisect

只有 `seed=7` 的第 3 个房间没有出口。请设计从事故报告到修复的完整诊断链，并说明什么时候不能直接运行 `git bisect`。

<details>
<summary>最小提示</summary>

把整局缩成 `generate_room(seed=7, room_index=3)`，再确认 good/bad 提交的测试判定稳定。
</details>

<details>
<summary>完整解析</summary>

报告先固定提交/build ID、工具/平台、内容版本、seed、room index、期望不变量和实际结果。然后写最小测试，断言出口存在并在失败消息中包含 seed/room。日志可包含 generator version、随机上下文、步骤计数和构建身份。只有已知 good/bad、所有中间提交可构建或可判定、测试无时间/网络/脏缓存漂移时才运行 bisect；不可判定提交用 skip。

修复后保留该回归测试，并运行其他 seed 的通用性质测试，避免只为 seed=7 写特殊分支。若生成器允许多种合法地图，断言可达性、出口和无重叠等性质，不硬编码唯一布局。常见错误是用截图、整局人工操作或当前时间 seed；验证是同一命令能在干净 checkout 重复失败和通过。游戏映射：房间、掉落、敌人波次和回放都应保留最小输入。
</details>

### TOOLCHAIN-Q8：cache、artifact 与权限

有人建议“把 Unity `Library/`、UE `DerivedDataCache/` 当 artifact 上传，并给所有 job 写权限，方便排错”。请指出问题并给出安全的最小设计。

<details>
<summary>最小提示</summary>

问：缓存是否可删除？它是不是玩家要运行的交付品？每个 job 是否真的需要写权限？
</details>

<details>
<summary>完整解析</summary>

缓存是可丢弃、可重建的加速数据，不是发布 artifact；上传它会放大存储、带宽、路径泄露和错误语义。正确 artifact 应是本次构建的包、manifest、测试报告、日志和必要符号。所有 job 写权限违反最小权限，来自 fork 的不可信代码可能获得发布或修改仓库能力。

安全设计：默认 `contents: read`；测试/构建 job 使用缓存但只上传本次 artifact；受保护分支的独立 deploy job 才拥有 Pages/发布权限；秘密通过平台 secret 注入且不打印；第三方 action 固定并审查。验证 workflow 权限块，确认测试 job 无写权限仍能通过，下载 artifact 检查没有秘密且包含 build ID、提交、目标平台和报告。游戏映射：缓存加速导入，artifact 才是可回滚包。
</details>

### TOOLCHAIN-Q9：从工作区到提交，命令到底改变了什么

你在个人分支上同时做了两个改动：`src/combat.py` 修复伤害计算，`README.md` 增加说明。请设计一组命令，只提交伤害修复，并逐条说明每个命令读取/改变哪个状态；最后证明提交没有包含 README 改动。

<details>
<summary>最小提示</summary>

先用 `status` 和 `diff` 看现状，再用路径限定或 `add -p` 选择暂存内容，提交前检查 `diff --cached`，提交后检查 `show` 和 `status`。
</details>

<details>
<summary>完整解析</summary>

一种安全流程是：

```bash
git status --short
git diff -- src/combat.py README.md
git add src/combat.py
git diff --cached
git commit -m "Fix combat damage calculation"
git show --stat --oneline HEAD
git status --short
```

第一步读取工作区、暂存区和 `HEAD`，不修改文件；第二步比较工作区与暂存区，只观察两个路径；`git add src/combat.py` 只把该路径当前内容复制到暂存区，不上传远端，也不影响 README；`git diff --cached` 比较暂存区与 `HEAD`，是“下一次提交会包含什么”的直接证据；`commit` 根据暂存区创建新的本地提交节点，未暂存的 README 不会进入该节点；`show` 读取刚创建的提交；最后的 `status` 应显示 README 仍是未暂存修改，或者在没有其他变化时显示干净。

如果 `src/combat.py` 内还混有不应提交的调试代码，应改用 `git add -p src/combat.py`，按块选择，而不是盲目 `git add .`。若误暂存 README，使用 `git restore --staged README.md`，它只改变暂存区并保留 README 工作区内容。验证不能只看提交信息，必须检查 `git show HEAD --name-only` 或 `git show --format= --name-only HEAD` 的文件列表。游戏映射是：把“规则修复”和“文档/调试变化”分开，便于 review、回滚和定位版本差异。
</details>

### TOOLCHAIN-Q10：分支、同步与 PR 合并策略

`main` 已推进，而你的 `feature/dash` 分支落后且有 3 个本地提交。请给出一条安全的同步方案，并比较 `merge` 与 `rebase`；说明什么时候允许 `push --force-with-lease`，以及 PR 合并后为什么还要重新运行主线构建。

<details>
<summary>最小提示</summary>

先用 `fetch` 更新远端信息，再在自己的分支整合 `origin/main`。区分“修改自己的未共享分支历史”和“修改别人可能已经基于的共享历史”。
</details>

<details>
<summary>完整解析</summary>

可采用以下流程：

```bash
git switch feature/dash
git status
git fetch origin
git log --oneline --graph --decorate --all
git rebase origin/main
# 解决冲突后：git add <resolved-path> && git rebase --continue
# 若发现方向错了：git rebase --abort
git push --force-with-lease origin feature/dash
```

`fetch` 只更新本地的远端跟踪引用（如 `origin/main`），不改当前工作区；`rebase origin/main` 把本地 3 个提交在新基底上重放，因此会生成新的提交 ID；它适合个人尚未被他人基于的 feature 分支，且需要先确认工作区干净。`--force-with-lease` 是因为远端分支原本已有旧提交线，重写后普通 push 会被拒绝；它会在覆盖前检查远端仍是自己上次看到的状态，比 `--force` 多一道保护。若分支已被多人共享、作为发布分支或有人在其上继续开发，不应擅自 rebase/强推，应改用 `git merge origin/main`，普通 `git push`，或先与团队约定。

无论选 merge 还是 rebase，都要重新运行测试和资产/构建门禁。PR 分支的绿色结果只证明当时那个提交和环境通过；主线在此期间可能加入输入映射、包版本或资源变化，真正交付的是主线整合后的 artifact。团队应在受保护的主线上重建，记录提交、工具版本、目标平台和 build ID，再由 QA 验证该 artifact，而不是把开发者本机产物直接当正式版本。游戏映射是冲刺、输入、动画和场景资源往往跨文件协作，分支历史整合与冷构建必须一起验证。
</details>

### TOOLCHAIN-Q11：从 PR 到发布候选与回滚

一个“增加冲刺能力”的 PR 已通过单元测试，但主线集成后发现某平台输入映射缺失。请写出从发现到修复发布的处理顺序，明确程序、QA、构建/发行和负责人各自拥有的状态；并区分 `git revert`、重新发布旧 artifact 与数据库/存档回滚。

<details>
<summary>最小提示</summary>

先保护正式版本和证据，再决定是代码回退、产物回退还是数据迁移修复；它们不是同一个按钮。
</details>

<details>
<summary>完整解析</summary>

先停止继续推广该候选版本，记录受影响的提交、build ID、平台、输入配置版本、日志和复现步骤。QA 将问题标记为发布阻断并确认最小复现；程序检查 PR 是否只覆盖逻辑而遗漏平台配置，补上输入映射和回归测试；构建/发行人员从固定提交重新生成候选 artifact，不能在发布机器上手工改包；负责人根据风险决定取消候选、回退旧版本或等待修复候选。修复候选必须再次经过低成本 CI、目标平台构建、产物启动、输入冒烟和 QA 验收，随后才进入正式发布。

`git revert <bad-commit>` 在共享分支上创建一个“反向变化”新提交，不重写他人历史，适合代码层撤销但仍需重新构建和测试；重新发布旧 artifact 是部署层回退，使用已经验证过的旧包，适合新包本身有问题且旧包与服务/存档兼容；数据库或玩家存档回滚是数据层操作，可能造成进度丢失或协议不兼容，必须有备份、迁移策略、权限审批和演练，不能用 `git reset` 代替。若发布分支做了修复，还要把同一修复合回主线并保留回归测试，避免下一次发布重新引入。游戏映射是“逻辑可用”不等于“玩家在目标平台能操作”，发布门禁必须覆盖平台输入、资产、存档和网络接缝。
</details>
