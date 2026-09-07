# 主实践：可复现 seeded-room 工程

这页同时包含题面、参考路线、失败诊断和代码入口。你不需要另外填写实验报告；验收以命令输出、测试结果和可解释的构建证据为准。

## 目标

完成一个不依赖 Unity/Unreal 的最小游戏工程，使另一位开发者在干净 checkout 中可以：

```text
运行测试 → 用显式 seed 构建 → 读取 manifest → 启动产物 → 复现一个故意失败 → 定位并修复
```

选择无引擎载体是为了让你把注意力放在工具链不变量上。完成后再将同一张输入/输出表迁移到 Unity 或 UE。

## 本课程实践边界

这个项目只验证工具链、Git、确定性、构建证据和故障定位，不承担接入最终游戏的职责。最终交付是一份可在另一台机器复现的命令行小游戏工程，包含固定 seed、测试、构建 manifest、CI 思路和回滚证据。

## 最快开始：下载到仓库外（推荐）

[下载 `toolchain-and-git-code.zip`](../../docs/downloads/toolchain-and-git-code.zip)，解压到个人短路径，例如 `~/game-labs/toolchain/`。打开包根目录 `START_HERE.md`，然后进入：

```bash
cd toolchain-and-git-practice/workspace/repro-game
python3 -m unittest discover -s tests -v
python3 src/build.py --output dist --seed 42
python3 dist/game.py --seed 42
```

预期 9 个测试通过，构建器输出 `built dist`，游戏输出包含 `seed=42`、checksum 和 5 个房间。这个目录是可编辑绿色基线；`../../reference/repro-game/` 只用于恢复或比较。后续必须亲自创建 Git 历史、注入回归、修改测试和走完定位/回滚，不能把基线通过当作完成。

如果你在本地直接阅读 Git 仓库而不是网站，亦可运行 `python3 scripts/package_practice.py --course toolchain-and-git --output /tmp/toolchain-and-git-code.zip` 生成同一结构。

## 环境与代码入口

- Python 3.11+，只用标准库；
- Git 2.x；
- 不依赖网络、Unity、Unreal、外部包或用户目录；
- 代码目录：`code/repro-game/`；
- [`src/game.py`](code/repro-game/src/game.py)：seed → 房间 → checksum；
- [`src/build.py`](code/repro-game/src/build.py)：清理输出、复制入口、写 manifest；
- [`tests/test_game.py`](code/repro-game/tests/test_game.py)：确定性、性质和边界测试；
- [`Makefile`](code/repro-game/Makefile)：统一入口。

## 分阶段指导

- 阶段 0：在隔离副本中观察 Git 工作区、暂存区和本地提交；
- 阶段 1：实现并测试固定 seed 的房间生成；
- 阶段 2：冷构建、生成 manifest、运行产物并用 `git bisect` 定位故意回归。

## 不能跳过的学习者改动

下载包提供的是可运行绿色基线，不是已完成作业。至少完成以下改动并保留自己的 Git 历史：

1. **独立改写**：保留公开测试，先把 `generate_room` 的函数体移到临时备份，再根据契约独立实现；不得只改变量名；
2. **先红后绿**：先加入一个针对固定 seed、出口数量或非法参数的失败测试，确认它在故意缺陷下失败，再修复到通过；
3. **构建证据**：给 manifest 增加一个稳定字段和一个 provenance 字段，证明前者参与确定性比较、后者允许两次构建不同；
4. **故障注入**：创建一个单独提交，引入题面指定的 seed 回归，用自动判定器完成 `git bisect`；定位后 revert 或修复，并保留回归测试；
5. **冷构建**：在两个新临时目录从同一提交构建，不复用 `dist/`，结构化比较 manifest 并启动两个产物。

如果没有“失败过的测试、自己写的修复提交、bisect 结果和两次冷构建证据”，只能证明参考基线能运行，不能证明已经掌握本课程出口能力。

## 仓库内实践的 Git 隔离（备选）

只有已经克隆本课程仓库并希望就近练习时，才从仓库根目录执行 `python3 scripts/init_practice.py --course toolchain-and-git`，再执行 `git check-ignore -v .practice/toolchain-and-git` 和 `git status --short --untracked-files=all`。预期命中 `.gitignore` 且主仓库不显示个人文件。不要直接编辑 `knowledge-sets/toolchain-and-git/code/`，不要使用 `git add -f`，不要在仓库根目录运行 `git clean -fdx`。

使用下载包时，后文命令在 `workspace/repro-game` 执行。使用 `.practice` 备选路径时，命令在个人副本 `repro-game` 中执行，不是教材公开 `code/repro-game`；初始化成功后进入：

```bash
cd .practice/toolchain-and-git/repro-game
git init
```

