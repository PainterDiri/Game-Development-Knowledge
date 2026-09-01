# 3. 分支与远端：多人工作时，引用怎样移动

分支（branch）不是项目的另一份完整复制。它主要是一个指向提交的可移动名字。你在分支上提交时，该名字向新提交移动。

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
git switch -c feature/player-dash  # 创建并切换
git branch -d feature/player-dash  # 安全删除已合并本地分支
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
- 默认 merge 行为取决于配置，不应让团队成员各自猜测。

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

## 本章验证

在临时仓库画出：本地 `main`、功能分支、`origin/main` 分别指向哪个提交。每执行一次 `fetch`、`pull --ff-only` 或 `push`，重新运行：

```bash
git log --oneline --decorate --graph --all
```

如果只能说“把代码同步了”，还没有掌握分支。你需要指出**哪个引用从哪个提交移动到哪个提交**。第 4 章处理历史真正分叉后的 merge、rebase、冲突和恢复。


## 本章练习

### T03-Q1：fetch 与 pull

远端 main 前进，本地 feature 有提交。先做什么？比较 `fetch`、`pull --ff-only` 和 `pull --rebase`。

<details><summary>最小提示</summary>

先 fetch 看图，不要直接 pull。
</details>

<details><summary>讲解与验证</summary>

`git fetch origin` 更新 `origin/main` 和对象，不改工作区；`pull --ff-only` 只有可直接前移才整合；`pull --rebase` 会重放未共享提交、改变提交 ID。用 `git log --graph --all` 验证。force-with-lease 只在个人未共享分支且团队允许时使用。游戏映射：构建分支要知道自己基于哪个提交。
</details>

### T03-Q2：把证据写出来

请为本章主题列出一个最小可执行验证，并说明预期结果和失败后的下一步。

<details><summary>最小提示</summary>

不要只写“运行一下”；写出输入、命令、观察对象和判定条件。
</details>

<details><summary>讲解与验证</summary>

合格验证应固定输入并记录命令、退出码、变更的 Git 状态或构建产物；预期结果必须可观察，失败时能缩小到一个阶段或不变量。若结果受时间、网络、缓存或未提交工作影响，应先隔离这些变量。常见错误是只看屏幕上的成功文字，不检查退出码、diff、artifact 或清理后重建。游戏映射：工程质量来自可重复证据，而不是一次“看起来能跑”。
</details>
