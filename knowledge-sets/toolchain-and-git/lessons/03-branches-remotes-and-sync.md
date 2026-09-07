# 3. 分支与远端：多人工作时，引用怎样移动

分支（branch）不是项目的另一份完整复制。它主要是一个指向提交的可移动名字。你在分支上提交时，该名字向新提交移动。

## 机制

本地分支与远端跟踪分支是提交引用；HEAD 通常是指向当前分支的符号引用；`fetch` 更新本地记录的远端引用，`switch` 更新当前工作区，`merge`/`rebase` 产生或重放历史，`push` 才请求远端引用移动。理解“哪个引用移动、哪个文件改变”是安全协作的核心。


```text
A---B---C  main
         \
          D---E  feature/player-dash
```

## 3.1 `git branch` 与 `git switch`

```bash
git branch                         # 列出本地分支
git branch feature/player-dash     # 在当前提交创建分支名
git switch feature/player-dash     # 切换工作区到该分支
git switch -c feature/other-task   # 替代上面两步：创建另一个不存在的分支
git switch main                    # 先离开待删除分支
git branch -d feature/player-dash  # 删除满足 Git 合并检查的本地分支
```

`switch` 会更新 `HEAD`、暂存区和工作区以匹配目标分支。若未提交修改会被覆盖或导致冲突，Git 通常会阻止切换。不要用强制选项绕过提示；先提交、暂存到安全位置或明确丢弃。

### 分支命名表达任务，不表达人名

常见形式：

```text
feature/player-dash
fix/seeded-room-exit
chore/upgrade-test-runner
release/1.3
hotfix/save-corruption
```

名字应帮助评审者理解工作目的。一个分支只承载一个可合并任务；“alice-work”几周不合并会积累大量冲突，也难以独立回滚。

## 3.2 远端不是云端工作区

```bash
git remote -v
git remote add origin <url>
git remote show origin
```

远端（remote）是 URL 与抓取/推送规则的别名。`origin/main` 是你上次获取到的远端主分支状态的本地记录，不是一个会实时更新的网络对象。

## 3.3 `fetch`：先拿信息，不改当前工作区

```bash
git fetch origin
git fetch --prune origin
```

- 下载远端新增对象；
- 更新远端跟踪引用，如 `origin/main`；
- 默认不切换分支、不合并、不改工作区；
- `--prune` 清理远端已经删除的跟踪引用。

因此在不确定远端发生了什么时，`fetch` 是安全的第一步：

```bash
git fetch origin
git log --oneline --graph --decorate HEAD..origin/main
git diff HEAD...origin/main
```

## 3.4 `pull`：fetch 之后立即整合

```bash
git pull --ff-only
git pull --rebase
```

`pull` 不是新的同步魔法，本质是 `fetch` 加一种整合策略：

- `--ff-only`：只有当前分支可以直接前移时才成功；历史已分叉就停下，让人决定；
- `--rebase`：先取远端，再把本地未共享提交重放到远端之上；
- 不带策略参数时的默认行为取决于 Git 版本与配置，不应让团队成员各自猜测。

不指定远端/分支时，pull 使用当前分支的上游配置，并不总是 origin/main。先用 `git branch -vv` 看 upstream；功能分支若跟踪 origin/feature，就不会因此整合主线。需要明确整合主线时可先 fetch 再 merge/rebase origin/main；没有配置 upstream 时则明确提供来源，而不是碰运气。

初学者在共享主线使用 `git pull --ff-only` 更容易观察历史；功能分支可按团队规则选择 rebase 或 merge。

## 3.5 `push`：上传对象并请求移动远端引用

```bash
git push -u origin feature/player-dash
git push
git push origin --delete feature/player-dash
```

第一次 `-u` 设置上游关系，之后可以直接 `git push`。push 失败的常见原因：

- 远端分支已前进，当前推送不是快进；
- 分支保护要求通过 PR/CI；
- 权限不足；
- LFS 大对象未获取或配额失败。

不要遇到拒绝就强推。先 `fetch`，画出提交图，决定 rebase、merge 还是放弃本地变化。

`--force-with-lease` 比 `--force` 多一层“远端仍是我上次看到的状态”检查，但仍会重写远端历史。它只适合团队明确允许重写的个人功能分支；受保护主线和他人共享分支不应使用。

