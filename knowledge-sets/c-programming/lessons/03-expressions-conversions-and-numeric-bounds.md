# 3. 表达式与数值边界：同一公式为什么算出不同答案

有了类型化对象后，程序通过表达式计算新值。但 `damage * multiplier / armor` 不是脱离类型的数学式：求值顺序、整数除法、提升、符号和可表示范围都会参与结果。

## 3.1 运算优先级不是求值顺序

```c
int result = base + bonus * 2;
```

优先级规定语法分组，因此表达式是 `base + (bonus * 2)`，不是 `(base + bonus) * 2`。这里加法需要乘积的值，但优先级本身不是通用的执行先后规则，也不保证函数参数从左到右求值。不要写多个互相依赖的副作用：

```c
int i = 0;
values[i++] = i; /* 对顺序作了危险假设 */
```

把每个状态变化拆成独立语句，使输入和结果可观察。

## 3.2 整数除法与显式转换

```c
int current = 1;
int maximum = 2;
float ratio_bad = current / maximum;          /* 先做整数除法，结果 0 */
float ratio_ok = (float)current / maximum;    /* 0.5 */
```

转换应表达设计意图，而不是用强制转换压掉警告。若原值超出目标类型范围，整数到整数的转换可能实现定义或按无符号规则取模；浮点到整数超出可表示范围则可能是未定义行为。必须先区分转换类别、检查范围，再转换。

## 3.3 有符号与无符号混合

`size_t` 是无符号整数类型，适合表示对象大小和数组计数，但负值转换成它会变成很大的值：

```c
int requested = -1;
size_t count = (size_t)requested;
```

对于本课上限较小的计数，文本解析可先进入足够宽的有符号类型，检查 `0 <= value <= limit`，最后再转 `size_t`。若要接受无符号类型的完整范围，有符号中间类型可能装不下；需改用无符号解析函数，并在解析前明确拒绝负号、随后检查范围和整串消费（第 8 章展开）。循环 `for (size_t i = count - 1; i >= 0; --i)` 也不会按预期终止，因为无符号值永远不小于 0。反向遍历可写 `for (size_t i = count; i > 0;) { --i; /* 访问第 i 项 */ }`，并通过 0、1、最大数量测试理解边界；先判断再递减，空区间不会发生无符号回绕。

比较也会转换：`-1 < 1u` 为假，因为 int 与 unsigned int 同等级比较时，-1 先转成 UINT_MAX。这不是“负数变大”的业务规则，而是通常算术转换。unsigned char 等比 int 窄的类型还可能先提升为 int：只要 int 能表示该类型全部值，运算就在 int 中进行；否则提升为 unsigned int。因此不能仅凭变量名带 unsigned，就断言中间表达式必定按该窄类型回绕。对不同等级的有符号/无符号类型，应比较等级和可表示范围，不能简单概括成“总转 unsigned”。

## 3.4 溢出规则不同

无符号整数按模运算回绕；有符号整数溢出是未定义行为。容量检查不要先做可能溢出的加法：

```c
/* 危险：used + requested 可能先溢出 */
if (used + requested > capacity) return false;

/* 前提 used <= capacity；减法形式避免加法溢出 */
if (requested > capacity - used) return false;
```

这段逻辑依赖不变量 `used <= capacity`。若前置状态已坏，第二种写法也不能自动修复系统，必须在模块入口或断言中验证。

## 3.5 浮点数不是实数

二进制浮点不能精确表示许多十进制小数。不要用 `position == target` 判断移动是否完成；使用允许误差、剩余距离或跨越检测：

```c
#include <math.h>
if (fabsf(position - target) <= 0.001f) { /* 到达 */ }
```

容差不是随便填的常量，应与单位、数值范围和算法误差相关。累计 `delta_time` 会积累误差；确定性回放还要考虑平台、编译器优化和浮点环境。

## 3.6 验证数值边界

为伤害公式列测试表：0、1、最大护甲、负输入是否拒绝、接近整数上限、会发生截断的小数。编译时开启 `-Wall -Wextra -Wconversion -Wsign-conversion` 可以暴露更多隐式转换，但它们会较严格，应逐条解释而非盲目关闭。

常见失败是“测试中数值很小，所以生产中也不会溢出”，或先转换成无符号再检查 `< 0`。游戏映射：生命值、经验、货币、坐标、帧计数、网络序号和资源大小都必须定义范围与溢出策略。

## 进一步拆解与实验

## 3.7 转换发生在哪里：先写出类型，再写公式

C 会在表达式中进行整数提升和通常算术转换。为了不靠猜，给每一步标注类型：

```c
int kills = 3;
int rooms = 8;
double ratio = (double)kills / (double)rooms;
```

`kills / rooms` 先按整数除法得到 `0`，再赋给 `double` 也只会得到 `0.0`；转换必须发生在除法之前。强制转换不是“让答案变准确”的魔法，它只是改变参与运算的类型。转换有代价：把很大的 `uint64_t` 转为 `int` 可能丢失范围，窄化转换必须先证明值在目标类型可表示范围内。

