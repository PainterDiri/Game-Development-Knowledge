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
    for (size_t i = 0; i < count; ++i) {
        if (health[i] > 0) --health[i];
    }
}
```

上述都是说明数组参数的片段，不是各自独立的程序；需 `<stddef.h>` 提供 size_t，输出还需 `<stdio.h>`。tick 要求非空区间指向至少 count 个有效 int，且初始生命非负；只有正生命递减，避免把 0 变负或在 INT_MIN 上继续递减。完整运行入口见 7.8。

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
cc -std=c17 -Wall -Wextra -O0 -g -fsanitize=address search.c -o search-san
./search-san
```

使用第 4 章 search.c 的副本，把 find_enemy 的循环条件改为 <=，并在这份故意错误副本中暂时注释 NULL/0 断言，让缺失目标用例走到数组末尾之外，应出现 stack-buffer-overflow；若不注释，首个 NULL/0 用例会先触发空指针访问。修复 < 后恢复所有断言，确认原边界仍在测试中。不要改动公共教材源码或在无工具运行后猜越界结果。验证还要覆盖 0、1、恰好容量、超过容量和删除最后一个元素。

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

下面两个删除片段的共同前提是 `index < count <= capacity`、values 指向真实容量、元素可按值复制；空数组应先拒绝删除，不能先计算 `count - 1`。稳定删除通常需要把后续元素左移，成本 O(n)：

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

## 7.8 求和与交换删除的完整验证入口

下面将 7.5 的函数与调用者组合成 `sum.c`；以 C17 编译运行，不带 `-DNDEBUG`，预期 `sum: passed`。输出只在循环结束后写入，因此中途正溢出或负溢出拒绝时仍保持旧结果 9。它不能检测虚报 count，调用者仍须保证真实内存范围。

还在同一数组程序中验证连续删除、末元素删除和空集合拒绝：每轮若删除则 count 减一，否则 i 加一，因此剩余待检查数量 count-i 严格下降。把删除后也 ++i 改进去，会跳过换入的零并触发断言，而不是只能靠肉眼看输出。

<!-- executable: sum.c -->
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
#include <assert.h>
#include <stdio.h>
/* No order guarantee; invalid index leaves both count and elements untouched.
   items owns at least *count live ints, count points to an independent object. */
static bool remove_swap(int *items, size_t *count, size_t index) {
    if (count == NULL || index >= *count || items == NULL) return false;
    items[index] = items[*count - 1u];
    --*count;
    return true;
}
int main(void) {
    int items[] = {0, 1, 0, 0};
    size_t count = 4u;
    size_t i = 0u;
    while (i < count) {
        if (items[i] == 0) assert(remove_swap(items, &count, i));
        else ++i; /* a moved-in element must be inspected before advancing */
    }
    assert(count == 1u && items[0] == 1);
    assert(!remove_swap(items, &count, count) && count == 1u && items[0] == 1);
    assert(remove_swap(items, &count, 0u) && count == 0u);
    assert(!remove_swap(NULL, &count, 0u) && count == 0u);
    int sum = 99;
    const int normal[] = {4, -2, 7};
    const int positive[] = {INT_MAX, 1};
    const int negative[] = {INT_MIN, -1};
    assert(sum_checked(NULL, 0u, &sum) && sum == 0);
    assert(sum_checked(normal, 3u, &sum) && sum == 9);
    assert(!sum_checked(positive, 2u, &sum) && sum == 9);
    assert(!sum_checked(negative, 2u, &sum) && sum == 9);
    assert(!sum_checked(NULL, 1u, &sum) && sum == 9);
    puts("sum: passed");
    return 0;
}
```

## 本章练习

### C07-Q1：改写错误的数组 API

**题型**：API 改写与边界测试
**作答产物**：带长度/容量的函数签名、实现要点和空/满/越界测试。

`void update(int items[])` 内用 `sizeof` 计算数量。指出问题并给出安全签名。


<details><summary>讲解、判定与验证</summary>

函数参数被调整为 `int *items`，`sizeof items` 是指针大小；接口也没有合法范围。改为 `void update(int *items, size_t count)`，入口检查 NULL 与空区间契约。用 0、1、容量大小测试，并将循环故意写成 `<=` 用 ASan 验证。游戏映射：敌人批处理和渲染实例列表必须显式传数量。
</details>

### C07-Q2：稳定删除与交换删除的结果和成本

**题型**：数组状态推演与算法取舍
**作答产物**：两种删除后的数组、元素移动次数、复杂度和适用约束。

固定容量数组有效区间为：

```text
index: 0   1   2   3   4
id:    10  20  30  40  50
count = 5
```

删除索引 1（id=20）：

1. 用稳定删除逐步写出每次赋值、最终数组前 `count` 项和移动次数；
2. 用交换删除写出赋值、最终数组和移动次数；
3. 如果其他系统持有“索引 3 指向 id=40”的句柄，两种方案分别怎样破坏该假设；
4. 为肉鸽弹幕列表与回放事件列表分别选择方案并说明证据。

<details><summary>讲解、判定与验证</summary>

稳定删除把后续元素左移：`a[1]=30`、`a[2]=40`、`a[3]=50`，再把 `count` 改为 4；有效区间为 `10,30,40,50`，发生 `count-index-1 = 3` 次元素移动，时间 O(n)。交换删除执行 `a[1]=a[4]` 后把 count 改为 4；有效区间为 `10,50,30,40`，一次元素赋值，时间 O(1)，但顺序变化。

原“索引 3→id40”在稳定删除后变成索引 2，所以裸索引句柄失效；交换删除后本例 id40 仍恰好在索引 3，但这不是可依赖保证，删除其他索引或后续操作会改变映射，且 id50 已从 4 跳到 1。若外部长期引用元素，应使用稳定 ID+查找、代际句柄或由容器发布重定位，而不是承诺裸索引永远稳定。

高频、顺序无语义且每帧遍历的弹幕列表通常偏向交换删除；仍需证明渲染/碰撞结果不依赖迭代顺序，确定性回放还要定义排序或稳定 ID。回放事件列表顺序通常就是语义，应稳定删除或更常见地追加并用游标/墓碑，不可交换。

评分点：数组结果和移动次数正确；明确两种方案都可能使索引句柄失效；取舍同时考虑顺序语义、成本与确定性。边界：删除最后元素时两者都可零移动；结构体赋值成本可能不小，不能只数语句。验证应测试首、中、尾删除和 count=1。游戏映射：对象池优化若悄悄改变迭代顺序，可能改变 RNG 消耗、伤害结算和网络回放结果。
</details>
