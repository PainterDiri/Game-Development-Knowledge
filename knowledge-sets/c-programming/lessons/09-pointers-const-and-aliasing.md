# 9. 指针、`const` 与别名：地址不是对象本身

字符串函数已经需要 `char *` 和 `const char *`。现在把它们拆开：对象是存放值的区域；指针对象存放一个地址值；解引用 `*p` 才是访问地址所指对象。指针本身也有生命周期、类型和可失效时机。

## 追踪一个指针

```c
#include <stdio.h>

int main(void) {
    int health = 10;
    int *mutable_view = &health;
    const int *read_only_view = &health;
    *mutable_view = 8;
    printf("health=%d read=%d\n", health, *read_only_view);
}
```

`&health` 取地址；`mutable_view` 可以通过解引用修改 `health`；`read_only_view` 承诺“通过这个视图不写”，但不表示底层对象永远不可变。四种常见写法：

- `int *p`：可改 `int`；
- `const int *p`：不能通过 `p` 改；
- `int *const p`：指针地址绑定后不能改，但可改对象；
- `const int *const p`：两者都不能通过该名字改。

## 合法区间与非法地址

对数组元素做指针加法只在同一个数组（或尾后一位）范围内有意义；尾后指针可以比较、用于计算长度，但不能解引用。`NULL` 表示没有有效对象，不是一个可以读写的“空对象”。返回局部对象地址、解引用已释放内存、把任意整数强转成指针，都是危险边界。

## 别名和 `restrict` 的取舍

两个指针可能指向同一对象，函数必须考虑这种别名：

```c
void add_in_place(int *dst, const int *src, size_t count);
```

若文档要求 `dst` 与 `src` 不重叠，才可以考虑 `restrict` 让编译器优化；一旦调用者违反承诺，行为可能未定义。优化提示不是免费性能，必须先有契约和测试。

## 验证与游戏映射

画出 `health`、`&health`、指针对象三者的区别；把 `*p` 改成 `p`，观察格式化输出的类型错误。Unity/UE 里句柄、引用、裸指针和对象指针也不是同一概念；C 只教你“地址 + 类型 + 有效期”三要素。下一章利用指针参数安全地返回多个结果，并把区间边界写进接口。

> 参考：[N1570 §6.5.3.2 地址与间接](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)、[N1570 §6.5.6 加法运算符](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)。