## 3.8 安全边界的证明方式

对容量和长度，优先写出能避免溢出的条件：

```c
if (count > capacity - incoming) {
    return false; /* 不足，且没有先计算可能溢出的 count + incoming */
}
count += incoming;
```

这个写法要求先证明 `incoming <= capacity`；若 `incoming` 本身可能超大，应先检查它。不要把 `count + incoming <= capacity` 当成无条件安全，因为加法在无符号类型上会回绕。

对有符号整数，标准不允许把溢出当作自然回绕：

```c
#include <limits.h>
if (damage < 0 || total_damage < 0 || damage > INT_MAX - total_damage) {
    return false;
}
total_damage += damage;
```

对无符号整数，回绕是定义好的模运算，但通常仍然不是游戏规则想要的行为。语言“定义了结果”不代表业务“接受这个结果”。

## 3.9 运算顺序、求值顺序与副作用

优先级回答“表达式怎样分组”，不总是回答“子表达式何时求值”。不要写依赖多个副作用顺序的代码：

```c
int i = 0;
int value = i++ + i++; /* 未序列化地修改同一标量：未定义行为 */
```

把副作用拆成独立语句：

```c
int left = i++;
int right = i++;
int value = left + right;
```

可读性和可验证性比少写一行更重要，尤其是伤害结算、随机数消耗和事件顺序。编译器在不同优化级别下可能重排没有依赖的表达式，因此“调试版刚好如此”不是顺序契约。

## 3.10 浮点比较与误差预算

浮点数用有限位表示二进制近似值。判断两个计算结果是否“足够接近”时，先定义允许误差：

```c
#include <math.h>
#include <stdbool.h>

bool nearly_equal(double a, double b, double abs_eps, double rel_eps) {
    double diff = fabs(a - b);
    if (diff <= abs_eps) return true;
    return diff <= rel_eps * fmax(fabs(a), fabs(b));
}
```

这个片段仅用于有限 `a/b`、非负有限容差，而且中间减法和乘法不溢出的情况；NaN、无穷以及极大量级需要单独规定策略，不能把它当作通用浮点等价关系。

绝对误差适合接近零的值，相对误差适合量级变化大的值；只使用一个固定 `0.000001` 可能在大数或接近零时失效。游戏中的位置、冷却和动画时间需要先决定单位、积分方式和可接受漂移，而不是看到 `==` 就机械替换。

## 3.11 把百分比的范围写进实现

在本例明确 `0 <= current <= maximum <= INT_MAX` 且 `maximum > 0`。函数片段需要 `<stdbool.h>`、`<limits.h>`、`<stddef.h>`：

```c
bool percent_floor(int current, int maximum, int *out) {
    if (out == NULL || current < 0 || maximum <= 0 || current > maximum)
        return false;
    if (current > INT_MAX / 100) return false;
    *out = current * 100 / maximum;
    return true;
}
```

它故意拒绝中间乘法装不下的输入，即使数学结果只有 0–100；这是正确但保守的契约，不是支持任意生命上限的方案。“转成更宽类型”只有目标确实更宽且足够容纳中间值才成立。先验证 1/2→50、0/20→0、20/20→100、maximum=0 拒绝且输出不变，再讨论更宽类型或商余分解。浮点血条显示与整数权威结算的舍入要求不能混用。
## 3.12 从小值到表示上限的可运行检查

保存为 `numeric.c`，用 `cc -std=c17 -Wall -Wextra -Wpedantic numeric.c -o numeric && ./numeric` 运行，不带 `-DNDEBUG`。assert 来自 `<assert.h>`：条件为假会中止并报告，条件为真继续；它适合测试内部预期，不替代发布版本的外部输入检查。预期 `numeric: passed`。极值测试不申请巨大内存，只验证纯算术边界。

<!-- executable: numeric.c -->
```c
#include <assert.h>
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
bool percent_floor(int current, int maximum, int *out) {
    if (out == NULL || current < 0 || maximum <= 0 || current > maximum)
        return false;
    if (current > INT_MAX / 100) return false;
    *out = current * 100 / maximum;
    return true;
}
static bool fits(size_t used, size_t requested, size_t capacity) {
    return used <= capacity && requested <= capacity - used;
}
int main(void) {
    int result = -1;
    assert(percent_floor(1, 2, &result) && result == 50);
    assert(percent_floor(0, 20, &result) && result == 0);
    assert(percent_floor(20, 20, &result) && result == 100);
    assert(!percent_floor(1, 0, &result) && result == 100);
    assert(!percent_floor(INT_MAX, INT_MAX, &result) && result == 100);
    assert(fits(0u, 0u, 0u));
    assert(fits(SIZE_MAX - 1u, 1u, SIZE_MAX));
    assert(!fits(SIZE_MAX, 1u, SIZE_MAX));
    assert(!fits(2u, 0u, 1u));
    puts("numeric: passed");
    return 0;
}
```

