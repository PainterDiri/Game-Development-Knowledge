# 6. 头文件、链接与模块：声明是边界，不是实现

单文件程序可以运行，但一个游戏运行时组件必须分模块：数学、随机、波次和测试不能互相复制定义。多文件失败通常发生在两个阶段：编译器不知道声明，或链接器找不到定义。

## 最小多文件模块

`damage.h`：

```c
#ifndef DAMAGE_H
#define DAMAGE_H
int apply_damage(int health, int damage);
#endif
```

`damage.c`：

```c
#include "damage.h"
int apply_damage(int health, int damage) {
    if (damage < 0) return health;
    return damage >= health ? 0 : health - damage;
}
```

`main.c` 只包含头文件，不复制函数体。构建：

```bash
cc -std=c17 -Wall -Wextra -pedantic -c damage.c
cc -std=c17 -Wall -Wextra -pedantic -c main.c
cc damage.o main.o -o damage_demo
```

头文件描述消费者可以依赖的公开契约；实现文件拥有内部细节。`static` 函数只在当前翻译单元可见，适合隐藏辅助函数；不要在头文件定义普通全局变量，否则多个翻译单元可能产生重复定义。

## 故意失败与诊断

- 删除 `#include "damage.h"`：编译阶段可能出现隐式声明或类型冲突；
- 保留声明但不把 `damage.o` 传给链接器：链接阶段出现 undefined symbol；
- 在头文件放 `int counter = 0;` 并被多个 `.c` 包含：每个翻译单元都拥有一份定义。

诊断时先问“哪一阶段失败”，不要把链接错误当成运行时 bug。

## API 设计边界

公开函数要避免依赖具体场景对象：`apply_damage(int, int)` 比 `apply_damage(Player*, UnityEngineObject*)` 更可移植。公开接口还要写单位、范围、失败表示和线程假设。C 的模块边界是后续 C++/C# 适配层的稳定内核。

## 验证与映射

把 `make` 命令或手动构建拆成“编译每个源文件 → 链接 → 运行测试”；只改 `damage.c` 时不应影响其他模块的声明。Unity Native Plugin、UE Module 和普通静态库都依赖类似的编译/链接边界，但它们还各自有平台 ABI 和构建系统。下一章在 API 中传递连续内存，并说明长度从哪里来。

> 参考：[N1570 §6.2.2 标识符链接](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)、[GCC C Dialect Options](https://gcc.gnu.org/onlinedocs/gcc/C-Dialect-Options.html)。
