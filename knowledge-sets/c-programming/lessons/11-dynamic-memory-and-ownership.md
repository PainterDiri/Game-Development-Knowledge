# 11. 动态内存与所有权：扩容失败后，谁还拥有旧数据

第 7 章的数组必须先有容量，第 9 章的指针只描述地址，不会延长对象寿命。现在编辑器读入多少个房间才知道需要多少存储：怎样增加容量，又保证分配失败时已有数据仍然可用？

## 11.1 先分清字节、元素、容量和长度

`malloc(bytes)` 从 `<stdlib.h>` 获取指定字节数的未初始化存储，失败返回 NULL；成功也没有替你初始化每个 int。`sizeof *items` 表示一个元素的字节数，不会对这个非变长数组表达式执行解引用；items 的声明必须已经可见。

若要容纳 requested 个 int，应先验证 `requested <= SIZE_MAX / sizeof *items`，再做乘法。`SIZE_MAX` 是 size_t 能表示的最大值，来自 `<stdint.h>`。如果先乘，回绕后的较小值可能让分配“成功”，访问时却越界。

容量 capacity 是可存放元素数，长度 count 是已经初始化且属于集合的元素数。核心不变量：

```text
0 <= count <= capacity
capacity == 0 时，items == NULL
capacity > 0 时，items 唯一拥有至少 capacity 个 int 的存储
只有 [0, count) 可作为有效集合读取；[count, capacity) 尚未承诺初始化
```

`calloc` 清零所有分配字节，但全零位模式不是任意类型的通用初始化（尤其不能把它等同于每个平台上的空指针表示）。本章用显式字段初始化建立不变量。

## 11.2 谁拥有，谁借用

| 动作 | 所有者 | 借用者 | 必须保证 |
|---|---|---|---|
| 创建空 Buffer | 调用者拥有容器 | 无 | 字段初始化为 `{0}` |
| reserve 实际重分配成功 | Buffer 拥有新分配块 | 旧借用全部结束 | 调用者重新获取元素地址 |
| reserve 无需增长 | 所有权与存储不变 | 旧借用仍有效 | 不调用 realloc |
| reserve 失败 | 原 Buffer 继续拥有原块 | 旧借用仍有效 | 原指针、长度、容量、已有元素不变 |
| destroy | Buffer 释放自己的块 | 不允许仍有人访问 | 字段恢复为空容器 |

复制 `Buffer copy = original` 只复制地址，不复制分配块。若两份都销毁，就会 double free。这里只允许唯一所有者；以后要深拷贝或转移时必须另外设计 API。`const int *` 可以表达只读访问，但并不能阻止调用者强行释放，也不能让借用在扩容后继续有效。

## 11.3 realloc 的提交点与零大小边界

`realloc(old, bytes)` 在 **bytes > 0** 时有两种结果：

- 失败：返回 NULL，旧分配块没有释放；唯一所有者不能被 NULL 覆盖。
- 成功：旧对象生命周期结束，新指针持有新对象；内容保留到新旧大小的较小者。即使数值地址相同，也不能再使用或比较旧指针/借用来判断是否移动，应只使用返回的新指针。

所以先存 candidate，再提交给所有者。`realloc(p, 0)` 在 C17 有实现定义的零大小行为，不能把 NULL 无条件解释为“旧块还在”。本章不调用任何零大小分配：空容器 reserve(0) 直接成功，释放只走 destroy。

## 11.4 完整程序：失败注入，而不是祈祷内存耗尽

将下面完整 C17 程序保存为临时目录中的 `buffer.c`。它是章节验证，不是第二个主实践。参数 should_fail 是一个明确的教学测试接缝：只模拟本次分配拒绝，不调用系统分配器，也不改变旧块。无需先学函数指针或尝试耗尽机器内存。

