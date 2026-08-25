# 2. 对象、类型与状态：一个变量不是“带名字的数字”

上一章留下的问题是“程序保存的值到底是什么”。在游戏里，`health`、`position.x`、`enemyCount` 看起来都只是字段，但它们的**表示范围、大小、可写性和生命周期**不同。C 用对象和类型把这些差异写出来。

## 从观察到定义

```c
#include <stdbool.h>
#include <stdio.h>

int main(void) {
    int health = 100;
    const int max_health = 100;
    double speed = 3.5;
    bool is_alive = true;

    printf("health=%d max=%d speed=%.1f alive=%d\n",
           health, max_health, speed, is_alive);
    printf("sizeof(int)=%zu sizeof(double)=%zu\n",
           sizeof health, sizeof speed);
    return 0;
}
```

**对象**是程序执行期间存放值的区域；**类型**规定这块区域如何解释、可以做哪些运算以及通常需要多少存储。变量是有名字的对象；`const` 变量仍然是对象，但不能通过这个名字修改。

`sizeof` 返回 `size_t`，所以用 `%zu`；不要把“在我的 Mac 上 `int` 是 4 字节”误写成 C 语言保证。标准规定最小范围和关系，具体大小可能随实现变化。

## 状态模型

把一次房间运行写成状态：

```text
RoomState = { health: int, speed: double, is_alive: bool }
```

一条语句是状态转换：`health -= damage`。正确性至少要保持：`0 <= health <= max_health`。类型只能帮你表达“这是整数/浮点/布尔”，不能自动保证这个业务不变量；不变量需要代码和测试共同维护。

## 失败：把表示和意义混在一起

```c
unsigned int damage = 20;
int health = 10;
health -= damage; // 结果可能不是 -10，而是转换后的大数
```

混合有符号与无符号类型时，整数转换规则可能让负数变成很大的无符号值。游戏里的实体计数、数组索引通常适合无符号或 `size_t`，但伤害、差值、速度方向常需要表达负数。不要只看字段名；先写出允许范围，再选类型。

## 验证与取舍

运行 `printf("%zu\n", sizeof(bool));`，再在另一种编译器上运行，记录差异；用 `-Wconversion` 捕捉隐式窄化。`float` 更省带宽，`double` 精度更高，但游戏帧逻辑应优先明确误差预算和跨平台复现要求，而不是全局替换类型。

Unity C# 的 `int/float/bool` 与 C 有相似表面，但不能假设内存布局、序列化和调用约定完全相同；UE C++ 也会额外引入反射类型。C 课程先掌握“值 + 表示 + 生命周期”的底层模型。下一章将研究多个值组合时，类型转换和溢出如何改变结果。

> 参考：[N1570 §6.2.5 类型](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)、[N1570 §6.5.3.4 sizeof](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)。
