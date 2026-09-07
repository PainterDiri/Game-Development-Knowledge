# 13. 预处理、未定义行为与调试：不崩不等于正确

C 给了你接近机器的控制，也允许程序进入标准没有规定结果的状态。此时“在我电脑上没崩”不是证据。本章建立缺陷诊断顺序：先减少输入，再阅读编译器诊断，再用动态工具和调试器确认生命周期/边界，最后补回归测试。

## 机制

本章把可观察现象还原为语言机制和不变量，而不是只记 API 名称。

## 13.1 宏先展开再编译

```c
#define SQUARE(x) ((x) * (x))
```

括号能减少优先级陷阱，但宏仍会重复求值：`SQUARE(i++)` 展开为两个没有规定先后关系的 i++，触发未定义行为，不能把结果描述成可靠的“两次递增”。宏没有类型检查，名称也可能污染全局。对常量优先使用 `enum`/`static const`，对行为优先使用函数；只有需要条件编译、字符串化或平台开关时才引入宏，并给出副作用规则。

```c
#ifdef _WIN32
/* 平台分支 */
#else
/* 其他平台 */
#endif
```

预处理器不会理解 C 的作用域和类型，它只是记号变换器。用 `cc -E` 查看实际输入，能解释“明明写了 A，编译器却看到 B”。

## 13.2 未定义行为的含义

未定义行为不是“随机返回一个值”，而是标准不再对程序结果提供要求，编译器可以基于“这种情况不会发生”的假设优化。典型来源：越界、释放后使用、返回局部地址、空指针解引用、有符号溢出、错误格式串和不兼容类型别名。

```c
int values[2] = {1, 2};
int x = values[2]; /* 越界：不要靠邻接内存解释 */
```

修复不是加 `printf`、加 `volatile` 或改优化级别；应恢复前置条件并测试边界。

## 13.3 警告与 Sanitizer 的角色

先启用（用 13.10 的完整 debug_damage.c 作为输入；在该节保存文件后再执行）：

```bash
cc -std=c17 -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -g debug_damage.c -o debug_damage
cc -std=c17 -Wall -Wextra -fsanitize=address,undefined -g debug_damage.c -o debug_damage-san
./debug_damage-san
```

警告是静态推断，覆盖不到所有运行路径；ASan 擅长越界、use-after-free 等地址错误，UBSan 覆盖多类运行时未定义行为，仍不是形式化证明，也不一定覆盖线程竞态或所有跨模块问题。不要在生产构建默认开启 Sanitizer 而不评估性能、依赖和平台支持。

## 13.4 调试器是观察工具

用 `gdb ./debug_damage` 或平台等价调试器，在断点处观察参数、局部对象、调用栈和内存。最小诊断问题不是“哪一行红了”，而是：哪个前置条件第一次被破坏？谁最后修改了对象？对象当时还活着吗？对并发或时间问题，应先记录可复现输入和事件序列。

## 13.5 故意失败到修复闭环

把循环改成 `<=`，用最小 count=0/1 复现 ASan；把 `free` 后读取，观察 use-after-free；把有符号值转换为 `size_t`，测试负输入。修复后必须保留能命中原边界的回归测试，并确认报告消失不是因为测试绕开了错误。

游戏映射：帧更新中的偶现崩溃、资源热加载后悬空句柄、敌人池越界和发布构建优化差异，都要用“最小复现—工具证据—修复—回归”处理。

## 进一步拆解与实验

## 13.6 诊断顺序：从最便宜的证据开始

一个实际缺陷可以按下列顺序缩小：

1. 固定输入、seed、平台和命令，先确认能重复；
2. 读取编译器首条相关警告，不要被后续连锁错误淹没；
3. 用最小数据量重现，缩短日志和调用链；
4. 运行 AddressSanitizer/UBSan 或静态分析，记录完整堆栈；
5. 在调试器中观察第一次破坏不变量的位置；
6. 修复根因，添加能命中原缺陷的回归测试；
7. 运行全套测试，确认没有“为了绕过报告而删除输入”。

“第一次破坏”比“最后崩溃”更有价值。例如一个越界写可能在几十行后才让 `enemy_count` 变成巨大数；只修崩溃行会保留真正的边界错误。

## 13.7 预处理输出和宏副作用实验

```bash
printf '#define SQUARE(x) ((x) * (x))\nint result = SQUARE(3);\n' > macro.c
cc -std=c17 -E macro.c > macro.i
grep 'int result' macro.i
```

上述预处理验证不链接，因此不需要 main；应看到 result 变为显式乘法。完整程序中 `#include` 展开后的内容会很长，不要试图把它全部读完；只搜索你关心的宏或声明。用以下测试说明括号并不能解决重复求值：

```c
#define SAFEISH_SQUARE(x) ((x) * (x))
int i = 2;
int result = SAFEISH_SQUARE(i++); /* result 不应被当作合法设计 */
```

