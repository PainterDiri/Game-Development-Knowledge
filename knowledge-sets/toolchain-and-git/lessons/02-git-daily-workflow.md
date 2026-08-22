# 2. Git 日常基础：工作区、暂存区与提交

想象你把 `damage=10` 改成 `damage=12`，又临时加入了调试输出。你只想提交伤害修复，不想提交调试代码。若版本控制只有“保存全部”按钮，这两个变化就很难分开。

Git 用三个主要状态解决这个问题：

```text
工作区（你正在编辑）
    │ git add / git restore
    ▼
暂存区（下一次提交准备包含什么）
    │ git commit
    ▼
本地提交历史（已经命名的快照）
```

## 2.1 `git init` 与 `git clone`：仓库从哪里来

### `git init`

```bash
git init
```

- **作用**：在当前目录创建 `.git/`，让目录成为 Git 仓库；
- **改变**：创建本地对象库、引用和配置；
- **不改变**：不会自动提交已有文件，不会创建远端仓库；
- **验证**：`git status` 不再报告“not a git repository”；
- **适用**：从本地新项目开始。

不要在仓库的子目录里误运行 `git init`，否则会得到嵌套仓库。先用 `git rev-parse --show-toplevel` 检查仓库根目录。

### `git clone`

```bash
git clone <repository-url>
```

- **作用**：复制远端仓库的对象和引用，创建工作区并配置默认远端 `origin`；
- **改变**：新建目录和本地仓库；
- **不改变**：不会证明依赖、LFS 对象、SDK 或引擎缓存已经齐全；
- **验证**：进入目录后运行 `git remote -v`、`git status` 和项目测试；
- **适用**：加入已有项目。

## 2.2 `git status`：每个操作前后的仪表盘

```bash
git status
git status --short
```

`status` 读取工作区、暂存区和当前提交，不修改文件。它会告诉你：

- 当前分支；
- 哪些文件只在工作区改变；
- 哪些变化已暂存；
- 哪些文件尚未跟踪；
- 是否正在 merge/rebase，以及冲突是否解决。

专业习惯不是“出错后才看 status”，而是重要操作前后都看一次。

## 2.3 `git diff`：确认到底改变了什么

```bash
git diff             # 工作区 vs 暂存区
git diff --cached    # 暂存区 vs 当前提交 HEAD
git diff HEAD        # 工作区整体 vs HEAD
```

`HEAD` 通常表示当前分支指向的提交。三个比较对象必须分清：

```text
HEAD -------- git diff --cached -------- 暂存区
  \---------------- git diff HEAD ---------------- 工作区
                     暂存区 -------- git diff ----- 工作区
```

提交前最重要的是 `git diff --cached`，因为它展示下一次提交实际会包含的内容，而不是编辑器里所有未保存想法。

## 2.4 `git add`：把变化放入下一次快照

```bash
git add path/to/file
git add -p
git add -A
```

- `git add <path>`：把指定路径当前内容复制到暂存区；
- `git add -p`：逐块选择，适合把调试代码和真实修复分开；
- `git add -A`：暂存所有新增、修改和删除，方便但容易混入无关文件。

`add` 不是上传，也不是永久保存。它只是改写暂存区。文件之后继续被编辑时，工作区和暂存区可以再次不同，所以 `add` 后仍应运行 `git diff --cached`。

## 2.5 `git restore`：撤销工作区或暂存选择

```bash
git restore path/to/file
git restore --staged path/to/file
git restore --source=<commit> path/to/file
```

- 默认形式用暂存区版本覆盖工作区，会丢弃该文件尚未提交的编辑；
- `--staged` 把文件移出暂存区，但保留工作区内容；
- `--source` 从指定提交取文件内容，适合恢复已知版本。

运行前先 `git diff`。如果内容还可能需要，先复制到临时文件或提交到个人分支，不要凭记忆恢复。

## 2.6 `git commit`：创建一个本地快照节点

```bash
git commit -m "Fix exit generation for seeded rooms"
```

提交包含：暂存区快照、父提交、作者/提交者信息和说明。它不会自动包含未暂存变化，也不会自动运行测试、上传远端或发布游戏。

一个可审查提交应服务一个原因，并包含必要的代码、配置和测试。例如：

```text
Fix seeded room exit invariant

- preserve exactly one exit for every generated room
- add regression for seed 7 / room 3
- verify with: python3 -m unittest discover -s tests -v
```

### 修改最后一次未共享提交

```bash
git commit --amend
```

它会创建一个新的提交替换当前提交，因此提交 ID 改变。只在确认该提交尚未被别人基于其工作时使用。

## 2.7 查看历史：`log`、`show` 与 `blame`

```bash
git log --oneline --decorate --graph --all
git show <commit>
git show <commit>:path/to/file
git blame path/to/file
```

- `log` 查看提交图和引用；
- `show` 查看某个提交的元数据与补丁，或读取该提交中的文件；
- `blame` 查看每行最后由哪个提交改变，用来寻找上下文，不是寻找“犯错的人”。

调查 bug 时先看提交目的和相关测试，再联系作者或评审者；把 `blame` 当责备工具会破坏协作。

## 2.8 文件操作与忽略规则

```bash
git mv old new
git rm path
git rm --cached path
```

Git 最终记录的是快照差异；`mv` 是移动后暂存，`rm` 是删除后暂存。`rm --cached` 只停止跟踪索引中的文件，工作区文件可保留，常用于误提交的生成文件。

`.gitignore` 只影响尚未跟踪的文件，不会让已经提交的秘密或缓存从历史消失：

```gitignore
# Python
__pycache__/
*.pyc

# 构建产物
dist/

# Unity/UE 派生缓存示例
Library/
DerivedDataCache/
Intermediate/
```

Unity `.meta` 通常是资产身份输入，不能因为“自动生成”就一并忽略；第 6 章会从构建输入角度解释。

## 2.9 一次完整日常循环

```bash
git status
git switch -c fix/seeded-room-exit
# 编辑代码和测试
python3 -m unittest discover -s tests -v
git diff
git add -p
git diff --cached
git commit -m "Fix seeded room exit invariant"
git status
```

完成后你应能解释每条命令读取或改变了哪个状态。第 3 章会加入分支、远端、fetch/pull/push，解释多人同时工作时这些本地状态如何同步。
