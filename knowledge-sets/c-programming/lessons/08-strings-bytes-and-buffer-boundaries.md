# 8. 字符串、字节与缓冲区：`\0` 也是容量的一部分

数组没有长度，字符串更容易让人忘记这一点。C 字符串是以 `\0`（数值为 0 的字节）结尾的字符序列；“看起来是文本”不等于自动安全。存档、日志、资源路径和网络包都需要明确字节数与容量。

## 长度和容量

```c
#include <stdio.h>
#include <string.h>

int main(void) {
    char name[8] = "Slime";       // 需要 6 个字节：5 个字符 + '\0'
    printf("%s length=%zu capacity=%zu\n",
           name, strlen(name), sizeof name);
}
```

`strlen` 逐字节扫描到 `\0`，因此输入必须保证终止；它不是 O(1) 的长度字段。一个 8 字节缓冲区最多放 7 个普通 ASCII 字符和终止符。UTF-8 中一个“可见字符”可能占多个字节，`strlen` 返回字节数，不是用户感知的字符数。

## 安全边界函数

```c
#include <stdbool.h>
#include <stddef.h>
#include <string.h>

bool copy_text(char *dst, size_t dst_capacity,
               const char *src) {
    if (!dst || !src || dst_capacity == 0) return false;
    size_t length = strlen(src);
    if (length + 1 > dst_capacity) return false;
    memcpy(dst, src, length + 1);
    return true;
}
```

先检查容量，再复制包含终止符的 `length + 1` 字节。函数没有静默截断：截断也许适合 UI，但不适合存档键、资产 ID 或网络协议字段；应把策略交给调用者。

## 失败：`strcpy` 和格式化输入

`strcpy` 不接收目标容量；`scanf("%s", name)` 若没有宽度限制也可能越界。`snprintf` 能报告“所需长度超过容量”，但仍需检查返回值。不要把用户文本、文件内容或网络数据当成可信输入。

## 游戏映射与验证

把 `"1234567"` 复制到 8 字节数组应成功，把 `"12345678"` 拒绝；测试空串、`NULL`、非 ASCII 字节和没有 `\0` 的字节块。Unity/UE 的字符串类管理更多元数据，但 Native Plugin 边界仍要约定编码、所有权和谁释放内存。下一章用地址传递这些缓冲区，回答“指针到底指向什么”。

> 参考：[N1570 §7.24 字符串处理](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)。
