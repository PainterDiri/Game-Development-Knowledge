# 实践：可复现的 seeded-room 小游戏

## 目标

在 `code/repro-game/` 中完成一个无引擎最小游戏的工程化闭环：固定 seed 生成房间、运行测试、从源构建 `dist/`、写入 manifest，并让第二次干净构建可比较。它不是为了替代 Unity/UE，而是用最少外部变量暴露工具链不变量。

## 环境

- Python 3.11+（仅使用标准库）
- Git 2.x
- macOS、Linux 或 Windows PowerShell；路径命令按系统调整

## 输入、输出与约束

- 输入：源码、`--seed`、`--version`、当前 Git 提交（若可用）。
- 输出：`dist/game.py`、`dist/build-manifest.json`、终端测试/构建日志。
- 约束：不得依赖网络、用户目录、IDE、未声明环境变量或随机当前时间；不得提交 `dist/`。
- 允许修改：`code/repro-game/` 下的源码、测试、Makefile 和说明；不修改仓库级脚本。

## 验收证据

```bash
cd knowledge-sets/toolchain-and-git/code/repro-game
python3 -m unittest discover -s tests -v
python3 src/build.py --output dist --seed 42 --version 1.0.0
python3 dist/game.py --seed 42
cat dist/build-manifest.json
```

必须满足：

1. 测试全部通过，并至少覆盖一个固定 seed 的房间输出；
2. 构建前清理/重建输出目录，不携带旧文件；
3. manifest 有版本、seed、源文件哈希、构建命令和提交信息；
4. 两次相同输入构建的 `game.py` 和 manifest 内容相同（允许 manifest 中明确声明的非确定字段，但本参考实现不生成它）；
5. `dist/` 在 `.gitignore` 中被排除；
6. 修改 seed 后，行为证据改变但源码哈希不应改变；
7. 至少制造一次故意失败：删掉源码、改变期望 seed、或在构建脚本中引入未声明时间输入，并写出如何诊断。

## 最小版本（时间不足时）

只完成 `generate_room(seed)`、两个 unittest、稳定 manifest 和 `build.py`；不要求制作图形界面。完成后再做 Git 冲突或 CI 微实验。

## 向引擎迁移

- Unity：把 `src/build.py` 的 manifest 思路迁移到 Editor 脚本；把 seed 和内容版本写入开发构建 HUD/日志；把 `Library/` 保持为缓存。
- UE：把命令入口迁移到 Automation/BuildGraph 或项目脚本；将引擎版本、目标平台、配置和插件列入 manifest；把 `DerivedDataCache/` 保持为缓存。
- 专业项目：把 manifest 与符号、测试报告、资产版本和构建服务的构建 ID 关联，回滚直接复用已验证 artifact。
