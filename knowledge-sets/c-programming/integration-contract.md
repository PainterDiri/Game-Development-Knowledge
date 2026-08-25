# 主项目接缝：F1 运行时基础库

本课程采用 `integrationMode=export`：先独立验证 C 组件，再由 Unity/UE 适配层消费一个稳定、窄小的 C ABI。C 代码不是主项目的场景逻辑，也不拥有引擎对象。

## 接缝输入/输出

| 方向 | 数据 | 所有者 | 规则 |
|---|---|---|---|
| 进入 | `seed: uint32_t` | 本局规则/测试入口 | 显式传入；不读取当前时间决定规则 |
| 进入 | `waveCount: size_t` | 调用者 | 先做容量校验；失败不改状态 |
| 返回 | `RgResult` | C 组件 | `RG_OK` 或文档化错误码；不能只写日志 |
| 返回 | `RgEnemy` 快照 | 调用者输出缓冲区 | 成功时写入；调用者无需释放 |
| 诊断 | checksum、buildId、contentVersion、seed、runId | 适配/测试层 | checksum 只做回归证据，不当安全哈希 |
| 生命周期 | `RgRuntime`/不透明句柄 | 适配层 | create/init 与 destroy 成对；destroy 后不可调用 |

## Unity 适配原则

建议把 C# 代码放在 `Assets/Game/Interop/RgRuntime/`，只做：

1. 声明 `DllImport`/调用约定；
2. 把 `seed`、波次数量和调用结果转换成受控 C# 类型；
3. 把快照复制到 C# 领域模型，再由 `GameObject`/Prefab 表现；
4. 在 `Dispose` 或等价生命周期中释放 C 句柄；
5. 启动和失败日志打印 `buildId + contentVersion + seed + runId`。

不要从 C 层回调 Unity 主线程，不要让 C 层保存 `GameObject` 指针，不要让 C 分配的字符串跨边界而没有释放函数。

## Unreal Engine 适配原则

C++ 模块可以用 RAII 包装 C 句柄，把 `RgEnemy` 转为 UE 的领域/表现数据；蓝图只接触经过 C++ 封装的高层接口。C 核心不依赖 `UObject`、世界、Tick 或反射宏。若需要网络复制，复制的是明确的快照/事件，而不是裸内存布局。

## 版本与回滚

- `abiVersion` 变化时生成新的导出入口或拒绝加载旧库；
- 结构体、错误码、RNG 消费顺序变化时递增 `contentVersion`/schema，并说明是否允许比较旧回放；
- 构建 artifact 必须记录编译器、目标平台和 Sanitizer/Release 配置；
- 如果适配器冒烟失败，回滚到上一个 C 库 artifact，主 Unity 单机流程仍可运行。

## 主项目冒烟

最小冒烟只需：初始化固定 seed → 生成 1 波 → 读取 1 个快照 → 验证 health/位置在约定范围 → 销毁句柄。它不能替代独立 `make test`/`make asan`，也不能把引擎画面出现当作 C 规则正确的证据。
