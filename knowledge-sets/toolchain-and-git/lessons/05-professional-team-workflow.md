# 5. 专业团队怎样协作：从任务到正式版本

“大家各建一个分支，最后合并”不是完整协作流程。真正需要控制的是：任务是否足够小、谁拥有状态、什么时候验证、谁能合并、进入主线后如何成为可发布版本，以及出事故后如何恢复。

下面描述的是公开且常见的工程模式，不声称所有公司使用同一流程。团队会按规模、平台认证、二进制资产比例和发布节奏调整。

## 5.1 一条变化的完整生命周期

```text
需求/缺陷
→ 可验收任务
→ 领取与所有者
→ 短分支/受控主干开发
→ 本地测试与小提交
→ push + PR/MR
→ 自动检查 + 同行评审
→ 合并
→ 集成构建与更大范围测试
→ 发布候选
→ 平台/QA/性能/兼容验证
→ 正式 artifact
→ 监控、热修复或回滚
```

每一阶段都要留下可验证证据，而不是只更新“完成”状态。

## 5.2 个人如何管好一个任务

一个可交付任务应写清：

- **问题与玩家影响**：例如 seed 7 的第三个房间可能没有出口；
- **范围**：允许修改生成器和测试，不顺便重写存档系统；
- **验收标准**：所有房间恰有一个出口，已有 seed 行为兼容或明确版本化；
- **依赖/风险**：是否修改共享场景、协议、存档 schema 或二进制资产；
- **验证命令**：单元测试、场景冒烟、目标平台构建；
- **回滚方式**：revert 是否足够，是否涉及数据迁移。

开发者领取任务后：

1. 从最新受保护主线创建短分支；
2. 先复现问题，建立失败测试或明确观察步骤；
3. 用单一目的提交逐步实现；
4. 每次提交前看 staged diff，运行相关低成本测试；
5. 频繁 fetch，避免与主线长期分叉；
6. 尽早开 Draft PR，让依赖和接口问题暴露；
7. 不把未完成核心逻辑藏在巨大提交或私人分支中。

## 5.3 PR/MR 应让评审者回答什么

一个好的 Pull Request/Merge Request 不是“请看代码”，而是一个可审查变化包：

```text
标题：修复 seeded room 出口不变量
问题：seed=7, room=3 无出口，玩家无法继续
方案：将出口选择从共享随机流分离，并保证 exactly-one
范围：生成器 + 回归测试；不修改存档 schema
验证：unit tests；1000 seeds 性质测试；Development 构建启动
风险：旧回放若依赖生成顺序，需要 contentVersion 保护
回滚：revert PR merge commit / 部署上一 artifact
```

评审通常分多层：

- **正确性**：规则和边界是否正确；
- **可维护性**：命名、状态所有者、依赖、错误路径；
- **测试**：失败能否复现，测试是否验证性质而非实现细节；
- **性能/平台**：是否影响帧预算、内存、包体或平台 SDK；
- **内容/设计**：玩法是否符合设计意图；
- **安全/数据**：密钥、玩家数据、网络信任边界和许可证。

作者负责回应、修改和解释；评审者负责指出可操作问题，不应借 PR 无边界重写作者的整个方案。

## 5.4 CI 如何配合评审

PR 上的低成本门禁通常按失败成本递增：

```text
格式/静态检查
→ 单元与确定性测试
→ 资产引用/导入检查
→ Development 构建
→ 产物启动与最小场景冒烟
```

更昂贵的平台矩阵、长时间玩法、性能基线和兼容测试可以在主线、夜间或发布候选上运行。CI 只自动证明它检查过的内容；绿色不等于“没有 bug”。

分支保护常要求：

- 必需检查通过；
- 至少一名或多名合适所有者批准；
- 未解决对话清零；
- 分支没有落后到无法安全整合；
- 作者不能绕过关键发布权限。

## 5.5 三种常见主线策略

### 短分支 + PR（常见于小中型团队）

从 `main` 建短分支，PR 通过后合并。优点是简单、评审清晰；风险是分支过大或环境不足时，问题在主线才暴露。

### Trunk-based development

开发者频繁向主干提交小变化，使用 feature flag、兼容接缝和强自动化保持主干可发布。它不是“所有人随便 push main”，而是要求更小批次、更快检查和严格主干纪律。

### 发布分支模式

主线继续开发，新版本从 `release/x.y` 稳定；只接受阻断级修复，修复需要合回主线，避免两条历史永久漂移。适合平台认证、长 QA 周期或同时维护多个版本，但分支越多，修复同步和测试矩阵成本越高。

完整 Git Flow 的长期 `develop`、release、hotfix 分支并非所有项目都需要。选择最少且足够的分支，明确每类分支允许进入什么变化。

## 5.6 合并策略如何选