## 本章练习

### C03-Q1：容量检查为何写成减法

**题型**：边界计算与代码修复
**作答产物**：逐步算式、溢出边界、修复代码和边界测试。

在 `used <= capacity` 前提下，解释 `requested > capacity - used` 为什么比 `used + requested > capacity` 更稳妥，并指出前提失效时会怎样。


<details><summary>讲解、判定与验证</summary>

无符号加法会回绕，危险表达式可能变小而错误放行；减法在已知 `used <= capacity` 时保持合法范围。若 `used > capacity`，减法也会回绕，所以入口必须先验证内部不变量。用 `SIZE_MAX` 附近的值写单元测试。常见错误是只测试小容量。游戏映射：对象池、网络包、资源缓冲区都用同类检查。
</details>

### C03-Q2：整数比例、舍入与溢出

**题型**：逐表达式类型计算与边界设计
**作答产物**：4 组输入的结果表；两种实现；除零、舍入和溢出契约。

比较下面三种写法，假设 `current`、`maximum` 是非负 `int`：

```c
A: int p = current / maximum * 100;
B: int p = current * 100 / maximum;
C: float p = (float)current / (float)maximum * 100.0f;
```

对 `(1,2)`、`(2,3)`、`(3,2)`、`(INT_MAX, INT_MAX)` 写出 A/B 在 C 语义有定义时的精确整数结果；遇到未定义行为必须标出，不能虚构数值。另写出 C 的数学期望附近值，并指出哪一步可能除零或有符号溢出。然后给出：

- 一个返回 0–100、向下取整并避免中间乘法溢出的整数 API；
- 一个允许超过 100% 的浮点 API。

<details><summary>讲解、判定与验证</summary>

A 先做整数除法：`1/2→0`、`2/3→0`、`3/2→1`、`INT_MAX/INT_MAX→1`，再乘 100，结果分别 0、0、100、100。B 对前三组分别得到 50、66、150；`INT_MAX * 100` 先发生有符号溢出，因此第四组是 UB，没有可写出的精确整数结果。更一般地，只要 `current > INT_MAX / 100`，B 就在除法前失效。C 约为 50.0、66.666…、150.0、100.0，受浮点舍入影响。三式在 `maximum==0` 时都非法或产生非有限结果，必须先定义契约。

一种整数实现：

```c
#include <stdint.h>
#include <stdbool.h>

bool percent_floor_0_100(int current, int maximum, int *out) {
    if (out == NULL || maximum <= 0 || current < 0) return false;
    int clamped = current > maximum ? maximum : current;
    int64_t scaled = (int64_t)clamped * 100;
    *out = (int)(scaled / maximum);
    return true;
}
```

浮点版可返回 `false`/错误码并通过输出参数写 `(float)current / maximum * 100.0f`，不夹到 100；仍需限定非负输入与正分母。评分点：A 的四行、B 的三个合法结果和一个 UB 判断正确；明确 B 先溢出再除并不安全；写出分母、范围、舍入与失败时输出是否保持不变。验证用 0、1/2、2/3、相等、超过上限和 `INT_MAX`。游戏映射：UI 血条通常夹到 100%，而护盾叠层或伤害倍率可能允许超过 100%；显示值与权威结算应分别定义类型和舍入。
</details>

### C03-Q3：优先级不等于求值顺序

**题型**：代码追踪与反例
**作答产物**：求值/副作用顺序表、可保证结论和一个反例。

下面代码试图从两个连续位置取值并推进索引：

```c
int total = values[i++] + values[i++];
```

请判断这段代码是否有可移植的确定结果，指出风险来自哪里，再给出一个更容易审查的改写。

<details><summary>讲解、判定与验证</summary>

加法的语法分组由运算符优先级决定，但两个 `i++` 之间没有足够的顺序关系；同一个标量在一个完整表达式中被多次修改而没有序列点，程序触及未定义行为，不能从一次运行结果推断规则。先检查 `i <= count && count - i >= 2`，再依次读取 `values[i]`、`values[i + 1]`。还需证明两个 int 相加不会溢出，才能计算 total 并最后执行 `i += 2`。数组必须真实包含 count 个有效元素；索引检查不替代对象有效期。边界是 `count` 小于 2、`i` 接近 `SIZE_MAX` 以及读取与推进分到不同阶段后的失败路径；常见错误是只加括号就以为改变了求值顺序。验证可用 `-Wall -Wextra`、Sanitizer 和 count=0/1/2 的测试。游戏映射：输入游标、伤害事件队列和 RNG 消费若把副作用藏在表达式中，会破坏重放和调试的可解释性。
</details>

下一章把表达式放入分支和循环，并用不变量证明每次状态更新都留在合法范围。
