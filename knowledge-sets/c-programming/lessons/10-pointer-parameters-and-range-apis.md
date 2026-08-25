# 10. 指针参数、输出参数与区间 API：把契约写进签名

上一章解释了指针，但“会解引用”还不够：一个函数如何返回成功/失败和多个结果？如何避免把数组边界藏在调用者猜测中？本章把指针变成可审计的 API。

## 输出参数的三问

```c
#include <stdbool.h>
#include <stddef.h>

bool find_min_max(const int *values, size_t count,
                  int *out_min, int *out_max) {
    if (!values || count == 0 || !out_min || !out_max) return false;
    int min = values[0];
    int max = values[0];
    for (size_t i = 1; i < count; ++i) {
        if (values[i] < min) min = values[i];
        if (values[i] > max) max = values[i];
    }
    *out_min = min;
    *out_max = max;
    return true;
}
```

读这个签名时固定问：

1. 谁拥有 `values`？本函数只读，调用者保持有效；
2. `count` 是否允许 0？不允许，因为需要 `values[0]`；
3. `out_min/out_max` 何时写入？只有成功时写入。

返回 `bool` 表示成功/失败，输出参数携带结果；失败时不留下半更新状态。也可以返回结构体，选择取决于 ABI、可读性和错误信息需求。

## 区间而不是“裸指针神秘长度”

对于数组片段，用 `{pointer, count}` 的概念表达半开区间 `[begin, begin + count)`。半开区间的好处是空区间自然表示为 `count=0`，相邻区间不重复，长度可用尾减首得到。不要把 `strlen` 用在任意二进制数据上，因为 `0` 字节可能是合法内容。

## 失败：输出参数别名

若调用 `find_min_max(values, n, &values[0], &values[1])`，输出写入可能覆盖输入，调用契约要么禁止重叠，要么先计算局部结果后统一写回。参考实现使用局部 `min/max`，把别名影响限制到最后一步。

## 游戏映射与验证

把“采样一波敌人的最小/最大速度”“计算碰撞包围盒”写成 `pointer + length + out` API；测试空区间、单元素、负值、输出指针为空和输入输出重叠。下一章必须回答一个更难的问题：如果结果或数组需要活过当前函数，谁负责分配和释放？
