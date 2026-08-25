# 11. 动态内存与所有权：`malloc` 成功不等于设计正确

自动对象在函数返回时结束；房间状态、可变敌人列表和加载后的资源可能要活得更久，于是需要动态存储期。动态内存最危险的地方不是语法，而是**所有权**：谁申请、谁能修改、谁在什么时候释放？

## 最小生命周期

```c
#include <stdlib.h>
#include <stddef.h>

int *make_scores(size_t count) {
    if (count == 0) return NULL;
    int *scores = malloc(count * sizeof *scores);
    if (!scores) return NULL;
    for (size_t i = 0; i < count; ++i) scores[i] = 0;
    return scores; // 所有权转移给调用者
}
```

`malloc` 返回未初始化字节；`sizeof *scores` 避免重复写类型；乘法本身也可能溢出，所以真实组件还应先检查 `count > SIZE_MAX / sizeof *scores`。调用者必须在所有路径上 `free(scores)`，包括中途错误返回。

## 三类典型失败

- **泄漏**：丢失最后一个指针，内存永不释放；短程序可能隐藏它，长时间运行的游戏会逐局增长。
- **use-after-free**：释放后继续使用指针；指针值可能仍然看似有效。
- **double free**：同一块内存释放两次；常见于所有权不清或错误路径重复清理。

可以用“创建/销毁成对”约束：`enemy_buffer_init` 成功后恰好一次 `enemy_buffer_destroy`；destroy 后句柄置为零/空，避免误用。

## 固定容量通常是更好的游戏取舍

实时系统不一定要每次波次都 `realloc`。固定容量数组让内存上限、失败条件和帧内成本可预测；动态扩容适合编辑器工具、加载阶段或不确定输入，但扩容会移动对象并使内部指针失效。不是“动态更高级”，而是根据生命周期和预算选择。

## 验证

用 `-fsanitize=address,undefined` 运行三个故意失败版本；修复后重复运行并确认无报告。若工具不可用，至少在代码审查表写出每个分支的释放责任。Unity 的 GC、`NativeArray.Dispose`、UE 的容器/智能指针各有规则，但不会替你决定领域状态所有者。下一章把拥有的字节组织成结构体，并测量布局而不是猜测。

> 参考：[N1570 §7.22.3 内存管理函数](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)、[Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)。