<!-- executable: buffer.c -->
```c
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int *items;
    size_t count;
    size_t capacity;
} Buffer;

/* Teaching seam: only this allocation attempt is deliberately failed. */
static void *resize_bytes(void *old, size_t bytes, bool should_fail) {
    if (should_fail) return NULL; /* old is untouched; bytes must be > 0 */
    return realloc(old, bytes);
}

/* Requires a valid, uniquely owned buffer. Does not change count. */
static bool buffer_reserve(Buffer *buffer, size_t requested, bool should_fail) {
    if (requested <= buffer->capacity) return true;
    if (requested > SIZE_MAX / sizeof *buffer->items) return false;
    int *candidate = resize_bytes(buffer->items,
                                  requested * sizeof *buffer->items, should_fail);
    if (candidate == NULL) return false;
    buffer->items = candidate;
    buffer->capacity = requested;
    return true;
}

/* Requires a valid initialized Buffer; no other owner may free its items. */
static void buffer_destroy(Buffer *buffer) {
    free(buffer->items);
    *buffer = (Buffer){0};
}

int main(void) {
    Buffer buffer = {0};
    assert(buffer_reserve(&buffer, 0u, false));
    assert(buffer.items == NULL && buffer.capacity == 0u);
    if (!buffer_reserve(&buffer, 1u, false)) return 1;
    buffer.items[0] = 7;
    buffer.count = 1u;
    int *borrowed = buffer.items;
    assert(buffer_reserve(&buffer, 1u, true)); /* no allocation needed */
    assert(buffer.items == borrowed && buffer.count == 1u);
    assert(!buffer_reserve(&buffer, 4u, true));
    assert(buffer.items == borrowed && buffer.items[0] == 7);
    assert(buffer.count == 1u && buffer.capacity == 1u);
    if (sizeof *buffer.items > 1u) {
        assert(!buffer_reserve(&buffer, SIZE_MAX, false));
        assert(buffer.items == borrowed && buffer.capacity == 1u);
    }
    /* End this borrow BEFORE a possibly successful realloc. */
    borrowed = NULL;
    if (!buffer_reserve(&buffer, 4u, false)) {
        buffer_destroy(&buffer);
        return 1;
    }
    assert(buffer.items[0] == 7 && buffer.count == 1u);
    buffer.items[buffer.count] = 9;
    ++buffer.count; /* publish length only after initialization */
    assert(buffer.items[1] == 9 && buffer.capacity == 4u);
    buffer_destroy(&buffer);
    buffer_destroy(&buffer); /* safe because OUR destroy restored empty state */
    assert(buffer.items == NULL && buffer.count == 0u && buffer.capacity == 0u);
    puts("buffer: all checks passed");
    return 0;
}
```

```bash
cc -std=c17 -Wall -Wextra -Wpedantic -Wconversion -g buffer.c -o buffer && ./buffer
cc -std=c17 -Wall -Wextra -Wpedantic -g -fsanitize=address,undefined buffer.c -o buffer-san && ./buffer-san
```

预期输出 `buffer: all checks passed`，退出 0；本例依赖 assert 执行验证，不要带 `-DNDEBUG`。正常分配本身失败时退出 1，而不是强行继续。测试覆盖空请求、第一次分配、模拟失败、字节溢出拒绝、成功增长、数据保留和二次销毁；动态工具没报告仍不等于全部内存错误已排除。

逐步跟踪一次增长：初始 `{NULL,0,0}` → reserve(1) 后 `{地址,0,1}` → 写入 7 后 count=1 → 模拟 reserve(4) 失败，四项旧状态不变 → 成功 reserve(4)，count 仍为 1 → 写第二个元素后 count=2。reserve 不等于 resize：它只获取空间，不承诺新元素存在。

## 11.5 销毁、部分构造与增长取舍

`free(NULL)` 无操作。`free(p); p=NULL` 只清除这一份指针，其他别名不会跟着清空。本例 destroy 第二次安全，是因为第一次把整个有效容器恢复为空；**不能因此直接 free 同一个悬空指针两次**。容器对象本身若已结束生命周期，再调用 destroy 同样非法。

若要同时创建敌人数组和掉落表，第二个分配失败时必须释放第一个成功资源；清理顺序通常与获取顺序相反。可以提前把资源指针设 NULL，通过一个 cleanup 路径统一释放，但不能把尚未初始化的垃圾指针传给 free。

本例按请求容量扩容，可能反复重新分配；倍增可减少增长次数，但倍增本身仍要检查溢出和预算。固定数组/对象池上限清晰、不触发运行中扩容；动态数组更灵活，却引入拒绝、搬移和借用失效。游戏实时战斗不一定适合随时增长，离线关卡工具更容易容忍这些成本。

## 本章练习

### C11-Q1：`realloc` 失败后的四项状态

**题型**：动态内存状态表与失败原子性
**作答产物**：两种写法的逐步状态表；安全实现；失败注入断言。

初始：`data` 指向含 `{10,20}` 的 2 个 `int`，`length=2`、`capacity=2`。需要扩到 4。比较：

```c
/* A */ data = realloc(data, 4 * sizeof *data);
/* B */ int *candidate = realloc(data, 4 * sizeof *data);
```

假设分配失败并返回 `NULL`。分别填写 `data`、旧分配是否仍拥有、`length`、`capacity`、元素值还能否访问。然后写出只有成功时才提交指针和 capacity 的 `grow_to_four` 核心代码，并定义 `realloc(ptr, 0)` 不进入本函数的原因。

