# 15. 未定义行为、Sanitizer 与调试器：先获得证据再猜

前面多次出现“可能看起来没问题”的错误。C 把某些行为留给实现或直接规定为未定义（undefined behavior, UB）：标准不再要求结果，优化器可以基于“程序不会这样做”推导。UB 不是一种特殊的崩溃，而是程序失去可推理性。

## 三类结果不要混淆

- **定义行为**：标准规定可观察结果；
- **实现定义/未指定**：实现选择或顺序未固定，文档/测试要记录；
- **未定义行为**：标准不保证任何结果，例如越界、use-after-free、有符号溢出、错误解引用。

编译器警告只能发现部分问题；动态工具负责观察运行路径。用 Clang/GCC：

```bash
cc -std=c17 -Wall -Wextra -Wconversion -Wshadow -pedantic \\
   -fsanitize=address,undefined -g demo.c -o demo
./demo
```

AddressSanitizer 常能报告越界、use-after-free、double-free；UBSan 能捕捉若干整数、对齐、类型和控制流问题。它们改变性能和内存布局，不能当作最终发布配置，也不能证明未覆盖路径没有 bug。

## 最小诊断流程

1. 固定输入：seed、文件、命令和构建器版本；
2. 让失败稳定重现；
3. 用警告缩小到编译期问题；
4. 用 Sanitizer 运行最小样本；
5. 用 `lldb`/`gdb` 断点、查看栈和局部变量；
6. 修复根因，增加回归测试；
7. 在无 Sanitizer 配置再次运行，确认不是只修了工具症状。

## 故意失败

```c
int values[2] = {1, 2};
return values[2]; // 越界读取
```

如果只打印 `0` 并不代表合法。运行 Sanitizer，记录报告指向的源行；再把测试加入实践目录。游戏里的“偶现崩溃”通常需要 build ID、seed、回放/输入和最小复现，而不是一张模糊截图。

下一章将把警告和 Sanitizer 之外的正确性证据变成单元测试、不变量和可重复基准。

> 参考：[Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)、[Clang UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)、[GCC Instrumentation Options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)。
