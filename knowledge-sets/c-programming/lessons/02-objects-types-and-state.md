# 2. 对象、类型与状态：变量不是没有边界的盒子

上一章的进程开始运行后，必须把生命值、波次和 seed 放进内存。若只把变量理解成“一个名字”，就无法解释溢出、地址、生命周期和指针。本章建立 C 的核心模型：**对象占据存储，类型规定值的表示与可做的操作，表达式读取或改变对象状态。**

## 2.1 声明、定义、对象和值

```c
#include <stdio.h>

int main(void) {
    int player_health = 20;
    const int max_health = 20;
    printf("health=%d max=%d\n", player_health, max_health);
    return 0;
}
```

`int player_health = 20;` 定义一个 `int` 对象并初始化为 20。对象有存储期和值，`player_health` 是访问它的标识符。`const` 表示不能通过该名字修改对象，不表示它一定在只读硬件内存，也不自动让整个程序线程安全。

“未初始化”和“初始化为 0”不是一回事。块内自动对象若未初始化，读取其不确定值会产生未定义行为：

```c
int damage;
printf("%d\n", damage); /* 错误：先读后写 */
```

编译器警告可能捕获它，但程序正确性不能依赖警告恰好出现。最稳妥的不变量是：对象第一次被读取前必须沿所有控制路径完成初始化。

## 2.2 基本类型与单位

C 提供整数、浮点、字符和布尔等类型，但类型名没有携带“点数”“秒”“像素”单位。下面两者都为 `int`，编译器无法阻止相加：

```c
int health_points = 20;
int elapsed_frames = 3;
int nonsense = health_points + elapsed_frames;
```

工程上用明确命名、结构体包装和 API 边界表达单位。`sizeof(type)` 返回以字节为单位的大小，结果类型是 `size_t`：

```c
printf("int bytes=%zu\n", sizeof(int));
```

不要硬编码 `int` 一定是 4 字节；需要固定宽度存档字段时使用 `<stdint.h>` 的 `uint32_t` 等类型，并另外定义字节序与序列化规则。

## 2.3 赋值是状态变化，不是数学等式

```c
int health = 20;
health = health - 3;
```

右侧先读取旧值并计算 17，左侧再把对象更新为 17。因此 `=` 是赋值运算，不表示数学恒等。设计状态更新时写出前置条件和后置条件：

```text
前置：0 <= damage，0 <= health <= max_health
更新：health = max(0, health - damage)
后置：0 <= health <= max_health
```

这些条件是后续测试和循环不变量的来源。

## 2.4 作用域与存储期先分开

**作用域**回答名字在源码哪里可见；**存储期**回答对象何时存在。块内变量通常具有自动存储期，离开块后生命周期结束：

```c
if (player_health > 0) {
    int bonus = 2;
    player_health += bonus;
}
/* bonus 在这里不可见，其对象也已结束生命周期 */
```

`static` 块变量的名字仍受块作用域限制，但对象贯穿程序执行；它会引入跨调用共享状态，可能破坏测试隔离与可重入性，不应当作“让指针永远有效”的通用补丁。

## 2.5 格式化输出就是类型契约

`printf` 的格式串决定它怎样解释后续参数。`%d` 对应提升后的 `int`，`%zu` 对应 `size_t`，`%u` 对应 `unsigned int`。格式错配不是简单显示难看，而可能让函数按错误表示读取参数。启用警告并优先让编译器检查字面量格式串。

## 验证、失败与游戏映射

建立 `types.c`，打印 `sizeof`、初始值和每次状态更新；再故意删除初始化，用 `cc -std=c17 -Wall -Wextra -Wpedantic` 观察警告。预期正常版本没有警告且生命值不低于 0。游戏映射：玩家状态、资源句柄、帧计数和网络字段都需要明确类型、单位、所有者与生命周期；“都是 int”会把错误拖到运行时。

## 进一步拆解与实验

## 2.6 用状态表追踪一次更新

面对 `health -= damage`，先不要凭感觉说“生命值减少了”。把它写成状态转移：

| 时刻 | `health` | `damage` | 发生的动作 |
|---|---:|---:|---|
| 进入函数前 | 20 | 3 | 前置条件：`0 <= health <= max_health` |
| 读取右侧 | 20 | 3 | 计算 `20 - 3` |
| 写回后 | 17 | 3 | 后置条件仍成立 |

