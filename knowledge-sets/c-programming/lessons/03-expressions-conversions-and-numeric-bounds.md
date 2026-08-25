# 3. 表达式、转换与数值边界：结果不是“看起来合理”

如果 `health -= damage` 的结果会受类型影响，下一步就是建立表达式的计算模型。游戏中最隐蔽的 bug 往往不是语法错，而是“编译成功、运行一阵、某个边界值才错”。

## 整数除法和浮点除法

```c
#include <stdio.h>
int main(void) {
    int frames = 5;
    int seconds_int = frames / 60;
    double seconds_real = frames / 60.0;
    printf("int=%d real=%.4f\n", seconds_int, seconds_real);
}
```

`int / int` 仍是整数除法，余数被丢弃；只要一个操作数是浮点，计算就在浮点域进行。帧时间、冷却时间和比例伤害都应先决定语义：是离散 tick 还是连续近似？不要靠“加一个 `.0`”掩盖未定义的单位。

## 转换、溢出和精度

- **隐式转换**：编译器为匹配运算或赋值自动改变表示；可能丢精度、改变符号或截断。
- **窄化**：把较大范围值放入较小类型，例如 `double` → `int`。
- **有符号整数溢出**：不是“自动绕回”这么简单，在 C 中可能导致未定义行为；无符号整数按模运算，但业务上仍可能错。
- **浮点误差**：二进制浮点不精确表示多数十进制小数；比较通常需要容差或改用整数单位。

```c
#include <limits.h>
#include <stdio.h>
int main(void) {
    printf("INT_MAX=%d\n", INT_MAX);
    int x = INT_MAX;
    /* x += 1;  // 故意失败：有符号溢出 */
    printf("x=%d\n", x);
}
```

## 一个可复用的边界函数

```c
#include <stdbool.h>
#include <limits.h>

bool add_int_checked(int left, int right, int *out) {
    if (right > 0 && left > INT_MAX - right) return false;
    if (right < 0 && left < INT_MIN - right) return false;
    *out = left + right;
    return true;
}
```

这个函数的机制是：在执行加法前，把结果必须满足的范围改写成对 `left` 的比较，因此永远不先触发溢出。返回 `false` 是错误路径；调用者可以拒绝伤害、钳制数值或记录诊断，但不能把失败当成成功。

## 验证与游戏映射

用表格测试 `INT_MAX + 1`、`-1 + INT_MIN`、`30 / 60`、`30 / 60.0`；编译加 `-Wconversion -Wsign-conversion`。在 Unity/UE 中，类似问题会出现在帧率转换、固定步长累加、经验值上限和网络序列化。下一章需要把布尔表达式接到分支和循环，并用不变量而不是直觉判断它是否终止。

> 参考：[N1570 §6.3 转换](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)、[GCC Warning Options](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html)。