<details><summary>讲解、判定与验证</summary>

A 直接覆盖唯一指针：`data` 变为 NULL，旧分配按照 `realloc` 失败契约仍存在，但程序已丢失其地址，形成泄漏；若代码提前把 capacity 改为 4，还会产生元数据谎言。length/capacity 若尚未修改仍是 2/2，但元素因指针丢失而无法再合法访问。

B 中 `candidate=NULL`，原 `data` 仍指向旧分配，length=2、capacity=2、值 `{10,20}` 都保持有效。安全核心：

```c
bool grow_to_four(int **data, size_t length, size_t *capacity) {
    if (data == NULL || capacity == NULL || length > *capacity) return false;
    if (*capacity >= 4) return true;
    int *candidate = realloc(*data, 4 * sizeof **data);
    if (candidate == NULL) return false;
    *data = candidate;
    *capacity = 4;
    return true;
}
```

真实通用实现还必须在乘法前检查 `new_capacity > SIZE_MAX / sizeof **data`，并说明 `*data==NULL` 是否允许。这里目标容量固定为 4 且非零，故不触发 `realloc(ptr,0)` 的实现差异/释放语义；通用函数应把请求 0 独立定义为 no-op 或显式 free，而不是交给 realloc 模糊处理。

失败注入断言：返回 false；data 地址与旧地址相同；length/capacity 不变；两个元素逐值不变；旧块最终仍由调用者 free。评分点：区分指针变量、分配对象和元数据；失败不覆盖原指针；成功后才提交 capacity。常见错误是只断言“返回失败”却不检查旧值，或在 realloc 前发布新容量。游戏映射：动态实体数组、网络缓冲和存档缓冲扩容失败时，旧运行时必须继续可用，不能半更新所有权状态。
</details>

### C11-Q2：地址没变，借用就还有效吗

**题型**：生命周期推演与反例
**作答产物**：分配代次时间线、借用失效点和修复后的契约。

保存 `int *view = buffer.items` 后成功扩容。学习者想写 `if (view == buffer.items) puts(*view)` 来证明无需更新借用。这个方案哪里错误？若只是 reserve(0) 的无操作路径又怎样？

<details><summary>讲解、判定与验证</summary>

成功 realloc 已结束旧对象生命周期，不能读取旧指针值来比较，更不能解引用；数值地址偶然复用不是旧借用存活的证据。结束旧借用，使用 buffer.items 重新取得 view。reserve(0) 在本实现不调用 realloc，原对象没有结束，借用可继续使用。应通过控制流和 API 契约判断，而不是通过 UB 实验推断。游戏资源容器扩容后缓存元素地址的组件，必须重新查找或使用不暴露地址的句柄。
</details>

### C11-Q3：第二次分配失败怎样清理

**题型**：所有权图与清理实现
**作答产物**：所有权图、每条失败路径的释放顺序和可运行清理代码。

需要两块互不共享的数组 A、B；A 成功、B 失败。要求失败时没有泄漏，也不能把半成品发布给调用者。给出获取、提交、清理顺序，并区分“内部资源已释放”与“调用者输出被改坏”。

<details><summary>讲解、判定与验证</summary>

先建立局部空 candidate，申请 A；失败立即返回。再申请 B；失败释放 A 并返回，不写调用者输出。都成功且初始化完成后才转移所有权到输出，局部不再释放已转移块。用确定的第二次失败开关覆盖路径，分别检查输出旧状态和释放次数；仅靠极大 malloc 请求不稳定。关卡资源批量加载同样应避免只发布半张关卡。
</details>

## 来源与适用范围

零大小 realloc 的 C17 差异另依据 [WG14 DR 400 及 C17 修正说明](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n2243.htm#dr_400)（2026-09-07 核对）：零大小未分配新对象时，旧对象是否被释放为实现定义；零大小调用列为过时特性。本课始终在调用前排除此路径。

核对日期：2026-09-07。课程仍按 C17 编译；以下 N1570 是 C11 草案，仅用于核对共通条款，不冒称已读取本轮未能解密的 N2176 PDF。依据 [WG14 C11 草案 N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf) 的 6.2.4（生命周期）、7.22.3 与 7.22.3.5（分配及 realloc）。不套用 C23 的零大小规则。示例仅验证本地单线程容器，不是通用分配器或完整内存管理课程。

下一章把“先构造 candidate，再一次提交”的思想用于外部文件，区分内存状态原子性与磁盘持久性。
