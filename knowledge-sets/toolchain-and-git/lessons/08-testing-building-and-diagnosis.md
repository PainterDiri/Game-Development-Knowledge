# 8. 测试、构建与诊断：把“成功”变成证据

## 8.1 “编辑器能打开”为什么不够

编辑器打开通常只覆盖一部分导入路径。它不能证明：

- 目标平台模块存在；
- 插件、输入映射和关键场景都被纳入构建；
- Shipping/Release 配置能够链接；
- 产物能启动并加载第一场景；
- 随机内容满足不变量；
- CI 使用的是干净输入而非本机缓存。

更合理的是从便宜到昂贵分层：

```text
格式/链接/静态检查
  → 单元与性质测试
  → 资产/导入/引用检查
  → Development 构建
  → 产物启动与关键流程冒烟
  → Shipping / 平台矩阵 / 长时测试
```

每一层都应该有明确退出码和可保留的失败证据。昂贵的完整打包不能代替便宜的配置校验。

## 8.2 构建脚本的四个职责

一个可靠构建入口至少完成：

### 1. 输入校验

检查源码目录、版本格式、seed、目标平台、依赖和必要工具。输入不合法时尽早以非零退出码失败，不要生成半成品。

### 2. 输出隔离

构建前清理输出目录，避免旧文件让新构建“看起来成功”。输出路径要由命令显式指定，不能偷偷写入源码目录。

### 3. 稳定生成

排序文件列表、使用仓库相对路径、明确编码、避免当前时间污染确定性字段。对于资产转换，写清导入器版本和目标平台。

### 8. 身份与证据

至少写入提交、输入文件哈希、工具版本、目标配置、seed、命令、测试结果和产物路径。真实项目还会加入插件版本、平台 SDK、符号位置、构建服务 ID 和许可证状态。

## 8.3 manifest 的设计：确定性字段与来源字段分离

建议把 manifest 分成两层：

```json
{
  "schema": 1,
  "deterministic": {
    "source_commit": "abc123",
    "game_version": "1.0.0",
    "target": "linux-x64",
    "seed": 42,
    "inputs": [
      {"path": "src/game.py", "sha256": "..."}
    ]
  },
  "provenance": {
    "build_id": "ci-1842",
    "runner": "linux-builder-3",
    "started_at": "2026-08-22T10:00:00Z"
  }
}
```

`deterministic` 用来比较两次相同输入；`provenance` 用来追踪是哪一次执行。当前时间可以是重要证据，但如果把它混进确定性哈希，两次正常构建就会必然不同。

manifest 也不是完整的供应链安全证明：它不能自动保证工具没有被篡改、资产许可证合法或测试覆盖充分。它的最小价值是让“这个产物从哪里来”成为可查询事实。

## 8.4 测试三层：例子、性质、冒烟

### 例子测试

验证一个已知输入的具体输出，适合检查解析器、命令行和 manifest 字段。

### 性质测试

不硬编码所有随机地图，而是断言不变量：

```python
room = generate_room(seed=7, room_index=3)
assert room.count("@") == 1
assert room.count("E") == 1
assert room.count("T") == 1
```

对肉鸽生成器，入口可达、出口存在、房间索引合法、掉落表版本存在，往往比硬编码一张完整地图更稳定。性质测试不是降低要求，而是测试规则而非偶然排列。

### 产物冒烟

源码测试通过后，仍要执行构建产物：

```bash
python3 dist/game.py --seed 42
```

这能发现复制文件失败、入口丢失、依赖路径错误和构建后权限问题。它不等于完整游戏测试，但它证明了“交付物本身能启动”。

## 8.5 调试：从事故描述到最小复现

“第三个房间坏了”还不是测试。一个可执行失败报告至少包含：

```text
commit / build ID
工具与平台
内容版本
seed / room_index / wave_index
输入操作或数据
期望不变量
实际结果
日志与退出码
```

压缩过程：

1. **固定**：提交、工具、平台、seed 和内容版本；
2. **缩小**：从完整游戏缩到一个房间、一次导入或一条构建命令；
3. **判定**：把失败改成断言和非零退出码；
4. **保存**：修复后把最小输入保留为回归测试。

