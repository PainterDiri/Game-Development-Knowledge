# 1. 从源文件到进程：先让程序可观察

上一章只给了路线；现在的问题很具体：你写下的 `.c` 文件为什么不能直接“运行”？游戏工程里编辑器、脚本、构建器和最终可执行文件也都经过类似边界。先不要背编译器术语，观察一次完整路径。

## 先运行，再命名

```c
#include <stdio.h>

int main(void) {
    puts("room cleared");
    return 0;
}
```

保存为 `hello.c`，运行：

```bash
cc -std=c17 -Wall -Wextra -pedantic hello.c -o hello
./hello
printf 'exit=%s\n' "$?"
```

`hello.c` 是**源文件**；`cc` 先预处理 `#include`，再把 C 翻译成目标代码，最后链接标准库形成可执行文件；`./hello` 启动一个进程；`return 0` 把成功状态交给操作系统。`-Wall -Wextra -pedantic` 是“多告诉我潜在问题”，不是“保证代码正确”。

```mermaid
flowchart LR
    S[.c 源文件] --> P[预处理]
    P --> C[编译/汇编]
    C --> L[链接库]
    L --> X[可执行文件]
    X --> R[进程：输入 → 状态 → 输出/退出码]
```

## 定义与边界

- **翻译单元**：一个 `.c` 文件经过预处理后的文本；编译器以它为单位生成目标代码。
- **声明**告诉编译器“名字和类型是什么”；**定义**提供实体本身的存储或函数体。
- **链接**解决跨文件符号；`stdio.h` 不是把全部 I/O 代码复制进来，而是提供接口声明，库实现由链接阶段连接。
- 本章不讨论“机器码每条指令怎样执行”；那属于计算机组成。这里只建立文件和进程的可观察边界。

## 故意失败：把警告当错误隐藏

```c
int main(void) {
    int score = 10;
    score = "ten";  // 类型不匹配
    return score;
}
```

用 `-Wall -Wextra -pedantic` 编译。编译器会拒绝或警告，因为字符串字面量不是 `int`。不要通过强制转换压掉警告：警告经常是“状态模型已经不可信”的最早证据。游戏中同类错误是把资源句柄、实体 ID 或浮点速度塞进错误字段。

## 验证与游戏映射

把 `return 0` 改成 `return 7`，观察 shell 的 `exit=7`；再把输出重定向到文件，确认 stdout 是进程输出而不是“屏幕魔法”。构建脚本、CI 和引擎打包都依赖同一件事：输入、命令、产物和退出码必须可观察。下一章将回答：这些值由什么类型保存，类型如何影响存储和解释？

> 参考：[ISO C11 草案 N1570 §5.1.1.2、§5.1.2.2.1](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)、[GCC Warning Options](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html)。