更稳妥的是类型明确的函数，或在接口中要求参数无副作用。宏适合编译期分支、字符串化和少数泛型技巧，但每个宏都应写出展开形式和求值次数。

## 13.8 调试器中的三个观察点

- **断点**：程序在某行停下，查看当前参数和局部对象；
- **监视点**：某对象被写入时暂停，适合追踪“谁改坏了 health”；
- **调用栈**：显示当前函数由谁调用，帮助判断哪个契约被违反。

调试命令因 GDB、LLDB 和 IDE 而异，概念不变。编译时加入 `-g` 保留调试信息，通常同时降低“优化导致变量消失”的困惑；但不要把只在 `-O0` 出现的行为当作最终证明。修复后要在接近发布的优化选项下再跑功能和 Sanitizer（在工具支持的范围内）。

## 13.9 未定义、实现定义和未指定

这三个词不能混为“编译器随便”：

- **未定义行为**：标准不再给出要求，编译器可据此优化；
- **实现定义行为**：实现必须选择并记录一种行为；
- **未指定行为**：实现可从允许集合中选择，不必每次相同。

课程中遇到位宽、`char` 符号性、整数表示、结构体填充等问题，先查适用标准和编译器文档，再把需要稳定的部分转换成显式协议。游戏跨平台存档和回放尤其不能把实现偶然性当成格式规则。

## 13.10 一次可跟随的断点、调用栈和监视点

保存下面完整程序为 `debug_damage.c`，限定 attack/armor 在 0–100，避免把业务错误与算术溢出混在一起。当前缺陷是护甲高于攻击时得到负伤害，从而回血，所有执行仍在 C 定义内，**ASan 不应该被期待发现错误的游戏规则**。

<!-- executable: debug_damage.c -->
```c
#include <stdio.h>
/* Logical defect, NOT undefined behavior: valid arithmetic, wrong game rule. */
static int damage_after_armor(int attack, int armor) {
    int damage = attack - armor;
    return damage;
}
int main(void) {
    int health = 10;
    int damage = damage_after_armor(3, 5);
    health -= damage;
    printf("damage=%d health=%d\n", damage, health);
    return health == 10 ? 0 : 1;
}
```

```bash
cc -std=c17 -Wall -Wextra -Wpedantic -O0 -g debug_damage.c -o debug_damage
./debug_damage
# 预期 damage=-2 health=12，退出 1；这是故意失败，不是实验通过
lldb ./debug_damage
```

在 LLDB 提示符逐条执行（不是 shell 命令）：

```text
breakpoint set --name damage_after_armor
run
frame variable attack armor
bt
thread step-out
frame variable health
watchpoint set variable health
continue
frame variable health
bt
continue
quit
```

断点让程序在函数入口暂停；先看到 attack=3/armor=5，调用栈中本函数由 main 调用。step-out 执行到返回调用者，然后 health 仍为 10，此时设监视点；continue 后 health 写入 12 应触发暂停，写入指令可能已经完成，所以停行不必正好是赋值源码行。最后 continue 到退出。断点编号、地址、行号和栈格式随编译器变化，不以逐字日志相同验收。

GDB 等价顺序是 `break damage_after_armor`、`run`、`info args`、`bt`、`finish`、`print health`、`watch health`、`continue`、`print health`、`continue`。调试器需要宿主允许跟踪进程；被系统权限阻止时先解决授权，不把无法启动说成代码通过。硬件监视点数量与目标支持有限。

修复函数返回语句为 `return damage > 0 ? damage : 0;`，重新编译，输出变为 `damage=0 health=10`、退出 0；再测 attack=8/armor=5 得到 3，边界 0/0 得到 0。修复前后的差异必须由同一个输入判定，而不是改测试使错误“合法”。只要超出本节限定范围，attack-armor 的溢出又需要独立检查。

## 13.11 单独验证真正的地址错误

以下是**故意错误的完整程序**，只在临时目录编译并带 ASan 运行，不把无工具时的数值当答案：

<!-- executable: oob.c -->
```c
#include <stdlib.h>
int main(int argc, char **argv) {
    (void)argv;
    int *values = malloc(2u * sizeof *values);
    if (values == NULL) return 2;
    size_t index = argc > 1 ? 2u : 1u;
    values[index] = 7;
    free(values);
    return 0;
}
```

用 `cc -std=c17 -Wall -Wextra -O0 -g -fsanitize=address oob.c -o oob`，执行 `./oob trigger` 应非零退出并报告 heap-buffer-overflow；`./oob` 写有效索引 1，应退出 0。修复方式是在写之前确认 `index < 2`，失败时先 free 再返回明确错误。更大缓冲或删除 trigger 输入会掩盖而非修复范围契约。把 count 和容量来自哪里追到调用者，才可能找到真正根因。

## 来源与适用范围

