# runtime-kit：C 运行时组件参考基线

这是课程主实践的**参考代码**，不是唯一答案。它只依赖 C17 标准库和一个编译器，不包含 Unity/UE 工程、缓存或平台资产。

## 构建与运行

```bash
make clean test
make asan
```

预期输出：

```text
runtime-kit: all tests passed
```

`make asan` 使用 AddressSanitizer 与 UndefinedBehaviorSanitizer；若当前编译器不支持，可先运行 `make test`，再用平台调试器验证。

## 设计约束

- 固定容量 `RG_RUNTIME_MAX_ENEMIES`，不在每次波次生成时动态分配；
- seed 显式进入 `rg_runtime_init`，同 seed、同调用序列产生同 checksum；
- 容量失败发生在任何写入之前，因此失败调用不改变状态；
- `RgRuntime` 的生命周期由调用者拥有，规则函数不接触引擎对象；
- 公开 API 通过 `RgResult` 返回错误，`rg_runtime_get_enemy` 用调用者提供的输出缓冲区；
- checksum 只用于测试/诊断，不是加密哈希，也不替代正式序列化校验。

## 已知限制

示例 RNG 只用于教学和可复现玩法，不适合密码学；浮点位置的 checksum 只保证当前构建/调用序列的测试用途，跨平台回放应采用明确的定点或序列化协议；示例没有线程同步和持久化版本迁移。
