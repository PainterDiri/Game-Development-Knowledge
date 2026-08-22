# 3. 可复现构建：锁定输入而非祈祷

## 三种“相同”

1. **字节级相同**：两个产物的每个字节相同，最强但跨平台/签名/压缩器常不现实。
2. **内容等价**：忽略已声明的时间戳、签名或容器差异，核心文件和资源相同。
3. **行为等价**：同一输入和测试序列下游戏行为一致，例如相同 seed 生成相同房间图。

课程主实践要求 manifest 和行为可复现；不会把不同平台可执行文件强行比较为字节相同。

## 构建输入清单

```text
commit/tree
language runtime + compiler/editor
SDK/target platform
third-party dependency lock
project configuration
environment variables (allowlist)
clock/random/network inputs
build command + entry point
```

**机制**：构建程序只是函数的近似；任何未记录的读取都是隐藏输入。常见隐藏输入包括当前时间、机器路径、用户名、未锁定网络依赖、全局环境变量、随机种子、缓存内容、未提交资产和“上次构建留下的文件”。

**取舍**：完全隔离的容器/固定镜像提高复现性，却增加镜像维护成本；只锁主版本简单，但不能保证补丁行为；把所有依赖 vendoring 进仓库有离线优势，却增加体积和许可证维护。选择应和项目风险匹配，并写出失败时的替代路径。

## 游戏工程的可操作约定

- 将“内容版本”和“代码版本”同时记录在构建 manifest；肉鸽掉落表改动可能改变复现，即使代码没变。
- 游戏随机使用显式 seed，并区分随机流（房间生成、敌人 AI、视觉抖动）；不要从全局时间随机取数。
- 构建脚本先清理输出目录，再生成产物；不把旧文件误当作新构建成功。
- 构建失败要在第一处错误终止，记录命令、退出码、工具版本和日志路径。
- 依赖下载失败与代码编译失败是不同故障类别；日志应让两者可区分。

## Unity / UE 命令行迁移

Unity 的通用形态是用锁定的 Editor 版本在 batch/headless 模式调用一个公开的构建方法；方法内部读取版本控制中的场景、地址/资源配置并写出目标目录。UE 的通用形态是用锁定的引擎、平台 SDK 和命令行参数调用 Automation/BuildGraph/打包工具。两者都需要：

- 清晰的 checkout 和生成目录边界；
- 明确的目标平台、配置（Development/Shipping 等）和符号策略；
- 测试先于昂贵打包；
- 上传产物、manifest、日志和测试报告；
- 记录许可证、平台模块和秘密注入方式，不把密钥写进仓库。

不要把这段原则误读成一个跨版本命令模板：引擎 CLI 参数和项目格式会变，实际项目必须以锁定版本官方文档为准。

## 验证实验

主实践中的 `src/build.py` 将源码复制到 `dist/game/`，按稳定顺序生成 `build-manifest.json`，并以显式 seed 运行 smoke test。你需要运行两次并比较：

```bash
rm -rf dist
python3 src/build.py --output dist --seed 42
sha256sum dist/game.py dist/build-manifest.json
cp -R dist /tmp/repro-first
rm -rf dist
python3 src/build.py --output dist --seed 42
diff -ru /tmp/repro-first dist
```

然后改变一个输入：`--seed 43` 应改变行为证据但不应悄悄改变源文件；改变 `--version` 应改变 manifest；在构建脚本中加入当前时间则暴露未声明输入。实验的重点不是“永远零差异”，而是能解释差异来源。