## 3.6 标签与发布身份

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
git show v1.0.0
```

分支会继续移动，标签（tag）通常给某个提交一个稳定发布名。标签本身不是发布包，也不证明测试通过；发布系统仍应把标签/提交、artifact、平台、构建 ID 和测试报告关联起来。

## 3.7 功能分支每天怎样保持可合并

建议循环：

```text
领取一个有明确验收标准的小任务
→ 从最新 main 创建短分支
→ 先写/更新测试
→ 小提交并本地验证
→ fetch 观察主线变化
→ 按团队策略 rebase 或 merge main
→ 解决冲突并重跑测试
→ push，创建 PR
```

若分支持续数周，解决办法通常不是“最后一天再合并”，而是拆小任务、建立兼容接缝、使用 feature flag 或先合并不改变行为的重构。

## 3.8 用本地裸仓库模拟两个协作者

本节承接第 2 章 2.10 的临时目录；跳读者先执行那一节的完整命令块。

裸仓库（bare）保存对象、引用和配置，没有用于编辑的工作区，适合充当这个情景的远端。work 是最初初始化的工作仓库，peer 是从远端创建的独立克隆；origin/main 是各自的本地观察，并不共享即时状态。`git -C <目录> ...` 在指定仓库执行一次 Git 命令，不改变当前 shell 目录。

<!-- git-scenario: 03 -->
```bash
# Continue after chapter 2 in the SAME shell; git_lab identifies the temporary lab.
git init --bare -b main "$git_lab/remote.git"
cd "$git_lab/work"
git remote add origin "$git_lab/remote.git"
git push -u origin main
git clone "$git_lab/remote.git" "$git_lab/peer"
git -C "$git_lab/peer" config user.name "Course Fixture"
git -C "$git_lab/peer" config user.email "fixture.invalid"
printf 'dash=space\n' > "$git_lab/peer/input.txt"
git -C "$git_lab/peer" add input.txt
git -C "$git_lab/peer" commit -m "Add dash input mapping"
git -C "$git_lab/peer" push
before_fetch=$(git rev-parse HEAD)
git rev-parse HEAD origin/main
git fetch origin
test "$(git rev-parse HEAD)" = "$before_fetch"
test ! -e input.txt
git show origin/main:input.txt
git log --oneline HEAD..origin/main
git pull --ff-only
test -f input.txt
# Create divergent commits that touch different files.
printf 'peer update\n' > "$git_lab/peer/peer.txt"
git -C "$git_lab/peer" add peer.txt
git -C "$git_lab/peer" commit -m "Record peer change"
git -C "$git_lab/peer" push
printf 'local update\n' > local.txt
git add local.txt
git commit -m "Record local change"
if git push; then
    echo 'ERROR: divergent push unexpectedly succeeded' >&2; exit 1
fi
if git pull --ff-only; then
    echo 'ERROR: divergent pull unexpectedly succeeded' >&2; exit 1
fi
git status --short
git log --oneline --graph --all
# Preserve both histories; no force push.
git merge --no-edit origin/main
test -f local.txt && test -f peer.txt
git push
git -C "$git_lab/peer" pull --ff-only
```

先预测再运行：peer 推送后、work fetch 前，work 的 HEAD 和 origin/main 都停在旧提交；fetch 后只 origin/main 前进，input.txt 不会凭空出现在当前工作区。pull --ff-only 才使 main、索引和工作区前移。随后两端各提交一项修改，push 与 pull --ff-only 都应失败；脚本用 if 明确接住“预期失败”，如果反而成功就退出报错。fetch 已经更新远端观察，即使 pull 的整合失败，也不是所有状态完全没变。

`git log A..B` 选的是 B 可达而 A 不可达的提交；`git diff A...B` 比较共同祖先到 B 的内容，不是“两边全部差异”。要比较当前两棵树直接用 `git diff A B`。分叉后本例 merge 保留两个父历史，再普通 push，不靠强推抹掉别人提交。

该实验验证远端引用语义和本地 transport，不验证托管平台账号、网络故障、PR 权限、分支保护或 LFS；无需为了本课实验创建真实远端。

## 本章验证

在临时仓库画出：本地 `main`、功能分支、`origin/main` 分别指向哪个提交。每执行一次 `fetch`、`pull --ff-only` 或 `push`，重新运行：

```bash
git log --oneline --decorate --graph --all
```

如果只能说“把代码同步了”，还没有掌握分支。你需要指出**哪个引用从哪个提交移动到哪个提交**。第 4 章处理历史真正分叉后的 merge、rebase、冲突和恢复。


## 本章练习

### T03-Q1：`fetch`、快进与重放

**题型**：提交图状态推演
**作答产物**：三条命令后的提交图、HEAD/远端跟踪分支位置和工作树变化表。

初始状态为：

```text
A---B---C  origin/main
     \
      D---E  feature/wave (HEAD)
