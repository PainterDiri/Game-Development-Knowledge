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

rebase 通常为需要重放的提交创建新提交，因此父节点变化会改变 ID；已在新基底中的补丁可能被跳过，无需重放时也可能不改变历史。适合：

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
git show 'HEAD@{1}'
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

## 4.8 冲突、放弃与恢复：必须看到引用和内容

继续第 3 章的临时情景。两个分支修改同一伤害行，先触发 merge 冲突并 abort，验证回到操作前干净状态；再重做并按照明确产品规则整合。后半段在未共享分支演示 rebase 的 abort/continue、软 reset 与恢复，以及发布分支 cherry-pick/revert。

<!-- git-scenario: 04 -->
```bash
# Continue the temporary lab; start clean, never use these on real uncommitted work.
cd "$git_lab/work"
test -z "$(git status --porcelain)"
git switch -c feature/damage
printf 'damage=15\ndebug=0\n' > rules.txt
git add rules.txt
git commit -m "Tune attack damage"
git switch main
# Make a deliberate same-line conflict, not just a mergeable appended line.
printf 'damage=14\ndebug=0\ninvulnerability=1\n' > rules.txt
git add rules.txt
git commit -m "Tune baseline and add invulnerability"
before_merge=$(git rev-parse HEAD)
if git merge feature/damage; then
    echo 'ERROR: expected a conflict' >&2; exit 1
fi
git status --short
git show :1:rules.txt
git show :2:rules.txt
git show :3:rules.txt
git merge --abort
test "$(git rev-parse HEAD)" = "$before_merge"
test -z "$(git status --porcelain)"
if git merge feature/damage; then exit 1; fi
# Product decision: attack 15 AND retain invulnerability=1.
printf 'damage=15\ndebug=0\ninvulnerability=1\n' > rules.txt
python3 -c 'from pathlib import Path; s=Path("rules.txt").read_text(); assert s == "damage=15\ndebug=0\ninvulnerability=1\n"'
git diff --check
git add rules.txt
git commit -m "Integrate damage with invulnerability"
git rev-list --parents -n 1 HEAD
# An unpublished branch: rebase, abort once, then resolve and continue.
git switch -c feature/rebase HEAD~1
printf 'damage=16\ndebug=0\ninvulnerability=1\n' > rules.txt
git add rules.txt
git commit -m "Tune unpublished damage"
before_rebase=$(git rev-parse HEAD)
if git rebase main; then echo 'ERROR: expected rebase conflict' >&2; exit 1; fi
git rebase --abort
test "$(git rev-parse HEAD)" = "$before_rebase"
if git rebase main; then exit 1; fi
printf 'damage=16\ndebug=0\ninvulnerability=1\n' > rules.txt
git add rules.txt
GIT_EDITOR=true git rebase --continue
test "$(git rev-parse HEAD)" != "$before_rebase"
git merge-base --is-ancestor main HEAD
# Simulate moving an UNPUBLISHED branch while preserving the complete old snapshot.
lost=$(git rev-parse HEAD)
git reset --soft HEAD~1
git reflog -n 3
git branch rescue/rebased "$lost"
test "$(git rev-parse rescue/rebased)" = "$lost"
git reset --soft rescue/rebased
test -z "$(git status --porcelain)"
# Keep the same fix on a release branch, and undo it without rewriting history.
git switch -c release/demo main
git cherry-pick -x rescue/rebased
picked=$(git rev-parse HEAD)
git revert --no-edit "$picked"
test "$(git show HEAD:rules.txt)" = "$(git show main:rules.txt)"
git merge-base --is-ancestor "$picked" HEAD
git switch main
```

冲突阶段 `git show :1:rules.txt` 是共同祖先，`:2:` 是当前一侧，`:3:` 是被合并一侧。这是索引的冲突阶段条目，不是三个磁盘文件。成功 add 后它们被一个已解决的普通索引条目取代；Git 不知道“保留伤害15与无敌帧”才是需求，因此先验证内容再提交。

rebase 冲突中 ours 通常是已经重放到的新基底，theirs 是当前正在重放的提交，不能凭 UI 的“当前/传入”猜原分支身份。`GIT_EDITOR=true` 只对这一次 continue 禁用交互编辑，接受已有提交说明；正常编辑说明仍应检查。

