# 11. 动态内存与所有权：`malloc` 不是生命周期设计

固定容量数组适合教学和对象池，但有些工具需要运行时数量。动态内存给出灵活性，也带来失败、泄漏、重复释放和释放后使用。关键不在记住函数名，而在每个分配块都有唯一的所有者和可追踪的销毁路径。

## 机制

本章把可观察现象还原为语言机制和不变量，而不是只记 API 名称。

## 11.1 分配、初始化与释放

```c
int *values = malloc(count * sizeof *values);
if (values == NULL) return RG_ERR_ALLOC;
for (size_t i = 0; i < count; ++i) values[i] = 0;
/* 使用 values */
free(values);
values = NULL;
```

`malloc` 返回未初始化字节，不能直接读取；乘法计算大小前要检查溢出。`sizeof *values` 比写 `sizeof(int)` 更不易在改类型时出错。`free(NULL)` 安全，但不应靠它掩盖所有权混乱。

## 11.2 所有权表

为容器写一张表：

| 资源 | 创建者 | 当前所有者 | 释放者 | 借用者 | 失效时机 |
|---|---|---|---|---|---|
| 敌人数组 | `buffer_create` | `EnemyBuffer` | `buffer_destroy` | 查询函数 | destroy 后 |

转移所有权要在 API 名称/文档中明确。借用者不能 `free`；所有者销毁后借用指针全部失效。不要返回内部缓冲区裸指针而不说明下一次扩容会使它失效。

## 11.3 `realloc` 的失败安全

```c
int *grown = realloc(values, new_count * sizeof *values);
if (grown == NULL) {
    /* values 仍然有效，不能覆盖它 */
    return RG_ERR_ALLOC;
}
values = grown;
```

直接写 `values = realloc(values, ...)` 会在失败时丢失旧指针，造成泄漏。成功后旧地址可能改变，所有指向旧元素的借用指针都可能失效。扩容 API 应在文档中写“可能使迭代器/指针失效”。

## 11.4 常见生命周期错误

- leak：分配后没有任何释放路径；
- double free：同一块被两个所有者释放；
- use-after-free：释放后继续访问；
- buffer overflow：分配字节数和元素数计算错误；
- partial construction：中途失败却忘记清理已成功资源。

清理代码可按已创建资源的逆序释放；或者用单一 `cleanup:` 路径，但必须避免重复释放。固定容量方案牺牲最大规模换取简单生命周期，动态方案牺牲复杂度换取灵活容量，不能只比较速度。

## 验证与游戏映射

使用 `-fsanitize=address,undefined` 和 LeakSanitizer（工具链支持时）；测试 0、1、扩容失败模拟、销毁两次、保存旧指针后扩容。游戏映射：资源加载、临时顶点、对象池和编辑器工具都要定义所有权；Unity/UE 的托管对象或容器并没有消除跨原生边界的所有权问题。

## 进一步拆解与实验

## 11.5 分配大小、元素数量与溢出

动态数组的安全性先从字节数开始：

```c
if (count > SIZE_MAX / sizeof *items) {
    return false; /* count * sizeof *items 会溢出 */
}
Enemy *items = malloc(count * sizeof *items);
```

使用 `sizeof *items` 比重复写类型名更不容易在类型改变后漏改。`malloc` 返回未初始化存储；需要零初始化可以使用 `calloc`，但“全零位模式”不应被误当成所有类型的通用有效值。分配成功还要初始化对象并建立 `count <= capacity` 等不变量。

## 11.6 所有权转移的文字契约

下面三种接口语义不同：

```c
Enemy *enemy_create(void);                 /* 返回：调用者拥有，必须 destroy */
void enemy_print(const Enemy *enemy);      /* 借用：调用期间不释放 */
void inventory_add(Inventory *inv, Enemy *enemy); /* 是否接管？必须写明 */
```

“传入一个指针”不能自动说明所有权。实践中在函数注释或文档中写：调用者拥有/被调用者借用/成功后转移/失败后仍由调用者拥有。失败路径尤其要明确，否则会出现双重释放或泄漏。

## 11.7 `realloc` 的两阶段模式

不要直接覆盖唯一指针：

```c
Enemy *grown = realloc(items, new_count * sizeof *items);
if (grown == NULL) {
    /* items 仍然有效，原状态保持 */
    return false;
}
items = grown;
```

如果 `realloc` 成功，它可能移动对象，旧指针不能再使用；所有借用旧地址的指针都可能失效。扩容后要重新建立初始化和长度不变量。若增长策略使用 `capacity *= 2`，也要检查乘法溢出和上限。

## 11.8 释放不等于擦除所有别名

`free(p)` 结束被分配对象的生命周期，但其他保存该地址的指针不会自动变成 NULL：

```c
free(p);
p = NULL; /* 只清除了这一份拥有者变量 */
```

如果存在借用者，拥有者必须保证释放发生在所有借用结束之后；复杂系统可以用句柄、引用计数或集中式生命周期管理，但每种机制都有成本。Sanitizer 能帮助发现一部分 use-after-free，不能替你设计所有权。

## 本章练习

### C11-Q1：修复不安全的 realloc

指出 `values = realloc(values, bigger);` 的失败问题，并给出安全写法。

<details><summary>最小提示</summary>

在覆盖所有者指针前保留临时指针。
</details>

<details><summary>讲解与验证</summary>

失败返回 NULL，直接覆盖会丢失原块地址；用 `void *candidate = realloc(values, bigger); if (!candidate) return error; values=candidate;`。还要检查 `bigger` 的乘法溢出，成功扩容后旧借用指针可能失效。通过注入分配失败或极大请求测试。游戏映射：运行时扩容失败必须保持旧状态可用，而不是半更新。
</details>

### C11-Q2：找出所有权冲突

函数 `get_items()` 返回内部数组指针，调用者 `free` 它，随后容器析构又 `free` 一次。如何改 API？

<details><summary>最小提示</summary>

返回借用视图，或者转移所有权；两者不能含糊。
</details>

<details><summary>讲解与验证</summary>

若容器继续拥有内存，返回 `const Item *` 加长度并明确“不得释放，直到下一次修改/销毁”；若调用者应接管，则用 `take_items` 命名并把容器指针清空。测试调用者不释放的借用路径和转移后的单次释放路径，用 ASan 检查 double-free。游戏映射：资源缓存和渲染批次常暴露临时借用视图，生命周期要短而明确。
</details>

下一章把结构化状态写入文件，并处理版本、截断、错误和失败原子性。