```

当前分支 `feature/wave` 的上游也是 `origin/feature/wave`，不是 `origin/main`。分别分析下列**互相独立**的操作：

1. `git fetch origin`；
2. `git pull --ff-only origin main`；
3. `git pull --rebase origin main`。

对每项写出：是否成功、哪些引用移动、D/E 的提交 ID 是否改变、工作树何时可能冲突。最后给出“只想先观察远端 main，再决定 merge/rebase”的安全命令序列。

<details><summary>讲解、判定与验证</summary>

`git fetch origin` 只下载对象并更新远端跟踪引用；在题图已是最新时图不变，HEAD、`feature/wave` 和工作树不动。`git pull --ff-only origin main` 等价于先 fetch 再尝试把当前 `feature/wave` 快进到 `origin/main`；由于 C 与 E 已分叉，不存在只移动分支指针的快进，所以失败，D/E 不变，正常情况下工作树不被整合。`git pull --rebase origin main` 则先 fetch，再把当前分支上相对 main 的 D/E 重放到 C，成功时得到：

```text
A---B---C---D'---E'  feature/wave (HEAD)
```

D/E 的补丁意图保留但提交 ID 改变；重放每个提交时都可能冲突，冲突会暂停并要求 `status → 编辑 → add → rebase --continue`，或 `rebase --abort` 回到开始前。

安全观察序列：

```bash
git status --short
git fetch origin
git log --graph --oneline --decorate --all -20
git diff origin/main...HEAD
```

确认工作树干净且分支是否共享后，再显式选择 `git merge origin/main` 或 `git rebase origin/main`。评分点：指出 pull 的来源由显式 `origin main` 决定，而不是当前上游；区分引用移动、提交身份和工作树变化；不能把 `fetch` 说成自动合并。边界：已共享的 feature 通常避免无沟通 rebase；任何后续 push 都先普通推送，只有团队允许改写且完成核对时才考虑 `--force-with-lease`。游戏映射：构建分支与内容分支必须明确基于哪个提交，不能把“已经下载远端状态”误认为“当前构建已包含远端状态”。
</details>

### T03-Q2：非快进 push 前如何保护本地工作

**题型**：故障诊断与恢复
**作答产物**：风险定位、安全命令序列、恢复点与验证输出。

远端 `main` 已前进，你的 `feature/wave` 也有两个本地提交。直接 `git push` 被拒绝。请给出一种保留双方历史的整合方案，并说明为什么不能先强制推送。


<details><summary>讲解、判定与验证</summary>

可执行方案是 `git fetch origin`，确认当前在 `feature/wave` 后选择 `git rebase origin/main` 或 `git merge origin/main`；解决冲突并运行测试后，再普通 `git push origin feature/wave`。rebase 会重写本地两个提交的身份，若该分支已经被别人基于它开发，应改用 merge 或先沟通；无论哪种方案，都要用 `git log --graph --oneline --decorate --all` 和 `git diff origin/main...HEAD` 验证变更范围。边界是远端分支保护和协作者共享历史，`git push --force` 可能覆盖别人刚推送的提交；常见错误是把本地 `main` 当成远端最新状态。游戏映射：多人同时改输入、敌人配置或资产索引时，先同步再整合可以把冲突留在可审查的功能分支，而不是直接污染集成分支。
</details>

## 来源与适用范围

核对日期：2026-09-07。使用本地 Git 2.55.0 运行章节情景；命令契约对照 Git 官方手册（[fetch](https://git-scm.com/docs/git-fetch), [pull](https://git-scm.com/docs/git-pull), [push](https://git-scm.com/docs/git-push)）。这些是教学工作流，不代表任何公司的内部流程。