本例 reset --soft 不丢工作区和索引，旧提交 ID 保存在 lost 中。真实遗失时要从 reflog 按说明/时间定位候选，再 `git show` 检查内容，建立 rescue 分支；**不要机械复制 HEAD@{1}，因为中间操作会继续改变序号**。reflog 不能救从未存入对象库的普通未提交文本。abort 从干净状态开始才容易恢复；有未提交修改时 merge --abort 不保证重建所有原始编辑。

cherry-pick -x 为回移修复记录来源，依赖它的接口/数据变更仍需检查。revert 生成新抵消提交，坏提交依然是祖先。回退 merge commit 时需选择主线父节点（-m 的参数是父编号），并理解对未来重合并的影响；本例只 revert 普通提交，不把 merge 回退当成同一条简单命令。

## 4.9 用稳定退出码二分真实提交图

<!-- git-scenario: 04bisect -->
```bash
# Independent tiny history, still below git_lab; no changes to the combat lab.
git init -b main "$git_lab/bisect"
cd "$git_lab/bisect"
git config user.name "Course Fixture"
git config user.email "fixture.invalid"
printf 'good\n' > behavior.txt
git add behavior.txt && git commit -m "Known working behavior"
good=$(git rev-parse HEAD)
printf 'notes\n' > notes.txt
git add notes.txt && git commit -m "Add harmless notes"
printf 'bad\n' > behavior.txt
git add behavior.txt && git commit -m "Introduce regression"
first_bad=$(git rev-parse HEAD)
printf 'more notes\n' >> notes.txt
git add notes.txt && git commit -m "Change unrelated notes"
# Keep the predicate outside the history under investigation.
cat > "$git_lab/predicate.py" <<'PYTEST'
from pathlib import Path
import sys
p = Path("behavior.txt")
if not p.exists():
    sys.exit(125)
sys.exit(0 if p.read_text() == "good\n" else 1)
PYTEST
git bisect start HEAD "$good"
git bisect run python3 "$git_lab/predicate.py"
test "$(git rev-parse refs/bisect/bad)" = "$first_bad"
git bisect reset
cd "$git_lab/work"
```

这里有四个提交，中间第三个首次把 good 改成 bad；判定器存放在历史外，避免 checkout 到旧版本时测试本身消失。脚本断言 bisect 的 bad 引用指向已知的首次坏提交；HEAD 可能仍在最后一个接受测试的好提交，不能拿它当结果，然后 reset 离开调查状态。

`git bisect run` 的约定：0=good，1–127（125 除外）=bad，125=本次无法测试而跳过，其他退出码使流程中止。127 往往是命令找不到，却会被解释成 bad，所以先确认工具存在。若编译失败不是正在调查的回归，适当返回125，而不是任意非零；跳过关键区间可能只能给出候选集合，不能伪称定位唯一提交。测试语义还应在所选区间保持可比较；修好又坏等非单调历史需要缩小区间。

## 本章决策口诀

- 合并已共享历史：优先 merge；
- 整理个人未共享历史：可 rebase；
- 把独立修复带到另一分支：cherry-pick，但记录来源；
- 共享主线回退：revert；
- 本地误操作恢复：先停手，看 status/reflog；
- 文件冲突结束后：必须测试语义和资产引用。

第 5 章把这些操作放进完整团队流程：任务、PR、评审、CI、发布候选和正式版本。


## 本章练习

### T04-Q1：按共享边界选择恢复方法

**题型**：双场景提交图诊断与恢复实作
**作答产物**：每个场景的命令、恢复前后提交图、工作树/历史影响和验证证据。

分别处理两个互不相关的场景：

**场景 A：共享历史**

```text
A---B---C  main, origin/main
```

C 是已被队友拉取的坏规则提交，B 对应的发布包仍可用。要求保留审计历史，并让 main 的内容撤销 C。

**场景 B：仅本地误操作**

你在未共享分支上原有 `D---E`，误执行 `git reset --hard D` 后 E 从普通日志消失，且操作后尚未运行会清理 reflog 的命令。要求恢复到 E。

为每个场景给出步骤；说明什么时候需要先建救援分支，以及为什么 A 不能用强推、B 不能直接凭记忆重写 E。

<details><summary>讲解、判定与验证</summary>

