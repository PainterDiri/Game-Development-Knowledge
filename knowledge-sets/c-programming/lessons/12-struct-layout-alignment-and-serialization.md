# 12. 结构体、布局与对齐：逻辑字段不等于字节协议

动态内存只解决“活多久”，结构体解决“这组字段如何共同表示一个状态”。游戏中的敌人、输入帧、掉落物都适合结构体，但直接把结构体写进文件或网络包是一个跨编译器、跨平台风险。

## 结构体和不变量

```c
#include <stddef.h>
#include <stdio.h>

typedef struct {
    float x;
    float y;
    int health;
} EnemyState;

int main(void) {
    printf("size=%zu x=%zu y=%zu health=%zu\n",
           sizeof(EnemyState), offsetof(EnemyState, x),
           offsetof(EnemyState, y), offsetof(EnemyState, health));
}
```

字段按声明顺序排列，但编译器可能在字段间插入 padding 以满足对齐要求；`sizeof(EnemyState)` 可能大于三个字段尺寸之和。`offsetof` 能测量当前实现的布局，不能把它变成跨平台协议保证。

## 为什么不直接 `fwrite(&state, sizeof state, 1, file)`？

因为可能存在：字节序、字段 padding、`int/float` 表示差异、版本变更、未初始化 padding 泄漏、编译器/平台布局不同。持久化应显式写字段，带 magic、版本、长度和校验；网络协议也应显式序列化。

## 字段顺序取舍

把高频一起读取的字段放在一起可能改善缓存；把 `bool`/小字段堆在一起可能减少尺寸，但会增加可读性和 ABI 风险。先测 `sizeof`、基准和实际内存，再优化；不要为几个字节牺牲稳定协议。

## 验证与游戏映射

写一个 `EnemyState` 的显式序列化函数，测试版本号不匹配时拒绝读取；比较字段重排前后的 `sizeof`。Unity 序列化、UE 反射和资产格式都比裸 `fwrite` 更有版本层，但 Native Plugin 仍必须明确结构体按值/按指针传递、对齐和调用约定。下一章把离散状态和紧凑标志编码为枚举、联合与位掩码。

> 参考：[N1570 §6.7.2.1 结构体和联合](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)。
