# 14. 文件 I/O 与错误处理：坏输入也是正常输入

内存状态最终要进入存档、日志或测试 fixture。文件不是“打开就成功”：路径不存在、权限不足、短读、损坏、版本过旧都可能发生。可靠代码把失败当成 API 的一部分。

## 写一个有版本的文本记录

```c
#include <stdio.h>
#include <stdbool.h>

bool write_score(const char *path, int score) {
    if (!path || score < 0) return false;
    FILE *file = fopen(path, "w");
    if (!file) return false;
    int written = fprintf(file, "score_v1 %d\n", score);
    int close_result = fclose(file);
    return written > 0 && close_result == 0;
}
```

每一步都检查返回值；`fclose` 也可能报告缓冲写回失败。读取时不要只检查“解析到了一个整数”，还要确认 magic、版本、范围和尾部是否符合预期。对不可信输入采取拒绝或安全默认，不要半初始化地继续运行。

## 错误模型的选择

- `bool`：调用者只关心成功/失败；
- `enum ErrorCode`：需要区分容量不足、坏输入、I/O 失败；
- 输出参数：成功时写结果，失败时保持输出不变；
- 日志：用于诊断，但不能替代调用者可判断的返回值。

不要让错误码和合法业务值重叠，例如用 `-1` 表示失败时，若合法 ID 也可能是负数，契约就不清楚。异常是 C++/C# 等语言层选择，不是 C 的默认控制流。

## 验证与游戏映射

为不存在路径、只读路径、损坏 magic、超大 score、截断文件写测试；测试应使用临时目录和固定输入，不依赖开发者机器上的个人路径。Unity 的 `Application.persistentDataPath`、UE 的 SaveGame 系统只属于适配层；领域组件应接收一个抽象的读写端口或字节缓冲区。下一章用编译器和运行时工具把内存错误缩成证据。

> 参考：[N1570 §7.21 输入/输出函数](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)。