场景 A 先确认工作树和目标提交，再创建反向提交：

```bash
git status --short
git show --stat C
git revert C
# 解决冲突时：编辑 → git add → git revert --continue
git diff --check
git test-or-project-command
git log --graph --oneline --decorate -5
```

结果近似 `A---B---C---R`，R 的补丁抵消 C。历史仍说明 C 曾发生以及何时被撤销；普通 push 不破坏队友已有提交。线上回滚若直接复用 B 的已验证 artifact，还要另记录部署目标与兼容性，Git revert 本身不等于部署完成。

场景 B 先从 reflog 找到 E，再固定它：

```bash
git reflog --date=local
# 假设确认 E 的对象名是 <e-sha>
git branch rescue/e <e-sha>
git switch feature-branch
git reset --hard <e-sha>
git log --graph --oneline --decorate -5
```

若当前工作树在误 reset 后又有新改动，先 `git status`，将其提交到临时分支或另行备份，再执行 hard reset。也可直接切到救援分支后决定如何合并。评分点：A 使用新增历史的 revert，B 使用 reflog 找对象并先固定引用；写明冲突/脏工作树处理；验证内容与图。常见错误是对共享 main `reset --hard` 后强推，或还没确认对象就继续做大量历史重写。游戏映射：共享代码修复需要可审计反向变更；本地丢失提交则依赖 Git 对对象与引用移动的记录，两者与“将线上服务器切回旧 artifact”又是不同状态层。
</details>

### T04-Q2：冲突解决后怎样证明没有丢掉意图

**题型**：冲突诊断与回归验证
**作答产物**：保留双方意图的结果、最小 diff 与覆盖两个意图的测试。

冲突文件同时包含“提高伤害”和“修复无敌帧”两方修改。你手工删掉冲突标记后，下一步不能只执行 `git add`。请列出恢复意图、验证和完成整合的顺序。


<details><summary>讲解、判定与验证</summary>

先用 `git diff --cc`、`git log -p` 和双方分支的测试理解两项修改，再编辑文件保留两项兼容意图，搜索 `<<<<<<<` 等残留标记，运行针对伤害和无敌帧的回归测试，确认工作区差异后才 `git add`，最后在 merge 中提交或在 rebase 中 `git rebase --continue`。边界是两项修改可能确实互相矛盾，此时要由规则优先级决定取舍，不能机械拼接文本。常见错误是选择“当前/传入”版本后跳过测试，或误把生成文件冲突当成源文件冲突。验证证据包括测试退出码、关键输入和最终 diff；游戏映射：资产 GUID、能力配置和战斗规则冲突都可能文本可合并但行为错误，必须以运行时不变量验收。
</details>

### T04-Q3：`bisect` 为什么需要稳定的判定器

**题型**：算法推演与测试设计
**作答产物**：搜索区间推演表、稳定判定器和一次错误判定的后果。

某个战斗回归只在随机 seed=42 且无图形界面时出现。请说明如何把它改造成 `git bisect run` 可以使用的测试入口，并指出什么情况下应中止二分。

<details><summary>讲解、判定与验证</summary>

测试脚本应固定 seed、输入资源和工具版本，成功返回 0、复现回归返回 1（一般 bad 范围是 1–127，125 除外），并把提交、seed、日志写入临时输出；先手工确认已知好提交返回 0、已知坏提交返回非 0，再运行 `git bisect start`、标记 good/bad 和 `git bisect run ./repro.sh`。如果测试出现无法判断的退出码、依赖网络/当前时间、构建失败与逻辑失败混在一起，或工作区有未保存修改，就应先清理或 `git bisect reset`，不能把 unknown 当 bad。常见错误是用人工观察或 flaky 测试二分。游戏映射：固定 seed 的最小战斗复现能把“偶发手感问题”缩小为一个提交，并留下可回归的证据。
</details>

## 来源与适用范围

核对日期：2026-09-07。使用本地 Git 2.55.0 运行章节情景；命令契约对照 Git 官方手册（[merge](https://git-scm.com/docs/git-merge), [rebase](https://git-scm.com/docs/git-rebase), [reflog](https://git-scm.com/docs/git-reflog), [bisect](https://git-scm.com/docs/git-bisect)）。这些是教学工作流，不代表任何公司的内部流程。