| 策略 | 主线结果 | 优点 | 代价/适用边界 |
|---|---|---|---|
| merge commit | 保留功能分支提交和合并节点 | 能看出集成边界，整 PR 可回退 | 历史节点较多 |
| squash merge | PR 压成一个提交 | 主线简洁、PR 级回退方便 | 丢失分支内细粒度历史 |
| rebase merge | 提交线性重放到主线 | 保留单个提交且线性 | 提交 ID 改变，要求提交本身质量高 |

不要只按美观选择。若团队主要以 PR 为审查和回滚单位，squash 可能合适；若需要保留逐步实现与作者关系，可用 merge/rebase。策略应统一并写进仓库规则。

## 5.7 合并后如何融入正式版本

合并到主线只是“进入集成候选”，不是自动成为玩家版本：

1. 主线 CI 重新构建，不盲信 PR 分支旧结果；
2. 产生带提交、工具版本、目标平台和 build ID 的 artifact；
3. 集成环境运行跨系统测试：输入、存档、资源、网络、性能；
4. 选定发布候选（release candidate, RC），冻结或限制变化；
5. QA/设计/平台负责人验证候选 artifact，而不是开发者本机目录；
6. 正式发布复用同一已验证 artifact，不在发布按钮处重新编译一份；
7. 标签、变更记录、符号、manifest 和回滚目标一起保存；
8. 发布后观察崩溃、性能、服务指标和玩家阻断问题。

## 5.8 热修复与回滚

事故发生时先保护玩家和证据：

```text
停止继续发布
→ 确认受影响版本/build ID
→ 保存日志、dump、seed、内容版本
→ 决定回滚旧 artifact 还是做最小 hotfix
→ 在受控分支修复并跑缩小后的门禁
→ 发布并监控
→ 将修复同步回主线和仍维护的发布分支
→ 保留回归测试和事故结论
```

代码 `git revert`、部署旧 artifact、回滚存档/数据库迁移是不同操作。涉及玩家数据或协议时，必须先检查向后兼容和备份，不能只替换可执行文件。

## 5.9 游戏团队的角色接缝

- 程序：规则、运行时、测试、性能和工具；
- 技术美术/内容：资产源、导入规则、预算和引用；
- 设计：验收意图、数值/关卡行为和可调参数；
- QA：风险覆盖、复现、平台矩阵和发布候选验证；
- 构建/发行：工具链、签名、artifact、权限和部署；
- 制作/负责人：范围、优先级、阻断标准和发布决策。

角色名称会变化，但每个关键状态必须有所有者、可修改者、生命周期和失败路径。

## 5.10 从标签到同一份发布字节

第 3–4 章证明的是 Git 操作，不是托管 PR 或真实平台发行。这里继续小情景，用源码 tar 充当“教学 artifact”，检验：候选来自哪次提交、检查的是哪份字节、主线后来变化是否影响旧候选。`git archive` 只包含所选提交的跟踪内容，不含工作区未提交文件；它也不会替你收齐子模块、LFS 实体或生成可执行游戏。

<!-- git-scenario: 05 -->
```bash
# Simulate promotion of immutable bytes, not an actual game/platform release.
cd "$git_lab/work"
test -z "$(git status --porcelain)"
git tag -a v0.1.0-lab -m "Validated teaching candidate"
mkdir "$git_lab/artifacts"
git archive --format=tar --output="$git_lab/artifacts/rc.tar" v0.1.0-lab
python3 - "$git_lab/artifacts" <<'PYTEST'
from pathlib import Path
import hashlib
import shutil
import sys
import tarfile
root = Path(sys.argv[1])
with tarfile.open(root / "rc.tar") as archive:
    stream = archive.extractfile("rules.txt")
    assert stream is not None
    assert stream.read() == b"damage=15\ndebug=0\ninvulnerability=1\n"
    assert "input.txt" in archive.getnames()
shutil.copyfile(root / "rc.tar", root / "released.tar")
assert hashlib.sha256((root / "rc.tar").read_bytes()).digest() == hashlib.sha256((root / "released.tar").read_bytes()).digest()
PYTEST
# Later main changes; the already checked artifact must NOT silently change.
printf 'damage=99\ndebug=0\ninvulnerability=1\n' > rules.txt
git add rules.txt && git commit -m "Simulate a later unvalidated change"
git show v0.1.0-lab:rules.txt
python3 - "$git_lab/artifacts" <<'PYTEST'
from pathlib import Path
import sys
root = Path(sys.argv[1])
assert (root / "rc.tar").read_bytes() == (root / "released.tar").read_bytes()
PYTEST
git status --short
printf 'Temporary lab retained for inspection: %s\n' "$git_lab"
```

Python 验证规则和输入文件后，把同一 rc.tar 复制为 released.tar 并比较 SHA-256。哈希相同支持本次传递未改变字节的检查（末段还直接逐字节比较），但不是数学上的无碰撞证明，不证明游戏正确、内容安全或来源可信；真实发布应在目标平台验证同一 artifact。本例没有运行网络部署、签名和商店提交流程。

