# 10. 结构体、枚举与位标志：把游戏状态建模而不是堆字段

当敌人同时有 ID、位置、生命、类型和多种状态时，散落的平行数组很快失去对应关系。结构体把相关字段放在一个对象中；枚举表达有限选择；位标志表达可组合属性。三者解决的问题不同。

## 10.1 结构体是不变量的载体

```c
#include <stdint.h>
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
typedef enum { KIND_NORMAL, KIND_ELITE, KIND_BOSS } EnemyKind;
```

枚举值表示一个选择，通常同一时刻只应有一种 kind。输入来自文件或网络时不能盲信整数落在枚举范围；解析后必须检查。不要把 enum 与 bit mask 混用：`kind == KIND_ELITE` 是比较，不能用 `kind & KIND_ELITE` 代替。

## 10.3 位标志表达可组合状态

```c
enum { ENEMY_ALIVE = 1u << 0, ENEMY_POISONED = 1u << 1, ENEMY_ELITE = 1u << 2 };
unsigned flags = ENEMY_ALIVE | ENEMY_ELITE;
if ((flags & ENEMY_ALIVE) != 0u) { /* 这一位已设置 */ }
flags |= ENEMY_POISONED;       /* 添加 */
flags &= ~(unsigned)ENEMY_ALIVE;         /* 清除 */
```

C17 中这些能用 int 表示的枚举常量具有 int 类型；清位时先转 unsigned 再取反，保证按无符号位掩码运算。位标志的宽度、无符号类型和保留位要定义清楚。死亡时是只清 `ALIVE`，还是同时要求 `health == 0`？选择一个权威规则，另一个作为可验证冗余，否则状态会分叉。

## 10.4 union 的边界

`union` 的成员共享存储，一次只保证最近写入的成员可按规则读取。若要保存不同变体，应同时保存 tag（判别字段）；没有 tag 就无法知道当前字节按哪种类型解释。不要用 union 绕过类型安全或直接当序列化格式。

## 验证、失败与游戏映射

打印 `sizeof` 和 `_Alignof` 观察布局，用断言检查 `health` 与 flags 一致；测试所有枚举值、未知值、组合/清除位和结构体初始化。游戏映射：敌人、道具、命令、动画状态和网络消息都需要清楚地区分互斥选择、组合属性和变体载荷。

## 进一步拆解与实验

## 10.5 结构体布局不是文件格式

非位域结构体成员地址按声明顺序递增，但编译器可能在字段之间插入 padding（填充）以满足对齐要求：

