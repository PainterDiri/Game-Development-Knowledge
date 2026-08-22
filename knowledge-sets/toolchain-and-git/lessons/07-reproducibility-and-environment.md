# 7. 可复现性与环境：锁版本仍然不够

## 7.1 先区分三种“相同”

工程讨论里“结果相同”常常没有定义。至少区分：

1. **字节级相同**：文件每个字节都相同，适合同平台、同工具链的严格复现；
2. **内容等价**：忽略已声明的时间戳、签名或容器差异，核心内容相同；
3. **行为等价**：相同输入、seed 和操作序列下，游戏行为满足同样性质。

跨 Windows、macOS、Linux 或不同代码签名环境时，字节级相同往往不是合理目标；但“行为等价”也不能被用来掩盖随机错误、丢资产或错误配置。你必须先写清本项目采用哪种判定。

## 7.2 可复现构建是输入控制问题

把构建写成函数：

```text
output = F(
    source_commit,
    asset_metadata,
    engine/compiler,
    direct_dependencies,
    transitive_dependencies,
    target_platform,
    build_config,
    environment_allowlist,
    clock_policy,
    random_seed,
    network_inputs
)
```

只锁定 Unity/UE 或 Python 版本，不能保证函数输入完整。常见隐藏输入包括：

- 间接依赖没有锁定，包管理器重新解析到了新版本；
- 本地环境变量改变了平台、区域、路径或功能开关；
- 当前时间进入压缩包、生成代码或 manifest；
- 目录遍历顺序依赖文件系统实现；
- 构建脚本读取用户目录里的配置；
- 网络服务返回了未固定的内容；
- 上一次构建留下的缓存包含旧导入结果；
- 肉鸽生成器使用当前时间或共享的全局随机流。

**可复现不是“每次恰好成功”，而是能解释哪些输入允许改变结果，以及哪些输入必须固定。**

## 7.3 环境清单应该能变成命令

一份可用的环境清单至少包括：

```text
OS / CPU 架构：
语言与运行时：
编译器 / Unity Editor / Unreal Engine：
包管理器与锁文件：
平台 SDK / 构建模块：
插件与 LFS/Perforce 获取方式：
目标平台与配置：
允许的环境变量：
构建入口：
测试、冒烟和清理命令：
网络/许可证前提：
```

差的清单只写“Unity 2022、Windows、能联网”；好的清单能让别人知道如何判断自己的环境是否满足，并能在失败时区分“缺工具”“缺依赖”“权限失败”和“代码失败”。

## 7.4 用单变量实验定位差异

不要一次改十项配置。用如下实验矩阵：

| 实验 | 只改变的输入 | 预期观察 | 结论边界 |
|---|---|---|---|
| A | 同一提交、同一 seed、删缓存 | 语义结果应相同 | 验证缓存不是隐藏输入 |
| B | seed 42→43 | 行为/房间内容可能改变 | 源哈希不应因 seed 改变 |
| C | 版本 1.0→1.1 | manifest 版本改变 | 不代表游戏行为必须改变 |
| D | 工具版本改变 | 可能有字节差异 | 需要记录工具影响，不立即归因代码 |
| E | 关闭网络 | 若仍能构建，说明依赖可离线恢复 | 不能证明所有依赖已锁定 |

实践中的 `build.py` 会把源文件 SHA-256、seed、版本、Python 版本和 Git 提交写入 manifest。它没有证明整台机器完全可复现，但能把最重要的差异来源显式化。

## 7.5 随机系统必须把 seed 当成输入

在肉鸽里，seed 是内容输入，不是调试备注。房间图、掉落、敌人波次和装饰随机都可能依赖它。

一个容易出错的写法是共享全局随机流：

```python
rng = random.Random(seed)
room = generate_room(rng)
spawn_enemies(rng)
play_fx(rng)       # 新增一个视觉随机调用，改变了后续敌人结果
```

只增加一个不影响玩法的视觉随机调用，后续房间可能全部改变。更稳定的做法是按领域或位置派生随机上下文：

```python
room_rng = random.Random((run_seed * 1_000_003) ^ room_index)
room = generate_room(room_rng)
```

这不是绝对正确的随机架构，但它暴露了一个重要设计选择：**随机流的消费顺序是否属于稳定协议？** 如果答案是“是”，就要测试和版本化；如果答案是“否”，就应按领域拆分随机流或保存事件输入。

## 7.6 时间与路径污染

以下 manifest 不稳定：

```json
{
  "built_at": "2026-08-22T10:00:01+09:00",
  "source": "PROJECT_ROOT/src/game.py",
  "files": ["b.py", "a.py"]
}
```

问题分别是：当前时间、用户绝对路径、未排序列表。修复策略：

- 把 provenance 时间与 deterministic 字段分开；
- 只写仓库相对路径；
- 对文件列表排序；
- 对 JSON 使用稳定编码；
- 不把不可控的 runner ID 混入确定性哈希；
- 如果必须记录时间，明确它用于追踪而不是两次构建比较。

## 7.7 Unity 与 Unreal 的环境映射

### Unity

需要同时锁定 Editor、目标平台模块、Packages/lock 文件、脚本化构建入口和许可证/登录前提。`Library/` 可以作为 CI cache，但不能成为“项目能不能构建”的唯一来源。冷构建必须证明删除缓存后仍能导入关键资产并构建目标平台。