现在若新提交出问题，“回滚部署”是重新选用已经保存和验证的旧 artifact；“代码回退”则是 revert 并按新提交重新构建候选。若涉及数据库/存档 schema，需要独立兼容计划，不应根据这份源码 tar 宣布数据可回滚。临时目录保留供检查；只在确认它确实是本次创建且无需要保留的内容后自行清理，不复制递归删除命令到真实项目。

## 本章验收：模拟一次专业交付

为“增加玩家冲刺”写一页交付说明：任务范围、分支名、3 个以内计划提交、测试、PR 描述、评审角色、CI 门禁、合并策略、发布候选验证和回滚方案。然后回答：

- 如果冲刺代码通过单测但场景输入映射遗漏，在哪一层发现？
- 如果发布分支修复了崩溃，如何防止主线再次引入？
- 如果二进制场景冲突无法合并，谁决定保留哪份，如何验证？

第 6 章开始把源码、资产、工具、缓存和发布产物放进构建模型，解释团队到底在验证什么。


## 本章练习

### T05-Q1：热修复为何不能只留在发布分支

**题型**：提交图推演与故障诊断
**作答产物**：提交图或引用移动表、缺陷原因和不改写共享历史的修复。

发布分支修好空存档崩溃，但 main 正在重构加载器。同事建议直接把 release 整条分支 merge 到 main。哪些证据决定可否这样做？怎样防止下一版复发？

<details><summary>讲解、判定与验证</summary>

先找修复的最小原因与回归输入，再检查 release 是否夹带冻结配置、临时版本号或旧接口。可迁移的独立修复可以 cherry-pick -x；接口已重构则按同一不变量在 main 重做修复，不能机械粘贴补丁。让同一个损坏存档回归在两条维护线上通过，分别验证候选包。常见错误是把“补丁应用成功”当成新加载器已修好，或只修改线上包不回到版本历史。存档崩溃与其他长期维护分支都需要明确回移所有者。
</details>

### T05-Q2：把“可合并”与“可发布”分开

**题型**：发布门禁矩阵与故障定位
**作答产物**：补全门禁表；给出阻断层、保留证据和恢复动作。

某 PR 修改输入映射。现有证据如下：

| 阶段 | 代码单测 | 配置 schema | Windows 键鼠 | Steam Deck 手柄 | artifact 身份 | 结果 |
|---|---:|---:|---:|---:|---|---|
| PR | 通过 | 通过 | 未运行 | 未运行 | 无 | ? |
| 集成构建 | 通过 | 通过 | 通过 | 失败：缺少动作绑定 | `build-184` | ? |
| 发布候选 | 未重新测试 | 未重新测试 | 未运行 | 未运行 | 发布脚本重新构建 `build-185` | ? |

回答：

1. 每行最多能证明“可评审、可合并、可构建、可发布”中的哪一级；
2. 最早应在哪一层阻断，失败时保留哪些日志/manifest；
3. 即使修复 Steam Deck 配置，为什么不能直接发布 `build-185`；
4. 设计一条确保“验收的就是上线的那个包”的最小链路。

<details><summary>讲解、判定与验证</summary>

PR 行只证明代码与 schema 达到可评审/可能可合并门槛，不能证明目标平台行为。集成构建生成了可识别的 `build-184`，但 Steam Deck 冒烟失败，所以应在目标平台集成门禁阻断并保存失败退出码、设备/运行时版本、输入配置摘要、commit、构建工具版本、日志和 artifact hash。发布候选行重新构建了 `build-185` 且没有继承测试证据，身份也与验收包不同，因此不可发布；“同一源码”不能证明二进制、资源导入、签名和环境完全相同。

最小链路可以是：PR 静态检查/单测 → 合并后一次受控构建 → 为 artifact 写不可变 ID 与 manifest → Windows/Steam Deck 都下载并测试同一 hash → 将同一 artifact 提升为 release candidate → 发布系统只做签名/封装且记录派生 hash，不重新编译游戏内容。修复后必须产生新 artifact 并重跑失败平台及受影响回归。

评分点：区分合并资格与发布资格；最早在能观察平台缺陷的门禁阻断；保留可复现输入和产物身份；禁止用“重新构建应该一样”替代 artifact promotion。边界：平台签名可能必然产生派生包，此时必须记录从已测包到签名包的受控转换并做安装/启动冒烟。游戏映射：输入、分辨率、内容包、存档迁移与服务器协议都可能在代码 PR 绿灯后才暴露，发布链必须把平台证据绑定到玩家实际拿到的包。
</details>

## 来源与适用范围

核对日期：2026-09-07。使用本地 Git 2.55.0 运行章节情景；命令契约对照 Git 官方手册（[archive](https://git-scm.com/docs/git-archive), [cherry-pick](https://git-scm.com/docs/git-cherry-pick), [revert](https://git-scm.com/docs/git-revert)）。这些是教学工作流，不代表任何公司的内部流程。
