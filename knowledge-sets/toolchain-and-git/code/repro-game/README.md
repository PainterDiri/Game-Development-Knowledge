# Repro Game

这是 `toolchain-and-git` 的最小可运行实践代码。它只依赖 Python 标准库，故意把随机种子、源码哈希、提交和构建命令写入 manifest。

```bash
python3 -m unittest discover -s tests -v
python3 src/build.py --output dist --seed 42 --version 1.0.0
python3 dist/game.py --seed 42
```

`dist/` 是产物，不应提交。修改 `src/game.py` 后重新运行测试和构建；如果要检验确定性，删除 `dist/` 并用完全相同参数构建两次比较输出。
