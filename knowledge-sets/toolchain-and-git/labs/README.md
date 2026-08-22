# 主实践：可复现的 seeded-room 小游戏

## 你要交付什么

完成一个不依赖引擎的最小游戏工程，让别人能在干净 checkout 中：

```text
运行测试 → 用显式 seed 构建 → 读取 manifest → 启动产物 → 复现一次故意失败
```

实践不是写一份报告，而是留下可以运行、解释和复现的工程证据。

## 环境与入口

- Python 3.11+（标准库即可）
- Git 2.x
- macOS、Linux 或 Windows PowerShell
- 代码入口：`code/repro-game/`

```bash
cd knowledge-sets/toolchain-and-git/code/repro-game
python3 -m unittest discover -s tests -v
python3 src/build.py --output dist --seed 42 --version 1.0.0
python3 dist/game.py --seed 42
```

## 三个 checkpoint

### A · 确定性

实现/理解 `generate_room(seed, room_index)`：

- 同一 seed 和 room index 结果相同；
- 不同 seed 至少有一项运行证据不同；
- 每个房间保留入口、出口和宝物不变量。

验收：测试通过，固定 seed 输出可复跑。

### B · 可重建

让 `build.py`：

- 构建前清理输出；
- 只从源码和显式参数生成 `dist/`；
- 生成包含版本、提交、Python、seed、命令和源文件哈希的 manifest；
- 同一输入两次构建结果一致；
- `dist/` 不进入 Git。

验收：两次 `diff -ru` 无差异，`git check-ignore -v dist/game.py` 命中忽略规则。

### C · 可诊断

故意引入一个只在 `seed=7, room_index=3` 触发的缺出口回归：

- 测试失败信息必须包含 seed 和 room；
- 日志/断言能指出第一个坏不变量；
- 用两个提交演练手动二分或 `git bisect run`；
- 修复后保留回归测试。

验收：能从报告复现、定位、修复，并证明其他 seed 的基础不变量仍通过。

## 允许修改与限制

允许修改 `code/repro-game/` 下源码、测试、Makefile 和说明。不修改仓库级脚本，不依赖网络，不读取用户目录，不把当前时间当作随机 seed，不提交 `dist/` 或 `__pycache__/`。

## 时间不足的最小版本

只完成 A+B：四个测试、稳定 manifest、两次相同输入构建和产物冒烟。之后再完成 C；不要通过删掉验收项来宣称“可复现”。

## 失败清单

至少制造一种失败并保留诊断过程：

- 删除源码后构建失败；
- 改变 seed 后行为变化但源码哈希不变；
- 把当前时间写入 deterministic manifest 后，两次比较失败；
- 让 `dist/` 不被忽略后用 `git check-ignore` 找出规则缺失。

## Unity/UE 迁移

完成 A+B 后，任选一个引擎项目写一份不超过一页的迁移表：

```text
Python 输入/输出 | Unity 对应物 | Unreal 对应物 | 额外依赖 | 验证命令/证据
```

至少覆盖：项目版本、随机 seed、构建入口、缓存目录、产物、manifest、测试/冒烟。迁移表可以放在个人练习目录，不要求提交到公开课程。