核对日期：2026-09-07。课程仍按 C17 编译；以下 N1570 是 C11 草案，仅用于核对共通条款，不冒称已读取本轮未能解密的 N2176 PDF。[C11 N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf) 的 3.4、5.1.1.3、6.5、6.10 分别约束行为分类、诊断、表达式和预处理；[LLDB 官方教程](https://lldb.llvm.org/use/tutorial.html) 用于核对断点、单步、调用栈与监视点命令。这里是单线程本地调试，不声称验证了多线程竞态或全部优化构建。

## 本章练习

### C13-Q1：优先级错误与重复求值不是同一缺陷

**题型**：宏展开与代码追踪
**作答产物**：预处理展开结果、求值次数、最小修复和测试。

对 `#define MIN(a,b) a < b ? a : b`，手工展开 `10 * MIN(2,3)`，比较实际分组与数学意图。再判断“加全套括号就能安全传入 `SQUARE(i++)`”是否成立。

<details><summary>讲解、判定与验证</summary>

展开为 `10 * 2 < 3 ? 2 : 3`，乘法先于比较，得到 3 而不是 20。给整个表达式和参数加括号修复这个分组问题；但 `SQUARE(i++)` 展开成 `((i++)*(i++))`，对同一标量的修改未序列化，属于 UB，没有合法预期数值。改为类型明确的函数，使实参只在调用前求值一次；仍需避免函数实参之间对同一对象发生未序列化冲突。用预处理输出检查展开、用无副作用数值验证修复，不运行 UB 来“测答案”。游戏伤害宏若重复消费随机数或修改状态，会把结算顺序藏起来。
</details>

### C13-Q2：从 ASan 报告回到容器契约

**题型**：诊断报告解读与最小反例
**作答产物**：首个非法访问、根因假设排序、修复补丁和回归测试。

给定摘要：

```text
ERROR: AddressSanitizer: heap-buffer-overflow on address 0x...6020
READ of size 4 at 0x...6020
    #0 sum_alive runtime.c:41
    #1 main arena.c:18
0x...6020 is located 0 bytes after 32-byte region [0x...6000,0x...6020)
allocated by malloc(8 * sizeof(int)) at runtime.c:12
```

相关代码：

```c
int sum_alive(const int *health, size_t count) {
    int total = 0;
    for (size_t i = 0; i <= count; ++i) total += health[i];
    return total;
}
```

1. 计算分配能容纳几个元素、非法地址对应哪个索引；
2. 若调用传入 `count=8`，定位首个错误与修复；
3. 若把循环改成 `<` 后报告仍存在，按优先级列出至少三项要检查的契约；
4. 设计能在修复后阻止回归的最小测试集。

<details><summary>讲解、判定与验证</summary>

32 字节且每次读 4 字节，分配容纳 8 个 int，合法索引 0–7；报告地址正好位于区域末尾之后，符合读取 `health[8]`。传入 count=8 时，`i<=count` 在 i=8 仍执行，首个非法访问就是该行；修复为 `i<count`，并把契约写成 count 是元素数量而不是最后索引。

若 `<` 后仍越界，优先检查：调用者传入的 count 是否真实且 `count<=capacity`；分配乘法是否溢出或用了错误元素大小；health 指针是否已因 realloc/free 失效；删除/追加是否使 length 元数据超过 capacity；多线程或别名是否并发改变元数据。ASan 指向第一次被观察到的非法内存访问，不自动证明唯一根因，更不证明其他逻辑正确。

最小测试：`count=0` 不读指针（按契约可允许 NULL）；`count=1` 只读首元素；`count=8` 读到最后合法元素；已知 `{1..8}` 求和为 36；故意传 `count=9` 不应进入不安全函数——更好的公开 API 接收/验证 capacity 或由容器封装 length。用 ASan/UBSan 运行边界测试，并保留普通结果断言。

评分点：索引和字节计算正确；修复半开区间；进一步检查调用者元数据、分配与生命周期；测试覆盖空、单个、满容量和结果。常见错误是把分配扩大到 9 以掩盖 `<=`，或关闭 Sanitizer。游戏映射：对象池越界常在邻接组件上爆炸，诊断必须回到“有效区间由谁拥有和更新”的容器契约。
</details>

### C13-Q3：分别分类，而不是一律说“机器相关”

**题型**：语义分类与反例
**作答产物**：逐案例分类、标准允许的结果集合和不可作出的假设。

判断四种情况：①读取 `values[2]`，其中数组只有 2 个元素；②普通 char 是 signed 还是 unsigned；③两个都只读状态的函数在 `left() + right()` 中的先后；④源文件缺少分号。它们各需要哪种证据？

<details><summary>讲解、判定与验证</summary>

①越界 UB，标准不规定结果；②实现定义，应查目标实现文档；③未指定先后，允许两种顺序，但不能依赖某次观察；④语法违反要求编译器诊断，不能把它和已构建程序中的 UB 混成一类。独立副作用若涉及同一标量再另判是否未序列化。验证以适用 C17 条款和诊断为依据，运行实验只是观察实现。游戏回放不能依赖③的顺序，外部文件不能默认②的符号性。
</details>

下一章把这些局部知识组合成模块化、可测试、可测量的主实践。
