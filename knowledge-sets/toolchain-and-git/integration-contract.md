# 主项目接缝：可复现运行上下文

本课程不要求把 Python 小实验硬塞进 Unity。它交付的是一个可以被 Unity 主项目消费的**运行上下文契约**：同一份内容版本和 seed 应能解释同一局测试、构建和回归报告。

## 最小契约

| 字段 | 类型 | 所有者 | 规则 |
|---|---|---|---|
| `contentVersion` | string | 内容/发行流程 | 内容数据改变时递增或更换，不使用当前时间代替版本； |
| `buildId` | string | 构建流程 | 标识一次构建，可由提交短哈希和目标平台组成； |
| `seed` | integer | 局内规则 | 所有需要复现的随机入口显式接收，禁止隐式读取全局时间； |
| `runId` | string | 运行时 | 标识一次运行，不参与决定性规则，便于日志关联； |
| `schemaVersion` | integer | 数据协议 | 变更存档、日志或回放结构时递增； |

## Unity 适配方式

在 Unity 项目中保留一个很薄的适配层，例如 `Assets/Game/Diagnostics/RunContext/`：

1. 启动时由构建/测试入口注入 `contentVersion`、`buildId` 和 `seed`；
2. 规则系统只依赖 `IRunContext` 或等价的领域接口，不直接读取 `Application.persistentDataPath`、系统时间或编辑器状态；
3. 日志、回放、失败截图和自动化测试都打印 `buildId + contentVersion + seed + runId`；
4. 调试入口可以强制指定 seed；正式玩家入口可以随机生成 seed，但必须把实际值写入本局记录；
5. 任何解析失败都明确拒绝、回退到安全默认值，或标记本局不可复现，不静默吞错。

这份契约只规定跨课程稳定的输入和证据，不规定 Unity 场景、Prefab 或日志库的具体实现。后续课程可以在不破坏规则层的前提下替换编辑器工具、网络传输或发行平台。

## 验收

- 同一 `contentVersion + seed` 在同一构建中能重现房间图、掉落或敌人波次的测试结果；
- 失败报告至少包含 `buildId`、`contentVersion`、`seed`、`runId` 和最小复现步骤；
- 改变 `runId` 不改变规则输出；改变 `contentVersion` 时，测试能说明是否允许比较；
- Unity 工程删除 `Library/`、缓存或个人设置后，契约仍由版本化源文件和显式参数恢复。

## 当前课程的边界

Python 示例是引擎无关的参考实现，不是 Unity 运行时代码。若需要把它带入主项目，应重写为 C# 适配器并保留上述字段和验收，不要直接复制 Python 依赖或把测试产物当作游戏资产。