如果副本已存在，初始化脚本会拒绝覆盖；继续使用已有副本，不删除自己的成果。验收中的 `(...)` 是子 shell，`set -eu` 让该组命令在失败或未设置变量时停止，不改变外层 shell 选项；`mktemp -d` 新建独占临时目录，双引号防止路径中的空格被拆开。快照留在本机临时目录供检查，不使用或强删固定的共享 `/tmp` 文件名。`--clean` 若拒绝未知文件，应先检查、备份或移开；不能改成 `rm -rf` 绕过保护。两次构建之间也必须清理，才是两次冷构建。

## 里程碑 0：先用 Git 管住一次小改动

### 任务

1. 进入当前可编辑基线：下载包使用 `workspace/repro-game/`，仓库备选使用 `.practice/toolchain-and-git/repro-game/`；在这里单独 `git init`，不要给外层教材仓库创建实践分支；
2. 运行现有测试，确认基线通过；
3. 只修改 README 或一条测试说明，使用 `git status`、`git diff`、`git add -p` 和 `git diff --cached` 观察三个状态；
4. 创建一个单一目的提交，并用 `git show --stat HEAD` 检查；
5. 在临时分支练习一次 `revert`，确认历史增加而不是删除。

### 验收

```bash
git status
git log --oneline --decorate --graph -5
git show --stat HEAD
```

预期：你能指出当前分支、工作区是否干净、最后提交包含什么，以及 revert 与删除历史的区别。

## 里程碑 A：确定性与性质

### 任务

1. 运行现有测试，理解 `generate_room(seed, room_index)` 的输入和不变量；
2. 验证相同 seed 的 `run()` 输出相同；
3. 验证不同 seed 能产生不同结果；
4. 为非法 room index 保留明确失败；
5. 如果扩展房间规则，测试入口、出口、宝藏的性质，而不是只复制一张期望字符串。

### 验收

```bash
python3 -m unittest discover -s tests -v
python3 src/game.py --seed 42
(
  set -eu
  run_dir=$(mktemp -d)
  python3 src/game.py --seed 42 > "$run_dir/a"
  python3 src/game.py --seed 42 > "$run_dir/b"
  diff -u "$run_dir/a" "$run_dir/b"
  printf '本次运行输出保留在 %s\n' "$run_dir"
)
```

预期：测试通过，`diff` 无输出，运行结果包含 seed、checksum 和每个房间。

## 里程碑 B：冷构建与 manifest

### 任务

1. 构建前用构建器的 `--clean` 清理已识别的 `dist/`；遇到未知文件则停止检查，不递归强删；
2. 从 `src/` 复制或生成产物；
3. 计算源输入哈希；
4. manifest 至少包含 schema、deterministic/provenance 分层、游戏版本、seed、提交、Python 版本、构建命令、输入哈希、目标和限制；
5. 不写入用户绝对路径和当前时间到确定性字段；
6. 确认 `dist/` 被忽略，不把产物提交到 Git。

### 验收

```bash
(
  set -eu
  compare_dir=$(mktemp -d)
  python3 src/build.py --output dist --clean
  python3 src/build.py --output dist --seed 42 --version 1.0.0
  cp -R dist "$compare_dir/a"
  python3 src/build.py --output dist --clean
  python3 src/build.py --output dist --seed 42 --version 1.0.0
  cp -R dist "$compare_dir/b"
  diff -ru "$compare_dir/a" "$compare_dir/b"
  printf '比对快照保留在 %s\n' "$compare_dir"
)
python3 dist/game.py --seed 42
git check-ignore -v dist/game.py
```

预期：两次构建无差异，产物可启动，`git check-ignore` 命中规则。改变 seed 时，行为应改变；源码哈希不应因为 seed 改变。

## 里程碑 C：故意失败与最小诊断

### 任务

在临时分支制造一个只影响 `seed=7, room_index=3` 的缺出口回归：

1. 让测试失败，并让失败信息包含 seed 和 room index；
2. 提交一个引入回归的提交；
3. 再提交一个与回归无关的正常修改；
4. 用 `git bisect` 或手动二分定位引入提交；
5. 修复并保留 `seed=7, room=3` 回归测试；
6. 再运行所有 seed/房间性质测试，确认没有只修复单个输出而破坏一般规则。

示例最小测试：

```python
room = generate_room(seed=7, room_index=3)
self.assertEqual(room.count("E"), 1, "seed=7 room=3 must have an exit")
```

### 验收

```bash
python3 -m unittest discover -s tests -v
git bisect start
git bisect bad
git bisect good <known-good-commit>
git bisect run python3 -m unittest discover -s tests -v
git bisect reset
```

如果某个提交不能判定，使用 `git bisect skip` 并在口头解释中说明结论范围变宽。

## 课程实践的最小版本

本实践不要求创建 Unity/Unreal 接缝；如果以后在引擎课程中复用构建证据，应重新按照那个课程的边界设计适配器。

## 时间不足的最小版本

只完成 0+A+B 也可以形成有效的最小交付：测试通过、两次冷构建一致、manifest 可读、产物可启动、产物目录被忽略。不要删除验收项后宣称“已可复现”。C 是把构建工程连接到真实调试工作的关键延伸。

## 验收证据矩阵

