# 实践解法与失败诊断

<details>
<summary>最小提示</summary>

先读 `src/game.py` 和 `tests/test_game.py`，确认“同一 seed → 同一房间序列”的不变量；再看 `src/build.py` 如何清理输出、排序输入、计算 SHA-256 和写 manifest。不要先加引擎或依赖。
</details>

<details>
<summary>推荐路线</summary>

1. 先运行测试，记录基线；
2. 检查 `generate_room(42)` 的结果与测试断言；
3. 运行构建，检查 `dist/` 是否只有预期文件；
4. 删除 `dist/` 后再构建并用 `diff -ru` 比较；
5. 改 seed 42→43，确认行为/manifest 的 seed 变化；
6. 用 `git status --ignored` 检查 `dist/` 被忽略；
7. 制造一次失败，再把失败原因归类为输入、工具、源、缓存或测试问题。
</details>

<details>
<summary>参考验收命令与预期</summary>

```bash
cd knowledge-sets/toolchain-and-git/code/repro-game
python3 -m unittest discover -s tests -v
rm -rf dist /tmp/repro-first /tmp/repro-second
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-first
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-second
diff -ru /tmp/repro-first /tmp/repro-second
python3 dist/game.py --seed 42
```

预期：测试通过；差异命令无输出；游戏打印固定房间路线和 checksum；`build-manifest.json` 可读且列出输入。
</details>

<details>
<summary>常见失败与诊断</summary>

- **两次 manifest 不同**：检查是否写入当前时间、无序遍历、绝对路径或随机生成的构建 ID；将路径归一化、列表排序，并把时间移出确定性字段。
- **删掉 dist 后仍能“通过”**：测试可能只测源码，不测构建输出；增加对 `dist/game.py` 的启动冒烟。
- **改 seed 后源码哈希变化**：构建脚本把生成结果写回源目录；生成数据应留在输出或临时目录。
- **Windows 失败、Unix 成功**：检查路径分隔符、大小写、编码和 shell 语法；Python 代码优先使用 `pathlib`。
- **Git 把 dist 显示为未跟踪**：`.gitignore` 作用域或目录层级错误；用 `git check-ignore -v dist/game.py` 查匹配规则。
- **bisect 结果不稳定**：测试依赖时间/网络/脏工作树；让测试只写临时目录，并固定 seed。
</details>

<details>
<summary>替代方案与迁移</summary>

可以用 Make、PowerShell 或 CMake 作为入口，只要入口在干净 checkout 可运行、失败退出码非零、输出有 manifest。Unity/UE 的构建脚本不必复制 Python 实现；复制的是不变量：显式版本、清理输出、固定随机、可下载证据和可回滚产物。
</details>