推荐日志记录能区分状态转移的字段，而不是打印所有对象。对于生成器，`seed=7 room=3 generator_version=2 invariant=exit_present` 比一张没有上下文的截图更有价值。

## 8.6 `git bisect` 为什么有前提

二分的逻辑是：如果一个已知 good 提交和一个已知 bad 提交之间，测试结果沿历史大致从 good 变 bad，那么每次测试中点即可缩小范围。

```bash
git bisect start
git bisect bad
git bisect good <known-good>
git bisect run python3 -m unittest discover -s code/repro-game/tests -v
git bisect reset
```

必须满足：

- 中间提交能构建或至少能运行判定测试；
- 测试无交互、无时间随机、无网络漂移；
- 工作树不会被测试污染；
- good/bad 定义清晰；
- 无法判定的提交用 `git bisect skip`，并降低结论精度。

如果测试受缓存或未固定 seed 影响，bisect 可能给出看似精确、实际上错误的提交。二分不是魔法，它放大的是测试稳定性。

## 8.7 Unity/UE 的门禁映射

| 层次 | Unity 示例 | Unreal 示例 | 失败证据 |
|---|---|---|---|
| 静态 | C# 编译、序列化检查、包锁校验 | C++ 编译、Config/插件校验 | 编译日志、错误路径 |
| 自动化 | EditMode/PlayMode、引用检查 | Automation System、功能测试 | 测试报告、截图/日志 |
| 构建 | batch/headless 脚本化构建 | 命令行/BuildGraph/Automation 打包 | manifest、构建日志 |
| 冒烟 | 启动、加载场景、输入映射 | 启动、加载地图、插件初始化 | 退出码、关键日志 |
| 发行 | 目标平台包、签名、符号 | Shipping 包、符号、平台 SDK | artifact、校验和、回滚版本 |

命令参数和 action 版本随项目变化；不变的是：公开入口、清理输出、锁定目标、保留证据。

## 本章验收

```bash
cd code/repro-game
python3 -m unittest discover -s tests -v
rm -rf dist /tmp/repro-a /tmp/repro-b
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-a
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-b
diff -ru /tmp/repro-a /tmp/repro-b
python3 dist/game.py --seed 42
```

预期：测试通过、两次目录无差异、产物启动成功。然后在临时分支故意让 `seed=7, room=3` 缺少出口，观察失败消息是否足以支撑最小复现。

## 8.8 把测试分层变成失败成本曲线

测试不是“有/没有”，而是失败被发现的时间和成本：

```text
静态检查 → 单元/性质 → 导入/引用 → 构建 → 产物冒烟 → 目标平台/长时运行
便宜快 ----------------------------------------------------> 昂贵慢
```

每一层都要回答三个问题：

1. 它能捕获哪一种失败？
2. 它不能捕获什么？
3. 失败时留下什么证据？

例如，性质测试能发现房间没有出口，但不能证明目标平台的输入映射存在；产物冒烟能发现复制和启动问题，但不能证明长时间战斗中的内存增长。把所有检查都称为“自动化测试”会让团队误以为覆盖范围更大。

## 8.9 让失败报告可以复制

不要只输出：

```text
Test failed
```

至少输出稳定定位字段：

```text
status=failed
commit=<source commit>
build_id=<build id or local>
seed=7
room_index=3
invariant=exit_present
expected=1
actual=0
exit_code=1
```

推荐日志采用 `key=value` 或 JSON 行，便于 CI 搜索和脚本解析；不要把 token、用户绝对路径和完整环境变量直接打进日志。对引擎项目，字段可以扩展为 `engine_version`、`target`、`scene`、`map`、`test_name` 和 `asset_guid`。

## 8.10 manifest 不是装饰，而是测试输入的一部分

一个可用 manifest 应至少能回答：

```text
这个包来自哪个提交？
使用了哪个目标平台、工具链和内容版本？
随机输入是什么？
输入文件和依赖如何校验？
哪些字段可以用于字节比较，哪些只用于追踪？
失败日志和测试报告在哪里？
```

