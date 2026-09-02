# 4. 合并、变基、冲突与恢复：不同历史怎样重新连起来

两位开发者从同一个提交开始：一人修改玩家冲刺，另一人升级输入配置。Git 能合并文本，但它不知道“新输入映射是否仍然触发冲刺”。所以集成包含两层：

1. **历史与文件层**：提交图能否连接、文本冲突能否解决；
2. **语义层**：游戏行为、资产引用、构建和测试是否仍正确。

## 4.1 `merge`：保留两条历史

```bash
git switch main
git merge feature/player-dash
```

- 若 `main` 没有新提交，Git 可以 fast-forward，直接移动引用；
- 若两边都前进，Git 做三方合并并创建有两个父节点的 merge commit；
- merge 不重写已有提交 ID，适合整合已共享历史；
- 文件无冲突不等于行为无冲突，仍要测试。

团队若希望 PR 永远留下一个明确合并节点，可使用 `--no-ff` 或平台的 merge commit 策略；若希望主线更紧凑，可使用 squash merge。选择要围绕审查、回滚和发布，而不是图看起来是否“漂亮”。

## 4.2 `rebase`：把提交重放到新基底

```bash
git switch feature/player-dash
git fetch origin
git rebase origin/main
```

rebase 会为每个重放提交创建新提交，所以 ID 改变。适合：

- 个人功能分支尚未被别人基于其开发；
- 合并前整理“小修复”“补测试”等提交；
- 团队明确采用线性历史。

不适合直接重写共享主线。发生冲突时：

```bash
git status
# 编辑并验证冲突文件
git add <resolved-files>
git rebase --continue
# 或放弃整个变基
git rebase --abort
```

交互式 `git rebase -i <base>` 可以重排、合并、修改个人提交，仍属于历史重写。

## 4.3 `cherry-pick`：复制特定变化

```bash
git cherry-pick <commit>
```

它把某个提交的补丁应用到当前分支并创建新提交。适合把一个独立修复移入发布分支；不适合长期代替正常合并，否则同一逻辑会以多个提交身份存在，后续合并更难推理。

## 4.4 `revert`、`reset` 与 `restore` 不解决同一问题

| 命令 | 主要改变 | 是否新增提交 | 共享历史建议 |
|---|---|---:|---|
| `restore` | 文件在工作区/暂存区的内容 | 否 | 用于未提交文件，先确认会不会丢工作 |
| `revert` | 新建一个抵消旧提交的变化 | 是 | 共享主线默认安全选择 |
| `reset --soft` | 移动当前分支，保留暂存区和工作区 | 否 | 仅整理未共享提交 |
| `reset --mixed` | 移动分支并重置暂存区，保留工作区 | 否 | 本地重新选择提交内容 |
| `reset --hard` | 分支、暂存区、工作区一起回退 | 否 | 可能丢未提交工作，不用于共享历史 |

共享主线出现坏提交时通常：

```bash
git switch main
git pull --ff-only
git revert <bad-commit>
python3 -m unittest discover -s tests -v
git push
```

`revert` 不删除历史中的秘密。若提交过凭据或私人数据，需要立即轮换、停止使用，并按仓库政策清理历史和缓存。

## 4.5 `reflog`：找回移动过的本地引用

```bash
git reflog
git show HEAD@{1}
git branch rescue/lost-work <commit>
```

reflog 记录本地引用近期移动，可找回误 reset 或误删分支前的提交。它不是远端备份，也不是永久保存策略；发现错误后尽快建立恢复分支并验证内容。

## 4.6 冲突处理：先恢复意图，再消除标记

文本冲突流程：

```bash
git status
git diff --name-only --diff-filter=U
# 阅读双方提交和测试，手工恢复正确意图
git diff --check
git add <resolved-files>
# merge: git commit
# rebase: git rebase --continue
```

不要机械选择 `ours` 或 `theirs`。两边可能各自只完成了一半正确逻辑。

### 游戏资产冲突

Unity 场景、预制体、`.meta`/GUID，Unreal 二进制资产和大型源素材可能无法可靠三方合并。常用控制：

