# 13. 枚举、联合与位标志：表示选择必须匹配状态模型

结构体可以同时保存多个字段，但有些状态是“从几种模式中选一种”，另一些是“多个能力同时存在”。把这两类混在一起会导致无效状态。

## 枚举：互斥模式

```c
typedef enum {
    ENEMY_IDLE,
    ENEMY_CHASING,
    ENEMY_DEAD
} EnemyMode;
```

枚举提高可读性，但底层表示和数值范围由实现处理；不要把枚举值直接当稳定存档协议，除非显式规定并测试版本。对未知值要有 `default` 错误路径，尤其是文件/网络输入。

## 位标志：可组合能力

```c
typedef unsigned int DamageFlags;
enum {
    DAMAGE_FIRE  = 1u << 0,
    DAMAGE_POISON = 1u << 1,
    DAMAGE_CRITICAL = 1u << 2
};

bool has_flag(DamageFlags value, DamageFlags flag) {
    return (value & flag) != 0u;
}
```

位标志的不变量是每一位代表一个独立布尔事实；组合用 `|`，检查用 `&`，清除用 `& ~flag`。不要把两个不同含义塞进同一位，也不要用有符号左移制造不可移植边界。

## 联合：同一存储的不同解释

`union` 的成员共享同一块存储；它节省空间，但读取哪个成员必须由额外的 tag 说明：

```c
typedef enum { VALUE_INT, VALUE_FLOAT } ValueKind;
typedef struct {
    ValueKind kind;
    union { int integer; float real; } as;
} TaggedValue;
```

没有 `kind` 的裸 union 无法知道当前有效成员。类型双关还会涉及有效类型和别名规则，不能把 union 当成任意字节转换工具。

## 验证与游戏映射

测试互斥模式的非法值、位标志组合/清除、tag 与 union 不一致；测量 `sizeof` 并比较结构体实现。道具标签、伤害元素和 AI 感知能力常适合位标志，状态机模式适合枚举；内容数据进入运行时前应校验。下一章把这些状态保存到文件，并让 I/O 失败成为显式结果。
