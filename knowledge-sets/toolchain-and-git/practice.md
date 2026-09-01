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

## Git 隔离

先从仓库根目录执行 `python3 scripts/init_practice.py --course toolchain-and-git`，再执行 `git check-ignore -v .practice/toolchain-and-git` 和 `git status --short --untracked-files=all`。预期命中 `.gitignore` 且主仓库不显示个人文件。不要直接编辑 `knowledge-sets/toolchain-and-git/code/`，不要使用 `git add -f`，不要在仓库根目录运行 `git clean -fdx`。

## 里程碑 0：先用 Git 管住一次小改动

### 任务

1. 在 `.practice/toolchain-and-git/` 内创建个人副本；若需要练习 Git，在该副本内单独 `git init`，不要给外层教材仓库创建实践分支；
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
cd code/repro-game
python3 -m unittest discover -s tests -v
python3 src/game.py --seed 42
python3 src/game.py --seed 42 > /tmp/run-a
python3 src/game.py --seed 42 > /tmp/run-b
diff -u /tmp/run-a /tmp/run-b
```

预期：测试通过，`diff` 无输出，运行结果包含 seed、checksum 和每个房间。

## 里程碑 B：冷构建与 manifest

### 任务

1. 构建前删除 `dist/`；
2. 从 `src/` 复制或生成产物；
3. 计算源输入哈希；
4. manifest 至少包含 schema、deterministic/provenance 分层、游戏版本、seed、提交、Python 版本、构建命令、输入哈希、目标和限制；
5. 不写入用户绝对路径和当前时间到确定性字段；
6. 确认 `dist/` 被忽略，不把产物提交到 Git。

### 验收

```bash
rm -rf dist /tmp/repro-a /tmp/repro-b
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-a
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-b
diff -ru /tmp/repro-a /tmp/repro-b
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

## 下载实践代码

本页负责学习：题面、提示、解题路线、验收和失败诊断都直接在网站阅读。你也可以从课程页的“下载实践代码”入口取得整理好的代码包；ZIP 只包含可运行的 `code/repro-game/`、测试和构建入口，不重复打包本页和折叠答案。

下载后先进入包内的 `reference/code/repro-game/`，运行：

```bash
python3 -m unittest discover -s tests -v
python3 src/game.py --seed 42
```

包内代码是公开参考基线，不代表唯一解法。它不包含 `dist/`、缓存、个人练习状态、日志、密钥或用户绝对路径；实践时只编辑 `.practice/toolchain-and-git/` 或仓库外副本，不要直接修改教材源文件。