| 维度 | 必须保留的学习者证据 | 单独出现时不足以证明 |
|---|---|---|
| 基线 | 初次测试、构建和启动的命令与退出码 | 已经会独立实现 |
| 独立改写 | 删除/重写核心函数后的 diff、先失败后通过的测试 | 参考实现是唯一解 |
| 故障诊断 | 可复现坏提交、`bisect` 判定器输出、定位提交与修复回归 | 仓库没有其他缺陷 |
| 可复现构建 | 两个冷目录的 manifest 结构化比较、artifact hash 与启动冒烟 | 所有操作系统字节完全一致 |
| Git 隔离 | 仓库外工作目录；或 `.practice` 的 `check-ignore` 与主仓库干净状态 | 自动备份或可恢复未提交工作 |
| 发布思维 | commit、工具版本、测试报告与 artifact 身份的关联 | 已完成真实商店、签名或线上回滚 |

## 常见失败与诊断速查

<details>
<summary>两次构建不一致</summary>

先比较 manifest，再查当前时间、绝对路径、目录排序、随机输入和构建 ID。不要用“比较时忽略所有字段”掩盖未声明输入；应把 provenance 与 deterministic 字段分离。
</details>

<details>
<summary>测试通过但产物不能运行</summary>

测试只覆盖源码。运行 `python3 dist/game.py --seed 42`，检查复制入口、相对路径、权限和输出目录清理。将产物冒烟加入构建验收。
</details>

<details>
<summary>改 seed 后源文件哈希变化</summary>

构建过程把生成结果写回了 `src/`。随机输出只能进入临时目录或产物目录，不能污染源输入。
</details>

<details>
<summary>bisect 结果不稳定</summary>

测试依赖时间、网络、脏工作树或共享缓存。先让测试固定 seed、只写临时目录、返回明确退出码；不可判定提交要 skip。
</details>

## 参考路线，不是唯一答案

参考实现采用：

- `random.Random(derived_seed)`，避免共享全局随机状态；
- 构建前删除输出目录；
- 稳定 JSON、仓库相对路径和源哈希；
- 性质测试而非硬编码所有房间文本；
- 非零退出码暴露失败。

你也可以用 Make、PowerShell、CMake 或另一种语言重写。评价依据是输入是否显式、输出是否可重建、失败是否可判定、证据是否足以定位，而不是文件是否长得像参考实现。

## 迁移到 Unity 与 Unreal Engine

| seeded-room 概念 | Unity | Unreal Engine | 额外验证 |
|---|---|---|---|
| source | Assets、Packages、ProjectSettings、脚本 | Content、Config、Source、插件 | 干净 checkout 导入 |
| seed | ScriptableObject/配置、测试参数、开发 HUD | DataAsset/命令行参数/测试数据 | 相同 seed 行为不变量 |
| build.py | Editor batch/headless 构建脚本 | Automation/命令行/BuildGraph | 退出码和输出目录 |
| Library/cache | `Library/`、导入缓存 | `DerivedDataCache/`、Intermediate | 删除后冷构建 |
| manifest | 构建脚本 JSON、版本 HUD | BuildGraph/脚本 JSON、构建标签 | 提交/引擎/平台/插件 |
| smoke | 启动并加载最小场景 | 启动并加载地图/插件 | 日志与退出码 |
| artifact | 平台包、符号、报告 | Shipping 包、符号、报告 | 下载后可运行、可回滚 |

专业项目可能使用不同的版本控制、构建服务和资产服务器，但不会消除这些边界；它们只改变实现载体和恢复成本。

## 下载包角色

本页保留题面、分阶段操作、验收和失败诊断；ZIP 只交付可运行资产，不复制网页讲解。包根目录结构为：

```text
toolchain-and-git-practice/
├── START_HERE.md
├── workspace/repro-game/   # 你的可编辑基线
├── reference/repro-game/   # 恢复与对照，只读使用
└── manifest.json
```

在 `workspace/repro-game/` 完成全部实践；只有需要判断自己是否偏离契约时才查看 `reference/repro-game/`。不要在 reference 中工作，也不要直接修改教材仓库的 `knowledge-sets/toolchain-and-git/code/repro-game/`。下载包不包含 `dist/`、缓存、个人状态、日志、密钥或机器绝对路径。

## 构建与清理的安全验收

参考 `src/build.py` 只允许当前实践项目的 `dist` 或其子目录作为输出；命令从个人副本的 `repro-game` 根目录执行。非空目标必须只有可识别的构建产物，未知文件、符号链接、源码目录和外部目录都会被拒绝。`make clean` 调用同一验证路径，只移除已识别文件，不递归删除任意目录。

运行 `python3 -m unittest discover -s tests -v` 应包含 `test_build` 的 5 个安全回归与 `test_game` 的 4 个规则测试。安全回归只使用新建临时项目，不拿现有个人源码做删除试验。详细机制与迁移练习见[第 8 章](lessons/08-testing-building-and-diagnosis.md)。这是本地主动误用保护，不是多租户安全沙箱或事务性发布系统。
