# 2. 环境与依赖：锁版本仍不够

## “锁版本”解决了什么？

版本锁定（pinning）把“任意可用版本”缩小为一个声明版本，例如 Python 3.12、Unity 某个 LTS、UE 某个引擎版本、目标平台 SDK 和包锁文件。但构建仍可能读取：

- 未锁定的间接依赖；
- 当前时间、用户目录、区域/编码和路径大小写；
- 全局环境变量、代理、许可证和平台 SDK；
- 网络上今天与昨天不同的下载内容；
- 上一次构建留下的缓存；
- 没有进入提交的内容表或随机 seed。

因此可复现构建不是一句“我们用同一个版本”，而是把构建函数的输入写出来：

```text
output = F(commit, tools, dependencies, config, platform,
           env_allowlist, clock, random_seed, network_inputs)
```

## 三种相同

1. **字节相同**：每个字节一致，跨平台通常最难；
2. **内容等价**：忽略已声明的时间戳、签名或容器差异后，核心文件一致；
3. **行为等价**：相同 seed 和输入序列下，游戏行为和不变量一致。

课程实践要求 deterministic manifest 和行为等价；不会把 macOS 与 Windows 的可执行文件强行要求字节相同。

## 从环境清单到最小命令

环境说明至少写：

```text
操作系统/架构
语言运行时与编译器
Unity/UE/SDK/包版本
依赖锁文件或校验和
目标平台与构建配置
允许注入的环境变量
构建入口与清理策略
测试与冒烟命令
```

优先让构建脚本使用 `pathlib`、稳定排序和仓库相对路径；不要把用户绝对路径写进 manifest。网络依赖如果不能完全离线，应记录下载来源、校验方式、缓存失效策略和失败分类。

## 游戏随机是工程输入

肉鸽项目中，随机不是装饰：房间图、掉落、敌人波次和视觉抖动可能共享或分离随机流。至少记录：

- run seed；
- 内容/掉落表版本；
- 生成器版本；
- 房间或波次索引；
- 目标平台与随机实现版本。

不要在测试中使用“当前时间作为 seed”。那会让失败变成不可复现的截图。

## 冷构建实验

```bash
cd knowledge-sets/toolchain-and-git/code/repro-game
rm -rf dist /tmp/repro-first /tmp/repro-second
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-first
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-second
diff -ru /tmp/repro-first /tmp/repro-second
```

然后逐个改变输入：

- seed 42→43：行为证据应改变，源码哈希不应改变；
- version 1.0.0→1.0.1：manifest 应改变；
- 在脚本中加入当前时间：应暴露未声明的非确定字段；
- 修改源码但不改 seed：源码哈希和提交应改变，行为是否改变取决于改动。

**诊断顺序**：先比 manifest，再比源文件哈希，再比工具版本和环境，最后才怀疑压缩器或平台差异。

## 小检查

- [ ] 我能列出构建的显式输入和隐藏输入；
- [ ] 我能解释字节相同、内容等价、行为等价的区别；
- [ ] 我能让肉鸽失败报告包含 seed、内容版本和最小位置；
- [ ] 我能设计一次“只改变一个输入”的复现实验。