### Unreal Engine

需要锁定引擎安装或源码版本、编译器、插件、Config、目标平台 SDK 和构建配置。`DerivedDataCache/` 能显著加快导入，但新 runner 不能依赖某个开发者机器预热过的缓存。Automation/命令行/BuildGraph 入口应明确输出目录、目标配置和失败退出码。

## 本章实验：两次冷构建

```bash
cd code/repro-game
rm -rf dist /tmp/repro-a /tmp/repro-b
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-a
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-b
diff -ru /tmp/repro-a /tmp/repro-b
```

预期没有差异。然后分别改变 seed、版本和源码，观察哪些 manifest 字段改变。若两次相同输入出现差异，先查时间、路径、排序和随机，不要直接声称“Python 不可复现”。

## 本章结论

可复现工程不是一个工具品牌，而是一种输入纪律：把隐式输入变成显式字段，把不可控差异分类，把“相同”定义成可测试命题。下一章把这个模型放到 Git 的对象和资产协作中。

## 7.8 三种“相同”不要混用

可复现讨论经常因为“相同”没有定义而争论不休。至少区分三层：

| 层次 | 判定 | 适合哪里 | 不能推出什么 |
|---|---|---|---|
| 字节相同 | 文件逐字节相同，哈希一致 | 发布包、资源包、静态站点 | 不保证跨平台行为完全一致 |
| 内容等价 | 关键数据/规则一致，压缩或排序差异允许 | 导入数据库、部分资产转换 | 需要定义比较器，不是“看起来一样” |
| 行为等价 | 给定输入时运行结果满足同一性质 | 随机地图、物理模拟、跨平台游戏 | 不代表日志、浮点最后一位或帧时序完全一样 |

例如，同一 Unity 场景在不同平台可能产生不同导入缓存字节，但如果场景引用、碰撞层和关键运行时测试都一致，可能达到“行为等价”；反之，两个包哈希相同也不能证明它们在目标机器上有正确的 GPU、输入设备或 SDK 行为。

在 manifest 中明确你比较哪一层：

```json
{
  "comparison": {
    "artifact": "byte-identical",
    "room_generation": "behavior-equivalent",
    "import_cache": "not-a-release-input"
  }
}
```

## 7.9 用差分实验定位隐藏输入

遇到“同一提交两次结果不同”，先建立最小差分矩阵：

```text
基线：commit=C, seed=42, target=linux-x64, cache=clean, network=off
实验 1：只把 seed 改成 43
实验 2：只恢复缓存
实验 3：只把工具版本改成 T2
实验 4：只把目标改成 windows-x64
```

每次只改变一个输入，并记录：输出哈希、行为结果、manifest 差异和退出码。一个简易 shell 骨架如下：

```bash
set -eu
for seed in 42 43; do
  rm -rf "out-$seed"
  python3 src/build.py --output "out-$seed" --seed "$seed" --version 1.0.0
  sha256sum "out-$seed/game.py" "out-$seed/build-manifest.json"
done
```

如果 seed 改变导致 `src/game.py` 的哈希改变，说明构建污染了源目录；如果只有 manifest 的 provenance 改变，可能是预期；如果 `game.py` 也改变，则需要检查生成代码、平台换行、压缩时间戳或复制过程。每个观察都只能支持它实际覆盖的结论，不能从一次成功推断“整条供应链安全”。

## 7.10 随机流的可维护设计

共享随机流适合非常小的线性脚本，却会把调用顺序变成隐形接口：

```python
rng = Random(run_seed)
rooms = generate_rooms(rng)
spawn_fx(rng)          # 视觉改动改变了后续掉落
loot = generate_loot(rng)
```

更可维护的方案是用语义域派生随机源，并显式版本化派生规则：

```python
from random import Random


def rng_for(run_seed: int, domain: str, index: int, generator_version: int = 1) -> Random:
    key = f"{generator_version}:{run_seed}:{domain}:{index}".encode()
    # 教学示例：真实项目可使用稳定的哈希到整数映射。
    derived = int.from_bytes(__import__("hashlib").sha256(key).digest()[:8], "big")
    return Random(derived)

room_rng = rng_for(42, "room", 3)
loot_rng = rng_for(42, "loot", 3)
```

它的边界是：随机算法本身、浮点运算、并行调度和引擎版本仍可能影响结果；如果回放要求逐帧一致，必须进一步记录输入事件、时间步和版本，而不是只保存一个 seed。

## 7.11 环境清单如何变成“可失败”的检查

好的环境清单不只是文档，它能主动失败：

```bash
python3 --version
python3 -c 'import sys; assert sys.version_info >= (3, 11)'
git --version
git rev-parse --show-toplevel
```

Unity/UE 项目也应提供等价的 `doctor` 或 CI 步骤：检查 Editor/Engine 版本、目标模块、插件版本、SDK、锁文件和许可证状态。检查失败时返回非零退出码，并指出“缺工具 / 版本不匹配 / 依赖下载失败 / 权限不足”，而不是只打印“build failed”。

### 本节验收

完成一次“同一提交、同一 seed、冷缓存、网络关闭”的构建比较；再只改一个输入并解释哪些字段应改变。你的答案至少要说明比较层次（字节/内容/行为）和无法由实验推出的结论。