如果 `damage` 为负数，后置条件可能失效；因此“赋值语句看起来正确”不等于状态更新正确。把输入检查放在修改状态之前：

```c
/* 片段：可放进已有 C17 源文件；此处省略 main。 */
#include <stddef.h>
#include <stdbool.h>

bool apply_damage(int *health, int max_health, int damage) {
    if (health == NULL || max_health < 0 || damage < 0) {
        return false;
    }
    if (*health < 0 || *health > max_health) {
        return false;
    }
    *health = damage >= *health ? 0 : *health - damage;
    return true;
}
```

这里 `health` 是将被修改的对象，`max_health` 和 `damage` 是输入。成功时函数改变 `*health`，失败时返回 `false` 且不应改变它。第 9 章会正式解释 `int *`；现在先把它当作“允许函数定位并修改调用者对象”的参数。

## 2.7 初始化、赋值和常量的区别

```c
int wave = 1;       /* 定义时初始化一次 */
wave = 2;           /* 之后的状态变化 */
const int cap = 32; /* 绑定后不能通过 cap 赋值 */
```

初始化发生在对象建立时，赋值发生在对象已经存在之后；`const` 约束的是通过该表达式进行修改。`const int *`、`int *const` 和 `const int *const` 的限制对象不同，先不要把它们统称为“常量指针”。判断方法是从标识符向外读：`const int *p` 表示“通过 p 不能改 int”，`int *const p` 表示“p 本身不能改指向”。

用编译器而不是记忆验证格式和警告：

```bash
cc -std=c17 -Wall -Wextra -Wpedantic -Wconversion types.c -o types
```

如果把 `size_t` 直接用 `%d` 打印，警告就是类型契约被破坏的证据；应改用 `%zu`。若不同平台的 `sizeof(int)` 不同，固定格式不要把它直接写入存档，而要在序列化层明确宽度。

## 2.8 对象、标识符和地址不是同一个概念

`player_health` 是名字，名字在源码作用域中可见；对象是运行时占据存储的实体；值是对象当前保存的内容；地址是定位对象的方式。多个表达式可以访问同一个对象（第 9 章的别名），一个地址也可能在对象生命周期结束后失效。

这个区分能解释一个常见误解：`int *p = &health;` 并没有复制一份生命值，它只创建了一个指向 `health` 的指针。执行 `*p = 0` 改的是原来的 `health`。调试时要分别问“哪个对象变了”“哪个名字可见”“哪个指针仍然有效”。

## 本章练习

### C02-Q1：初始化不变量

函数里声明 `int total_damage;`，随后在循环中执行 `total_damage += hit;`。为什么即使偶尔得到正确结果也不合法？

<details><summary>最小提示</summary>

第一次 `+=` 同时包含一次读取和一次写入。
</details>

<details><summary>讲解与验证</summary>

`+=` 需要读取旧值，而自动对象 `total_damage` 尚未初始化，读取不确定值会导致未定义行为。修复为 `int total_damage = 0;`，并测试空命中列表时结果仍为 0。常见错误是依赖 debug 构建恰好把栈填零。游戏映射：帧统计、累计伤害和资源计数器若无明确初值，会产生难复现的幽灵状态。
</details>

### C02-Q2：类型与单位边界

`float cooldown = 120;` 无法判断 120 是秒、毫秒还是帧。给出两种改善接口的方法及其取舍。

<details><summary>最小提示</summary>

先改善命名，再考虑用结构体或只允许构造函数创建值。
</details>

<details><summary>讲解与验证</summary>

最低成本是命名 `cooldown_frames` 或 `cooldown_seconds`；更强的做法是定义 `typedef struct { float seconds; } Duration;` 并通过 `duration_from_seconds` 创建。前者简单但仍可能误传，后者增加样板却能在 API 评审中暴露单位。用编译期类型错误或边界测试验证。游戏映射：移动速度、动画时间、网络 tick 与物理步长常因单位混淆出现数量级错误。
</details>

下一章研究表达式如何组合这些值，以及整数转换、溢出和浮点误差怎样改变结果。