- 把场景拆成较小可独立负责的对象/子关卡；
- 文本化可审查配置，但仍运行导入和引用检查；
- 对不可合并二进制使用锁定/签出和明确资产负责人；
- Git LFS 解决大对象存储的一部分问题，不替代锁定、备份、配额和恢复演练；
- 冲突解决后删除派生缓存做冷导入，加载关键场景并构建冒烟。

## 4.7 `bisect`：用可判定测试二分回归

```bash
git bisect start
git bisect bad
git bisect good <known-good-commit>
git bisect run python3 -m unittest discover -s tests -v
git bisect reset
```

前提：有已知 good/bad，测试稳定返回退出码，中间提交可构建或能 `skip`。如果测试依赖当前时间、网络、脏缓存或人工判断，先缩小为稳定回归，否则二分会给出错误信心。

## 本章决策口诀

- 合并已共享历史：优先 merge；
- 整理个人未共享历史：可 rebase；
- 把独立修复带到另一分支：cherry-pick，但记录来源；
- 共享主线回退：revert；
- 本地误操作恢复：先停手，看 status/reflog；
- 文件冲突结束后：必须测试语义和资产引用。

第 5 章把这些操作放进完整团队流程：任务、PR、评审、CI、发布候选和正式版本。


## 本章练习

### T04-Q1：选择恢复命令

共享 main 上的坏提交已被他人拉取；本地未共享分支误 reset。分别选择命令。

<details><summary>最小提示</summary>

共享历史与个人未共享历史的答案不同。
</details>

<details><summary>讲解与验证</summary>

共享 main 用 `git revert` 创建抵消提交，不重写历史；个人误 reset 用 `git reflog` 找旧 HEAD，再建 rescue 分支；`git reset --hard` 可能丢未提交工作。merge/rebase 冲突都要 `status`、解决、`git diff --check`、测试。游戏映射：发布回滚还要重新构建 artifact，不能只改 Git 指针。
</details>

### T04-Q2：冲突解决后怎样证明没有丢掉意图

冲突文件同时包含“提高伤害”和“修复无敌帧”两方修改。你手工删掉冲突标记后，下一步不能只执行 `git add`。请列出恢复意图、验证和完成整合的顺序。

<details><summary>最小提示</summary>
先读双方提交和冲突上下文，再验证行为；冲突标记消失不等于语义正确。
</details>

<details><summary>讲解与验证</summary>

先用 `git diff --cc`、`git log -p` 和双方分支的测试理解两项修改，再编辑文件保留两项兼容意图，搜索 `<<<<<<<` 等残留标记，运行针对伤害和无敌帧的回归测试，确认工作区差异后才 `git add`，最后在 merge 中提交或在 rebase 中 `git rebase --continue`。边界是两项修改可能确实互相矛盾，此时要由规则优先级决定取舍，不能机械拼接文本。常见错误是选择“当前/传入”版本后跳过测试，或误把生成文件冲突当成源文件冲突。验证证据包括测试退出码、关键输入和最终 diff；游戏映射：资产 GUID、能力配置和战斗规则冲突都可能文本可合并但行为错误，必须以运行时不变量验收。
</details>

### T04-Q3：`bisect` 为什么需要稳定的判定器

某个战斗回归只在随机 seed=42 且无图形界面时出现。请说明如何把它改造成 `git bisect run` 可以使用的测试入口，并指出什么情况下应中止二分。

<details><summary>讲解与验证</summary>

测试脚本应固定 seed、输入资源和工具版本，成功返回 0、复现回归返回非 0，并把提交、seed、日志写入临时输出；先手工确认已知好提交返回 0、已知坏提交返回非 0，再运行 `git bisect start`、标记 good/bad 和 `git bisect run ./repro.sh`。如果测试出现无法判断的退出码、依赖网络/当前时间、构建失败与逻辑失败混在一起，或工作区有未保存修改，就应先清理或 `git bisect reset`，不能把 unknown 当 bad。常见错误是用人工观察或 flaky 测试二分。游戏映射：固定 seed 的最小战斗复现能把“偶发手感问题”缩小为一个提交，并留下可回归的证据。
</details>
