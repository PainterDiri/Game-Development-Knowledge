# 10. 结构体、枚举与位标志：把游戏状态建模而不是堆字段

当敌人同时有 ID、位置、生命、类型和多种状态时，散落的平行数组很快失去对应关系。结构体把相关字段放在一个对象中；枚举表达有限选择；位标志表达可组合属性。三者解决的问题不同。

## 10.1 结构体是不变量的载体

```c
typedef struct {
    uint32_t id;
    int health;
    int attack;
} Enemy;
```

`Enemy` 的每个实例拥有自己的字段。应写出不变量：`health >= 0`、`attack >= 0`、ID 在当前运行时唯一。构造/初始化函数或复位函数负责建立不变量，公开字段则需要调用者自律；模块封装可减少破坏入口。

结构体可能包含 padding（对齐填充），所以 `sizeof(Enemy)` 不等于字段大小简单相加。它适合作为同一构建内的内存布局，却不自动成为跨平台存档或网络协议。

## 10.2 枚举表达互斥状态

```c
typedef enum { ENEMY_NORMAL, ENEMY_ELITE, ENEMY_BOSS } EnemyKind;
```

枚举值表示一个选择，通常同一时刻只应有一种 kind。输入来自文件或网络时不能盲信整数落在枚举范围；解析后必须检查。不要把 enum 与 bit mask 混用：`kind == ENEMY_ELITE` 是比较，不能用 `kind & ENEMY_ELITE` 代替。

## 10.3 位标志表达可组合状态

```c
enum { ENEMY_ALIVE = 1u << 0, ENEMY_POISONED = 1u << 1, ENEMY_ELITE = 1u << 2 };
unsigned flags = ENEMY_ALIVE | ENEMY_ELITE;
if ((flags & ENEMY_ALIVE) != 0u) { /* 设置 */ }
flags |= ENEMY_POISONED;       /* 添加 */
flags &= ~ENEMY_ALIVE;         /* 清除 */
```

位标志的宽度、无符号类型和保留位要定义清楚。死亡时是只清 `ALIVE`，还是同时要求 `health == 0`？选择一个权威规则，另一个作为可验证冗余，否则状态会分叉。

## 10.4 union 的边界

`union` 的成员共享存储，一次只保证最近写入的成员可按规则读取。若要保存不同变体，应同时保存 tag（判别字段）；没有 tag 就无法知道当前字节按哪种类型解释。不要用 union 绕过类型安全或直接当序列化格式。

## 验证、失败与游戏映射

打印 `sizeof` 和 `_Alignof` 观察布局，用断言检查 `health` 与 flags 一致；测试所有枚举值、未知值、组合/清除位和结构体初始化。游戏映射：敌人、道具、命令、动画状态和网络消息都需要清楚地区分互斥选择、组合属性和变体载荷。

## 进一步拆解与实验

## 10.5 结构体布局不是文件格式

结构体字段通常按声明顺序排列，但编译器可能在字段之间插入 padding（填充）以满足对齐要求：

```c
#include <stddef.h>
#include <stdio.h>

typedef struct {
    char kind;
    int health;
    double x;
} Enemy;

int main(void) {
    printf("size=%zu health_offset=%zu\n",
           sizeof(Enemy), offsetof(Enemy, health));
}
```

`sizeof(Enemy)` 可能大于各字段大小之和；不同 ABI、编译器或架构也可能不同。因此直接 `fwrite(&enemy, sizeof enemy, 1, file)` 不是可移植存档格式：padding、字节序、类型宽度和指针字段都会破坏兼容性。内存布局适合运行时访问，序列化格式要逐字段编码并带版本。

## 10.6 用类型表达互斥和可组合

枚举适合“当前阶段只能是一个值”：

```c
typedef enum { ENEMY_IDLE, ENEMY_CHASING, ENEMY_DEAD } EnemyState;
```

位标志适合“多个属性可以同时存在”：

```c
enum { FLAG_ALIVE = 1u << 0, FLAG_ELITE = 1u << 1 };
unsigned flags = FLAG_ALIVE | FLAG_ELITE;
if ((flags & FLAG_ELITE) != 0u) { /* 同时拥有两项属性 */ }
flags &= ~FLAG_ALIVE;
```

`enum` 的底层表示和取值范围有实现细节；位移操作要使用无符号值并确认位宽。清除标志时不能写 `flags ^= FLAG_ALIVE`，因为异或是“翻转”：如果标志已经关闭，异或反而会打开它。清除应使用按位与 `&= ~FLAG_ALIVE`。

## 10.7 union 的读取前提

`union` 的所有成员共享同一存储，写入一个成员后只能在语言允许的规则下读取相应表示；它不会自动记录“当前激活成员”。如果需要安全变体，配套一个 tag：

```c
typedef enum { VALUE_INT, VALUE_FLOAT } ValueKind;
typedef struct {
    ValueKind kind;
    union { int i; float f; } data;
} Value;
```

不变量是 `kind` 与当前有效成员一致。单独有一个 union 而没有 tag，调用者无法知道应该读哪个成员，容易把任意位模式误当成有效值。游戏配置中“伤害是整数或百分比”可以用这种 tagged union，但序列化仍要写 kind 和具体字段。

## 本章练习

### C10-Q1：enum 还是 bit flags

“敌人种类”和“敌人同时中毒、精英、可攻击”分别应使用什么表示？

<details><summary>最小提示</summary>

前者通常互斥，后者可以同时成立。
</details>

<details><summary>讲解与验证</summary>

种类用 enum，强制或至少表达 normal/elite/boss 的单一选择；可组合属性用无符号 bit flags，通过 `|` 添加、`&` 检查、`& ~mask` 清除。验证未知值拒绝、组合值保留各位。常见错误是把 enum 数字当位掩码。游戏映射：状态效果可组合，职业/敌人 archetype 通常是主类别。
</details>

### C10-Q2：结构体能否直接写文件

`fwrite(&enemy, sizeof enemy, 1, file)` 是否适合作为长期跨平台存档？

<details><summary>最小提示</summary>

考虑 padding、字节序、类型宽度、版本和未初始化字节。
</details>

<details><summary>讲解与验证</summary>

默认不适合稳定格式。布局、padding、字节序、字段宽度、编译器和新增字段都会改变读取含义；短写也必须检查。短期同构建缓存可以接受，但应写限制。稳定存档逐字段编码固定宽度并带 magic/schema/range 校验。用截断文件、错误版本和另一种布局测试。游戏映射：存档、回放和网络协议都要把内存布局与外部格式分开。
</details>

下一章处理可变规模数据，并把“谁分配、谁释放、何时失效”写成所有权契约。
