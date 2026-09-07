# repro-game：可复现房间生成与构建基线

语言与环境：Python 3.11+、Git 2.x、POSIX shell（核心 Python 代码只用标准库）。这是课程主实践的可运行基线，不是完成答案。

```bash
python3 -m unittest discover -s tests -v
python3 src/build.py --output dist --seed 42
python3 dist/game.py --seed 42
python3 src/build.py --output dist --clean
```

预期：9 个测试通过；构建输出 `built dist`；运行结果包含 seed、checksum 和 5 个房间；清理只删除 manifest 声明拥有的产物。`src/build.py` 会拒绝未知文件、符号链接、受保护目录和不受信任 manifest。

已知限制：这不是通用构建系统或安全沙箱；没有外部依赖、平台 SDK、Unity/UE 资产导入或远程 CI。实践要求学习者在个人副本中创建 Git 历史、改变规则/测试、注入失败并完成 bisect、修复与回滚，不能把原样运行当作掌握。
