# 6. 多文件、头文件与链接：模块边界怎样变成构建边界

单文件程序适合学习语法，却不能承载真实运行时。把代码拆成 `runtime.c`、`arena.c` 和测试文件后，新的问题出现：声明放哪里？某个名字能否被另一个文件看见？为什么每个 `.c` 都能单独编译，却在最后链接失败？

## 机制

本章把可观察现象还原为语言机制和不变量，而不是只记 API 名称。

## 6.1 翻译单元与头文件

每个 `.c` 文件经过预处理后形成一个翻译单元。`#include "runtime.h"` 不是运行时加载文件，而是把头文件文本纳入当前翻译单元。头文件适合放类型、宏、函数原型和外部变量声明，不应放普通外部函数的重复定义。

```c
/* runtime.h */
#ifndef RUNTIME_H
#define RUNTIME_H
int clamp_health(int health, int maximum);
#endif
```

include guard 防止同一翻译单元重复包含。`static` 函数定义限制在当前翻译单元内部；不需要公开的辅助函数应优先使用它，减少命名冲突和可见 API。

## 6.2 声明、定义、链接

```bash
cc -std=c17 -Wall -Wextra -Wpedantic -c runtime.c -o runtime.o
cc -std=c17 -Wall -Wextra -Wpedantic -c arena.c -o arena.o
cc runtime.o arena.o -o arena
```

前两条只生成目标文件，最后一条解析跨文件符号。`extern int g_score;` 是声明，不分配定义存储；`int g_score;` 在文件作用域通常是定义。全局变量会扩大状态所有权和测试耦合，宁可通过拥有者结构体传递。

故意失败实验：把 `runtime.o` 从链接命令移除，得到 undefined reference；把同一个非 `static` 函数体放进两个 `.c`，得到 multiple definition；让原型参数与定义不一致，观察警告或错误。三类失败分别对应链接输入重复、定义重复和接口不一致。

## 6.3 Make 的依赖图

Makefile 不是魔法脚本，而是目标与依赖的有向图：

```make
CFLAGS = -std=c17 -Wall -Wextra -Wpedantic -g
arena: arena.o runtime.o
	$(CC) $(CFLAGS) $^ -o $@
arena.o: arena.c runtime.h
runtime.o: runtime.c runtime.h
```

当 `runtime.h` 改变时，依赖它的两个目标都应重编译；只列 `.c` 会留下过期对象。运行 `make -n` 先查看将执行什么，`make` 再实际执行。构建成功不代表链接到的是正确版本，必要时删除对象做冷构建。

## 验证、失败与游戏映射

用 `nm arena.o`（平台可用时）观察定义和未解析符号，用 `make -n` 检查依赖，用 `make clean all` 验证从空产物开始。游戏模块可对应规则库、渲染适配器、平台层和测试；低层模块不应直接包含 Unity UI 或场景对象。

## 进一步拆解与实验

## 6.5 头文件、定义和链接的最小实验

建立三个文件：

```c
/* health.h：声明，给调用者看的接口 */
#ifndef HEALTH_H
#define HEALTH_H
int clamp_health(int health, int max_health);
#endif
```

```c
/* health.c：定义，真正提供机器码 */
#include "health.h"
int clamp_health(int health, int max_health) {
    if (max_health < 0) return 0;
    if (health < 0) return 0;
    return health > max_health ? max_health : health;
}
```

```c
/* main.c：使用者 */
#include <stdio.h>
#include "health.h"
int main(void) {
    printf("%d\n", clamp_health(30, 20));
    return 0;
}
```

分别运行：

```bash
cc -std=c17 -Wall -Wextra -Wpedantic -c main.c -o main.o
cc -std=c17 -Wall -Wextra -Wpedantic -c health.c -o health.o
cc main.o health.o -o health-demo
```

如果 `main.c` 没有包含头文件，编译器无法检查调用是否匹配；如果只链接 `main.o`，会得到未解析的 `clamp_health`；如果在头文件放普通函数定义并被多个 `.c` 包含，可能得到重复定义。头文件保护宏防止同一个翻译单元重复包含，但不能替你处理跨翻译单元的定义规则。

## 6.6 `static` 与可见性

文件作用域的 `static` 函数只在当前翻译单元可见：

```c
static int normalize_damage(int damage) {
    return damage < 0 ? 0 : damage;
}
```

这有两个作用：隐藏模块内部实现，并避免与别的文件同名冲突。对外暴露的函数应尽量少；每多一个公共符号，就多一个需要维护的契约。不要把所有函数都放进头文件，也不要用全局变量跨模块传递状态而不写所有权和生命周期。

## 6.7 Make 规则表达依赖

```make
CFLAGS = -std=c17 -Wall -Wextra -Wpedantic -g
arena: main.o health.o
\t$(CC) $(CFLAGS) $^ -o $@

main.o: main.c health.h
health.o: health.c health.h
```

`main.o` 依赖 `health.h` 是因为头文件改变时，`main.o` 必须重新编译；链接规则只在对象文件改变时重新生成可执行文件。`make` 比“每次手敲一长串命令”可靠，因为依赖关系成为可检查的文本。它不会自动知道隐藏依赖：若生成脚本、环境变量或工具版本影响输出，也必须显式记录。

## 本章练习

### C06-Q1：头文件应该放什么

判断“函数原型、普通函数体、结构体定义、`static` 辅助函数”各自是否适合放公共头文件，并说明原因。

<details><summary>最小提示</summary>

问它是声明、可重复定义的类型，还是会在每个包含者中生成实体。
</details>

<details><summary>讲解与验证</summary>

函数原型和需要共享的结构体定义适合头文件；普通外部函数体放头文件会在多个翻译单元产生重复定义，除非明确使用 `static inline` 等规则；`static` 辅助函数通常留在 `.c`，避免泄漏 API。用两个 `.c` 都包含头文件的最小工程运行链接验证。游戏映射：插件头文件应只暴露稳定 ABI 所需的边界。
</details>

### C06-Q2：为什么头文件改了却没重编译

Makefile 只写 `runtime.o: runtime.c`，而 `runtime.c` 包含 `runtime.h`。修改头文件后仍使用旧对象，如何修复和验证？

<details><summary>最小提示</summary>

把直接包含关系写入依赖图。
</details>

<details><summary>讲解与验证</summary>

改为 `runtime.o: runtime.c runtime.h`，所有直接包含头文件的目标都列出它。运行 `touch runtime.h && make -n`，预期看到对应 `.o` 重编译；再 `make clean all` 做冷构建。常见错误是只给最终可执行文件列所有源文件，导致增量构建无法判断。游戏映射：资源导入和生成代码也需要显式输入依赖，否则编辑器缓存会掩盖错误。
</details>

下一章利用模块 API 传递数组，开始讨论连续内存、长度和有效区间。
