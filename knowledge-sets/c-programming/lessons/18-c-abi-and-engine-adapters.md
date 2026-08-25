# 18. C ABI 与引擎适配：把稳定内核交给 Unity/UE

最后的问题不是“如何把 C 代码复制进引擎”，而是“哪些边界需要稳定”。Unity Native Plugin 通常通过 C 导出函数被 C# P/Invoke 调用；UE 可以把纯 C 代码编译进模块，再由 C++ 封装。两者都要求明确 ABI、布局、字符串、线程和所有权。

## 稳定的 C 边界

```c
#ifdef __cplusplus
extern "C" {
#endif

typedef struct RgRuntimeHandle RgRuntimeHandle;
RgRuntimeHandle *rg_runtime_create(unsigned int seed);
void rg_runtime_destroy(RgRuntimeHandle *handle);
int rg_runtime_spawn_wave(RgRuntimeHandle *handle, unsigned int count);

#ifdef __cplusplus
}
#endif
```

`extern "C"` 防止 C++ 名字改编，让链接器能按 C 名称找到函数；不透明句柄让调用者不能依赖内部结构体布局。返回值使用固定、文档化的错误码；跨边界尽量传标量、固定布局的 POD 结构或调用者提供的缓冲区，不把“由库分配、由另一语言释放”的指针当默认方案。

## Unity 与 UE 的分工

- **Unity**：C# 适配器拥有 `IntPtr` 句柄和 `Dispose`/生命周期；`DllImport` 声明调用约定；规则输入用显式 seed；渲染对象由 C# 创建。
- **Unreal Engine**：C++ 模块拥有 RAII 包装器，蓝图只接触经过封装的高层类型；不要让 C 核心直接依赖 `UObject` 反射或世界状态。
- **两者共同**：版本化二进制、平台构建矩阵、结构体对齐、线程归属、错误码和回滚 artifact 都必须进入构建/发布证据。

## 不要跨边界的东西

不要把 `FILE *`、C 标准库分配的字符串、内部指针、编译器特有 bit-field、未版本化结构体直接暴露给 C# 或蓝图。若必须传文本，约定 UTF-8、字节数和释放者；若必须传数组，采用“调用者提供缓冲区 + capacity + out_count”。

## 验证与交付

即使没有安装引擎，也能做 ABI 烟测：用一个 C++ 小程序链接 C 实现，调用 `create → spawn → read → destroy`；再用 `nm`/`objdump`（平台可用时）检查导出符号。正式接入前保存一个可回滚的静态库/动态库 artifact、编译器版本和测试报告。

这就是本课的迁移出口：不是“C 比 C# 快”的口号，而是能解释对象、生命周期、数据布局、错误和工具如何在语言/引擎边界上保持可验证。后续数据结构课会在这个组件上增加可变容器；计算机组成课会解释缓存、调用约定和指令层成本。

> 参考：[Unity Native plug-ins 手册](https://docs.unity3d.com/Manual/NativePlugins.html)、[Unreal Engine C++ 编程文档](https://dev.epicgames.com/documentation/en-us/unreal-engine/programming-with-cplusplus-in-unreal-engine)。