建议把确定性字段与 provenance 分开：

```json
{
  "schema": 2,
  "deterministic": {
    "source_commit": "abc123",
    "target": "linux-x64",
    "seed": 42,
    "inputs": [{"path": "src/game.py", "sha256": "..."}]
  },
  "provenance": {
    "builder": "course-build-script",
    "command": "python3 src/build.py --output dist --seed 42"
  }
}
```

`source_commit` 属于输入身份；`builder` 和命令属于解释来源。真实项目还需要依赖锁文件、插件版本、平台 SDK、符号和构建服务 ID。manifest 不能证明工具未被篡改，也不能替代测试。

## 8.11 一个可自动化的最小复现脚本

将事故步骤写成脚本，而不是复制一段聊天记录：

```bash
#!/usr/bin/env bash
set -eu

python3 - <<'PY'
import sys
sys.path.insert(0, "src")
from game import generate_room
room = generate_room(seed=7, room_index=3)
assert room.count("E") == 1, f"seed=7 room=3 exit count={room.count('E')}"
PY
```

脚本有三个价值：可以被 `git bisect run` 调用；可以在干净 checkout 复现；可以作为永久回归测试。若事故只能靠“打开编辑器后手动点击十步”复现，先补一个最小命令行入口或记录输入事件，再谈二分。

### 本节验收

让一次故意失败同时具备：非零退出码、固定 seed/场景/房间、可读断言、可在干净 checkout 重复运行。然后列出该测试不能证明的两件事，避免把局部证据夸大成整机正确。


## 本章练习

### T08-Q1：把失败缩成命令

bisect 或 CI 需要一个什么样的测试入口？

<details><summary>最小提示</summary>

测试要稳定、可自动返回退出码、依赖固定输入。
</details>

<details><summary>讲解与验证</summary>

入口应无交互、无当前时间/网络/脏缓存依赖，成功 0、失败非 0，并在失败时保留 seed、提交和日志。先单测再集成/冒烟，`git bisect run` 才有判定依据。常见错误是用人工观察或 flaky 测试二分。游戏映射：最小复现让偶现战斗回归可定位。
</details>

### T08-Q2：把最小复现做成可自动判定入口

玩家报告“seed=17 的第三波敌人消失”。请设计 `repro.sh` 或等价脚本的输入、输出、退出码和日志字段，使它既能给人读，也能交给 CI 或 `git bisect run`。

<details><summary>最小提示</summary>
固定 seed、内容版本和运行模式；成功/失败要由退出码表达，日志要包含能重放事故的身份。
</details>

<details><summary>讲解与验证</summary>

入口应接受或固定 seed=17、内容版本、平台无关的测试配置，关闭交互和当前时间依赖，成功返回 0，发现第三波数量不符返回非 0；日志至少写 seed、commit/build ID、期望与实际波次、关键 checksum 和临时日志路径。先在已知好版本和已知坏版本各运行一次，再交给 CI 或 bisect。边界是构建失败、环境缺失和游戏逻辑失败要使用不同错误类别或清晰日志，不能把所有非 0 都解释成同一 bug；常见错误是只截屏、只返回文字或让脚本依赖本机绝对路径。游戏映射：最小复现是把玩家反馈转成可持续回归的工程资产。
</details>

### T08-Q3：如何识别 flaky 测试

一个性能冒烟测试有时通过、有时失败，但功能输出始终正确。请列出排查顺序，并说明何时不能把重试当作修复。

<details><summary>讲解与验证</summary>

先固定 seed、输入规模、CPU/GPU 目标、并发度、缓存状态和时间限制，保存每次运行的分布与环境；再判断失败是超时、资源争用、未排序输出、真实数据竞争还是阈值过紧。重复运行和对照版本只能帮助定位，不能把“重试三次取一次成功”当成质量门禁，因为它会隐藏真实回归。验证应给出失败率、p50/p95 或稳定的行为断言，并在修复后连续冷/热运行。游戏映射：帧时间、加载时间和网络延迟测试必须区分噪声与退化，否则发布门禁会在真正事故前失去可信度。
</details>
