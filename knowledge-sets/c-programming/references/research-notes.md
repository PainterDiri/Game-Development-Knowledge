# C 程序设计 · 研究笔记

研究日期：2026-08-25。正文以 C17 可移植核心为主；链接记录了访问版本/页面，课程只使用支持具体结论的部分。

## 1. C 对象、类型、表达式与库边界

- **问题**：如何解释对象、存储期、指针、数组、结构体、转换和标准库 I/O，而不把实现细节冒充语言保证？
- **来源**：[ISO/IEC 9899:2011 draft N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf) — WG14，2011 草案，访问日期：2026-08-25。
- **关键事实（自己的话）**：N1570 公开描述了翻译环境、对象/类型、转换、声明、数组、函数、结构体/联合、指针运算、内存管理与 I/O 的规范边界。
- **对课程的影响**：第 1–14、18 章以标准概念为骨架；涉及对象生命周期、数组半开范围、指针有效性和 `sizeof` 时不依赖某台机器的偶然布局。
- **不确定性/冲突**：N1570 是 C11 草案而非当前 ISO 标准；课程使用其可公开核对的核心条款，并在 C23 迁移注记中提醒版本差异。
- **是否进入正文**：是。它是对象模型和标准库结论的主要依据。

## 2. 编译器警告与标准方言

- **问题**：如何把类型转换、遮蔽和可疑代码尽量提前暴露？
- **来源**：[GCC Warning Options](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html) 与 [GCC C Dialect Options](https://gcc.gnu.org/onlinedocs/gcc/C-Dialect-Options.html) — GNU Project，当前在线手册，访问日期：2026-08-25。
- **关键事实（自己的话）**：`-Wall`/`-Wextra` 是一组警告而非正确性证明；`-Wconversion`、`-Wshadow` 等更严格选项需要结合项目噪音预算；`-std=c17` 约束语言方言。
- **对课程的影响**：所有实践以 `-std=c17 -Wall -Wextra -Wconversion -Wshadow -pedantic` 为基线，区分警告、编译错误和运行时错误。
- **不确定性/冲突**：不同 GCC/Clang 版本启用的警告集合略有差异；正文不依赖某条非标准扩展。
- **是否进入正文**：是。第 1、3、6、15、17 章直接使用。

## 3. 动态内存与 Sanitizer

- **问题**：如何验证越界、use-after-free 和未定义行为，而不是凭崩溃猜测？
- **来源**：[Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)、[Clang UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)、[GCC Instrumentation Options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html) — LLVM/GNU Project，当前在线文档，访问日期：2026-08-25。
- **关键事实（自己的话）**：ASan/UBSan 通过插桩在运行时检测一组内存和未定义行为；它们有额外开销，覆盖不到的路径仍可能有问题，不能代替测试或发布配置。
- **对课程的影响**：第 11、15、16 章提供可运行的编译命令、故意失败和修复后回归测试。
- **不确定性/冲突**：Apple 平台、GCC、Clang 的支持范围和报告格式不同；学习者若工具不可用，可使用调试器/Valgrind，但不能把“没有报告”当成证明。
- **是否进入正文**：是。

## 4. Unity/Unreal 的 C 边界

- **问题**：C 组件如何进入 Unity/UE，同时不把领域规则绑死在引擎对象上？
- **来源**：[Unity Native plug-ins](https://docs.unity3d.com/Manual/NativePlugins.html) — Unity Technologies，在线手册，访问日期：2026-08-25；[Programming with C++ in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/programming-with-cplusplus-in-unreal-engine) — Epic Games，在线文档，访问日期：2026-08-25。
- **关键事实（自己的话）**：Unity 原生插件需要处理平台构建和托管/原生调用边界；UE C++ 代码在引擎模块、反射和对象生命周期框架中运行。跨边界的数据、调用约定、符号、所有权和线程都必须显式。
- **对课程的影响**：第 18 章只交付不透明句柄、标量/快照、错误码和薄适配器原则，不编造某个引擎版本的私有实现。
- **不确定性/冲突**：具体插件目录、平台命名、UE 模块模板会随版本变化；这些 API 细节不作为 C 核心知识的前置。
- **是否进入正文**：是，但明确标为迁移边界，不把平台示例当作唯一方案。

## 5. C23 版本注记

- **问题**：课程应使用最新标准还是最大化跨编译器可运行性？
- **来源**：[WG14 C language standards information](https://www.open-std.org/jtc1/sc22/wg14/www/projects) — ISO/IEC JTC 1/SC 22/WG 14，访问日期：2026-08-25。
- **关键事实（自己的话）**：C 标准持续演进；C23 已成为新一代标准，但编译器和平台库支持存在差异。
- **对课程的影响**：课程核心选用 C17 语法/库交集，另写迁移说明；学习者可以在完成实践后尝试 `-std=c23`，但必须保留 C17 构建证据。
- **不确定性/冲突**：不同工具链对 C23 的实现进度不同；不能仅凭 `__STDC_VERSION__` 推断全部库特性。
- **是否进入正文**：部分进入 README，避免让版本热度挤压对象/内存原理。