<!-- executable: layout.c -->
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
if ((flags & FLAG_ELITE) != 0u) { /* 只检查 ELITE 位，不检查 ALIVE */ }
flags &= ~(unsigned)FLAG_ALIVE;
```

`enum` 的底层表示和取值范围有实现细节；位移操作要使用无符号值并确认位宽。清除标志时不能写 `flags ^= FLAG_ALIVE`，因为异或是“翻转”：如果标志已经关闭，异或反而会打开它。清除应使用按位与 `&= ~(unsigned)FLAG_ALIVE`。

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

## 10.8 手推带标签的载荷

完整程序保存为 `value.c`，以 C17 编译运行。`data.i` 和 `data.f` 占用重叠存储；kind 是我们自行维护的规则，不是编译器自动同步的元数据。

<!-- executable: value.c -->
```c
#include <assert.h>
#include <stdio.h>
typedef enum { VALUE_INT, VALUE_FLOAT } ValueKind;
typedef struct {
    ValueKind kind;
    union { int i; float f; } data;
} Value;
static int print_value(const Value *value) {
    switch (value->kind) {
    case VALUE_INT: printf("points=%d\n", value->data.i); return 1;
    case VALUE_FLOAT: printf("ratio=%.2f\n", (double)value->data.f); return 1;
    default: return 0;
    }
}
int main(void) {
    enum { FLAG_ALIVE = 1u << 0, FLAG_ELITE = 1u << 1 };
    unsigned flags = FLAG_ALIVE | FLAG_ELITE;
    assert((flags & FLAG_ELITE) != 0u);
    flags &= ~(unsigned)FLAG_ALIVE;
    assert(flags == FLAG_ELITE);
    flags &= ~(unsigned)FLAG_ALIVE; /* clearing twice is idempotent */
    assert(flags == FLAG_ELITE);
    Value unknown = {.kind = (ValueKind)99, .data = {.i = 7}};
    assert(!print_value(&unknown));
    Value points = {.kind = VALUE_INT, .data = {.i = 7}};
    Value ratio = {.kind = VALUE_FLOAT, .data = {.f = 0.5f}};
    return print_value(&points) && print_value(&ratio) ? 0 : 1;
}
```

不带 -DNDEBUG 编译；输出 `points=7` 与 `ratio=0.50`，并断言组合位、重复清除和未知标签拒绝。调用契约是非空指针且 tag 与最后写入的载荷一致；default 只能拒绝未知 tag，不能检测“合法 tag 搭配错误成员”。C 的 union 表示重解释另有语言细则，可能遇到陷阱表示，本课程不以它实现跨类型位转换。游戏配置应在解析成功时一起写入标签与载荷，不允许 UI 单独修改标签。
## 本章练习

### C10-Q1：枚举状态与可组合位标志

**题型**：位运算计算与类型建模
**作答产物**：十六进制中间结果；4 行状态表；enum/flags 选择说明。

定义：

```c
enum EnemyFlags {
    ENEMY_ALIVE   = 1u << 0, /* 0x01 */
    ENEMY_ELITE   = 1u << 1, /* 0x02 */
    ENEMY_BURNING = 1u << 2, /* 0x04 */
    ENEMY_FROZEN  = 1u << 3  /* 0x08 */
};
```

初始 `uint32_t flags = ENEMY_ALIVE | ENEMY_ELITE;`。依次执行：

```c
flags |= ENEMY_BURNING;
flags &= ~ENEMY_ALIVE;
flags ^= ENEMY_FROZEN;
flags ^= ENEMY_FROZEN;
```

每一步写出十六进制结果，并分别用表达式判断 elite/alive。再回答：敌人的 AI 阶段 `Idle/Chase/Attack/Dead` 应使用互斥 enum 还是 flags？为什么“清除 frozen”不应使用 XOR？

<details><summary>讲解、判定与验证</summary>

初始为 `0x01|0x02 = 0x03`。加入 burning 后 `0x07`；清除 alive 后 `0x06`；第一次切换 frozen 后 `0x0E`；第二次切换后回到 `0x06`。检查 elite：`(flags & ENEMY_ELITE) != 0u` 为真；检查 alive：`(flags & ENEMY_ALIVE) != 0u` 为假。不要写 `flags == ENEMY_ELITE` 来判断 elite，因为同时 burning 时总值不是 0x02。

AI 阶段一次只能处于一个主状态，宜用互斥 enum，并额外验证值域/转换；alive、elite、burning、frozen 可以组合，适合 flags。清除 frozen 应写 `flags &= ~ENEMY_FROZEN`，无论原来是否设置，结果都确定为未设置；XOR 是切换，原来未设置时反而会把它加上，不满足“清除”的后置条件。

评分点：五个状态值正确；检查表达式使用掩码非零；建模依据是互斥性而不是“哪个写法短”；区分 set/clear/toggle。边界：`~` 会在提升后的整数宽度翻转全部位，赋回无符号目标通常按位截断；项目可用明确无符号掩码并限制合法位。游戏映射：控制状态机用 enum，状态效果与碰撞层常用 flags；混淆后会制造“不可能状态”或错误清除 buff。
</details>

### C10-Q2：结构体能否直接写文件

**题型**：布局计算与序列化反例
**作答产物**：字段/对齐推演、不可移植原因和显式格式方案。

`fwrite(&enemy, sizeof enemy, 1, file)` 是否适合作为长期跨平台存档？


<details><summary>讲解、判定与验证</summary>

默认不适合稳定格式。布局、padding、字节序、字段宽度、编译器和新增字段都会改变读取含义；短写也必须检查。短期同构建缓存可以接受，但应写限制。稳定存档逐字段编码固定宽度并带 magic/schema/range 校验。用截断文件、错误版本和另一种布局测试。游戏映射：存档、回放和网络协议都要把内存布局与外部格式分开。
</details>

下一章处理可变规模数据，并把“谁分配、谁释放、何时失效”写成所有权契约。
