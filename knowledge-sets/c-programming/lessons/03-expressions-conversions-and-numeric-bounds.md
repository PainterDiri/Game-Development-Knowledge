# 3. 表达式与数值边界：同一公式为什么算出不同答案

有了类型化对象后，程序通过表达式计算新值。但 `damage * multiplier / armor` 不是脱离类型的数学式：求值顺序、整数除法、提升、符号和可表示范围都会参与结果。

## 3.1 运算优先级不是求值顺序

```c
int result = base + bonus * 2;
```

优先级规定表达式如何分组，所以先算乘法；它不保证函数参数从左到右求值。不要写多个互相依赖的副作用：

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

转换应表达设计意图，而不是用强制转换压掉警告。若原值超出目标类型范围，转换结果可能实现定义或取模；先检查范围，再转换。

## 3.3 有符号与无符号混合

`size_t` 是无符号整数类型，适合表示对象大小和数组计数，但负值转换成它会变成很大的值：

```c
int requested = -1;
size_t count = (size_t)requested;
```

因此文本解析应先进入足够宽的有符号类型，检查 `0 <= value <= limit`，最后再转 `size_t`。循环 `for (size_t i = count - 1; i >= 0; --i)` 也不会按预期终止，因为无符号值永远不小于 0。反向遍历可写 `for (size_t i = count; i-- > 0;)`，并通过 0、1、最大数量测试理解边界。

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
if (damage > INT_MAX - total_damage) {
    return false;
}
total_damage += damage;
```

对无符号整数，回绕是定义好的模运算，但通常仍然不是游戏规则想要的行为。语言“定义了结果”不代表业务“接受这个结果”。

## 3.9 运算顺序、求值顺序与副作用

优先级回答“表达式怎样分组”，不总是回答“子表达式何时求值”。不要写依赖多个副作用顺序的代码：

```c
int i = 0;
int value = i++ + i++; /* 不应依赖这种写法的结果 */
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

绝对误差适合接近零的值，相对误差适合量级变化大的值；只使用一个固定 `0.000001` 可能在大数或接近零时失效。游戏中的位置、冷却和动画时间需要先决定单位、积分方式和可接受漂移，而不是看到 `==` 就机械替换。

## 本章练习

### C03-Q1：容量检查为何写成减法

在 `used <= capacity` 前提下，解释 `requested > capacity - used` 为什么比 `used + requested > capacity` 更稳妥，并指出前提失效时会怎样。

<details><summary>最小提示</summary>

比较两式在加法超出 `size_t` 上限时的行为。
</details>

<details><summary>讲解与验证</summary>

无符号加法会回绕，危险表达式可能变小而错误放行；减法在已知 `used <= capacity` 时保持合法范围。若 `used > capacity`，减法也会回绕，所以入口必须先验证内部不变量。用 `SIZE_MAX` 附近的值写单元测试。常见错误是只测试小容量。游戏映射：对象池、网络包、资源缓冲区都用同类检查。
</details>

### C03-Q2：百分比为何变成零

`int percent = current / maximum * 100;` 在 `1/2` 时得到 0。给出整数版和浮点版修复，并比较溢出与舍入。

<details><summary>最小提示</summary>

改变乘除顺序会保留整数精度，但可能扩大中间值。
</details>

<details><summary>讲解与验证</summary>

整数版可写 `current * 100 / maximum`，但要先保证 `maximum != 0` 并防止乘法溢出；可提升到更宽类型。浮点版写 `(float)current / (float)maximum * 100.0f`，能表示小数但有舍入误差。测试 0、1/2、等于最大值和接近上限。游戏映射：血条显示可用浮点比率，权威资源结算通常更适合有明确舍入规则的整数。
</details>

下一章把表达式放入分支和循环，并用不变量证明每次状态更新都留在合法范围。
