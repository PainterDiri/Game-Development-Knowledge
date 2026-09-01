# 7. 数组与连续内存：长度不是从指针里自动长出来的

运行时要批量更新敌人。C 数组把元素连续放置，带来缓存友好和简单布局，也把边界责任交给 API。最危险的误解是：函数收到 `int values[]` 就知道调用者数组有多少元素。

## 7.1 数组对象与索引

```c
int health[3] = {10, 8, 5};
for (size_t i = 0; i < 3; ++i) printf("%d\n", health[i]);
```

数组包含三个 `int` 对象，合法下标为 0、1、2。`health[3]` 已越过对象末尾。`sizeof health / sizeof health[0]` 只有在 `health` 仍是数组对象的作用域内才得到元素数。

```c
void tick(int health[]) {
    size_t count = sizeof health / sizeof health[0]; /* 错：参数已调整为指针 */
}
```

数组参数会调整为指针参数，函数必须显式接收长度：

```c
void tick(int *health, size_t count) {
    for (size_t i = 0; i < count; ++i) --health[i];
}
```

## 7.2 容量、长度与空区间

长度是当前有效元素数，容量是可容纳的最大元素数。二者混用会导致读取未初始化元素或写穿内存。API 应定义 `values == NULL, count == 0` 是否表示合法空区间；若 count 大于 0，NULL 必须失败。

结构体包装可以把关系保存起来：

```c
typedef struct { int *data; size_t length; size_t capacity; } IntBuffer;
```

但字段公开意味着任何调用者都能破坏 `length <= capacity`；更严格的模块会隐藏结构体定义，只暴露操作函数。

## 7.3 搜索、交换删除和排序

线性搜索是 O(n)，它按顺序检查有效区间。若不要求顺序，删除元素可用末尾交换，O(1) 删除但改变顺序；若顺序是游戏设计的一部分，则需移动后续元素，O(n)。算法选择必须写入不变量和调用者可见语义，而不能只追求“快”。

## 7.4 越界的故意失败

把 `i < count` 改为 `i <= count`，小数组也会写一个越界元素。普通运行可能“没崩”，这只是相邻内存暂时可写，不是合法性证明。使用 ASan：

```bash
cc -std=c17 -Wall -Wextra -fsanitize=address -g demo.c -o demo
./demo
```

预期报告 stack-buffer-overflow 或 heap-buffer-overflow。验证还要覆盖 0、1、恰好容量、超过容量和删除最后一个元素。

## 游戏映射

敌人池、投射物、顶点、输入事件和网络包都是“指针 + 长度/容量”问题。Unity 的 NativeArray、C++ 的 span-like 视图和 C 的显式区间表达的是同一契约：谁拥有存储、当前有效范围是什么、何时失效。

## 进一步拆解与实验

## 7.5 数组参数为什么必须带长度

函数参数中的数组会调整为指针，因此下面两个声明在参数位置等价：

```c
int sum_a(const int values[], size_t count);
int sum_b(const int *values, size_t count);
```

函数体内无法从 `values` 推出元素数量；`sizeof(values)` 得到的是指针大小，不是数组总字节数。长度必须成为显式契约。下面是**可编译函数片段**（需要与包含 `main` 的 C17 文件一起编译），因此显式列出它使用的头文件：

```c
#include <limits.h>
#include <stddef.h>
#include <stdbool.h>

bool sum_checked(const int *values, size_t count, int *out_sum) {
    if (out_sum == NULL || (values == NULL && count != 0)) return false;
    int sum = 0;
    for (size_t i = 0; i < count; ++i) {
        if ((values[i] > 0 && sum > INT_MAX - values[i]) ||
            (values[i] < 0 && sum < INT_MIN - values[i])) return false;
        sum += values[i];
    }
    *out_sum = sum;
    return true;
}
```

`values == NULL && count == 0` 是否允许，必须在 API 中写清；一种设计允许空集合，另一种设计要求指针永远非空。两者都可以，模糊才危险。

## 7.6 连续布局和缓存局部性

数组元素按索引连续排列（中间不插入别的元素），所以顺序扫描通常有良好局部性：CPU 取入一个缓存行时，附近元素也可能被带入。这个事实解释了为什么 O(n) 的数组扫描在中等规模下常常比“看起来更高级”的结构快。但不要从布局直接跳到性能结论；元素大小、访问模式、分支、分配和平台都要测量。

二维数组也有布局规则：C 的行主序意味着 `matrix[row][column]` 中相邻 column 更适合连续访问。遍历顺序错误不会必然出错，但可能制造明显缓存代价。课程重点是先证明索引范围，再讨论速度。

## 7.7 删除策略必须和规则绑定

稳定删除通常需要把后续元素左移，成本 O(n)：

```c
for (size_t i = index + 1; i < count; ++i) {
    values[i - 1] = values[i];
}
--count;
```

若元素顺序不重要，交换最后一个元素可以 O(1)：

```c
values[index] = values[count - 1];
--count;
```

交换删除会使 ID 到索引的映射失效，任何保存索引的调用者都可能指向另一个实体。更稳妥的 API 暴露稳定 ID 或句柄，而不是承诺内部索引永久不变。每一种删除方案都要测试 `count==0`、删除首/尾/中间和连续删除。

## 本章练习

### C07-Q1：改写错误的数组 API

`void update(int items[])` 内用 `sizeof` 计算数量。指出问题并给出安全签名。

<details><summary>最小提示</summary>

参数声明中的数组不是完整数组对象。
</details>

<details><summary>讲解与验证</summary>

函数参数被调整为 `int *items`，`sizeof items` 是指针大小；接口也没有合法范围。改为 `void update(int *items, size_t count)`，入口检查 NULL 与空区间契约。用 0、1、容量大小测试，并将循环故意写成 `<=` 用 ASan 验证。游戏映射：敌人批处理和渲染实例列表必须显式传数量。
</details>

### C07-Q2：交换删除的取舍

容器 `[A,B,C,D]` 删除 B 后用 D 覆盖 B。写出结果，并说明何时不能这样做。

<details><summary>最小提示</summary>

交换删除保持紧凑和 O(1)，但不保持原顺序。
</details>

<details><summary>讲解与验证</summary>

结果为 `[A,D,C]`，长度减一。若 UI 列表、回放或设计规则依赖稳定顺序，就必须移动 `[C,D]` 得 `[A,C,D]`，代价 O(n)，或另设稳定 ID/排序层。测试删除头、中、尾和连续删除。游戏映射：死亡敌人通常可无序交换删除，事件日志和展示列表通常不能默认无序。
</details>

下一章把字节数组解释为文本，处理终止符、截断和输入解析。
