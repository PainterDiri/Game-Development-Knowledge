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

这组命令是模块命名示意，需要已有的 runtime.c/arena.c；本章下方 health.h、health.c、main.c 才是可从空目录复现的完整文件组。前两条只生成目标文件，最后一条解析跨文件符号。`extern int g_score;` 是声明，不分配定义存储；`int g_score;` 在文件作用域是暂定定义：若本翻译单元没有另一个完整定义，会在翻译单元结束时按零初始化定义处理。全局变量会扩大状态所有权和测试耦合，宁可通过拥有者结构体传递。

故意失败实验：把 `runtime.o` 从链接命令移除，得到 undefined reference；把同一个非 `static` 函数体放进两个 `.c`，得到 multiple definition；让原型参数与定义不一致，观察警告或错误。三类失败分别对应链接输入缺失、定义重复和接口不一致。

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

用 `nm arena.o`（平台可用时）观察定义和未解析符号，用 `make -n` 检查依赖，使用下方完整 Makefile 的 `make clean && make all` 验证从空产物开始（顺序执行，不把可能并行的 clean 与 all 当成依赖链）。游戏模块可对应规则库、渲染适配器、平台层和测试；低层模块不应直接包含 Unity UI 或场景对象。

## 进一步拆解与实验

## 6.4 头文件、定义和链接的最小实验

建立三个文件：

<!-- executable: health.h -->
```c
/* health.h：声明，给调用者看的接口 */
#ifndef HEALTH_H
#define HEALTH_H
int clamp_health(int health, int max_health);
#endif
```

<!-- executable: health.c -->
```c
/* health.c：定义，真正提供机器码 */
#include "health.h"
int clamp_health(int health, int max_health) {
    if (max_health < 0) return 0;
    if (health < 0) return 0;
    return health > max_health ? max_health : health;
}
```

<!-- executable: main.c -->
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

## 6.5 `static` 与可见性

文件作用域的 `static` 函数只在当前翻译单元可见：

```c
static int normalize_damage(int damage) {
    return damage < 0 ? 0 : damage;
}
```

这有两个作用：隐藏模块内部实现，并避免与别的文件同名冲突。对外暴露的函数应尽量少；每多一个公共符号，就多一个需要维护的契约。不要把所有函数都放进头文件，也不要用全局变量跨模块传递状态而不写所有权和生命周期。

## 6.6 Make 规则表达依赖

<!-- executable: Makefile -->
```make
CC = cc
CFLAGS = -std=c17 -Wall -Wextra -Wpedantic -g
.PHONY: all clean
all: health-demo
health-demo: main.o health.o
	$(CC) $(CFLAGS) $^ -o $@
main.o: main.c health.h
	$(CC) $(CFLAGS) -c $< -o $@
health.o: health.c health.h
	$(CC) $(CFLAGS) -c $< -o $@
clean:
	rm -f main.o health.o health-demo
```

只在新建的章节临时目录保存这些文件。配方行必须以真实 Tab 开头，不是字符 `\t`；`$@` 是目标名，`$<` 是第一个依赖，`$^` 是全部依赖。clean 只删除本例三个明确产物；不要把它扩成递归清理源码目录。运行 `make all && ./health-demo` 得到 20，第二次 `make -n` 不应列编译命令；`touch health.h` 后 `make -n` 应显示两个编译和一次链接。


`main.o` 依赖 `health.h` 是因为头文件改变时，`main.o` 必须重新编译；链接规则只在对象文件改变时重新生成可执行文件。`make` 比“每次手敲一长串命令”可靠，因为依赖关系成为可检查的文本。它不会自动知道隐藏依赖：若生成脚本、环境变量或工具版本影响输出，也必须显式记录。

## 本章练习

### C06-Q1：头文件应该放什么

**题型**：模块边界分类与短代码
**作答产物**：声明/定义/内部实现分类表和可链接的最小文件布局。

判断“函数原型、普通函数体、结构体定义、`static` 辅助函数”各自是否适合放公共头文件，并说明原因。


<details><summary>讲解、判定与验证</summary>

函数原型和需要共享的结构体定义适合头文件；普通外部函数体放头文件会在多个翻译单元产生重复定义，除非明确使用 `static inline` 等规则；`static` 辅助函数通常留在 `.c`，避免泄漏 API。用两个 `.c` 都包含头文件的最小工程运行链接验证。游戏映射：插件头文件应只暴露稳定 ABI 所需的边界。
</details>

### C06-Q2：从依赖图判断最小重建集合

**题型**：Make 依赖图推演与时间戳诊断
**作答产物**：修改 3 类文件后的重建目标表；修正后的 Make 规则；一次可执行验证。

项目关系：

```text
arena -> main.o runtime.o ui.o
main.c    includes runtime.h, ui.h
runtime.c includes runtime.h, config.h
ui.c      includes ui.h, config.h
```

当前 Makefile 却只有：

```make
main.o: main.c
runtime.o: runtime.c
ui.o: ui.c
arena: main.o runtime.o ui.o
```

分别修改 `runtime.h`、`config.h`、`ui.c` 时，正确的最小重建集合是什么？现有规则会漏掉哪些？写出修正规则，并用 `touch` 与 `make -n` 设计验证；说明为什么最后仍要做一次冷构建。

<details><summary>讲解、判定与验证</summary>

修改 `runtime.h` 应重编 `main.o`、`runtime.o`，再重链接 `arena`；修改 `config.h` 应重编 `runtime.o`、`ui.o`，再重链接；修改 `ui.c` 只需重编 `ui.o` 并重链接。现有规则对两个头文件修改都完全漏重编，`ui.c` 修改则能触发正确链。

直接规则：

```make
main.o: main.c runtime.h ui.h
runtime.o: runtime.c runtime.h config.h
ui.o: ui.c ui.h config.h
arena: main.o runtime.o ui.o
```

可执行验证：先 `make clean && make` 建基线，记录对象时间；运行 `touch config.h && make -n`，预期只打印 runtime/ui 的编译命令和最终链接，不应编译 main；再实际 `make` 并检查时间。对 `runtime.h` 重复。大型项目可让编译器生成 `.d` 依赖文件，避免手写漏项。

冷构建 `make clean && make` 只能证明从空产物能建成；增量实验才证明依赖图正确。反过来，增量成功也可能只是旧对象恰好兼容，因此发布前仍需冷构建对照。评分点：三个重建集合正确；规则包含直接 include；区分图正确性与偶然链接成功。常见错误是只让 `arena` 依赖头文件，却不让对应 `.o` 失效。游戏映射：脚本程序集、shader include 和生成代码同样需要显式依赖，否则编辑器里“看似改了”但构建继续使用陈旧中间产物。
</details>
