# 5. 函数、作用域与调用栈：边界如何约束状态变化

循环已经能处理一批敌人，但如果伤害规则散落在 `main`、敌人回合和测试中，修复一次规则就可能漏三处。函数不是为了“把代码变短”，而是为输入、输出、失败和状态所有权建立可测试边界。

## 5.1 参数按值传递

```c
int clamp_health(int health, int max_health) {
    if (max_health < 0 || health < 0) return 0;
    if (health > max_health) return max_health;
    return health;
}
```

调用时参数值被复制到函数的参数对象。函数修改参数不会自动改调用者对象。返回值适合表达一个主要结果；错误与多个结果以后会用错误码和输出参数。

函数契约应说明：

```text
输入：health、max_health 的允许范围和单位
输出：返回值范围
失败：max_health < 0 时怎样处理
副作用：是否修改外部状态、写日志或分配内存
```

静默“修正”非法 `max_health` 可能隐藏上游错误。教学实现可返回状态码，或用断言表达只允许内部调用满足的前置条件。

## 5.2 声明、定义与原型

```c
int clamp_health(int health, int max_health); /* 声明/原型 */
```

原型让编译器在调用点检查参数数量和类型。定义提供函数体。不要依赖隐式声明；现代 C 中它是错误。公开声明通常进入头文件，定义进入 `.c` 文件，第 6 章会解释多翻译单元。

## 5.3 调用栈与自动对象

每次调用都有自己的参数和局部自动对象：

```c
int compute_damage(int base) {
    int scaled = base * 2;
    return scaled;
}
```

返回后 `scaled` 生命周期结束，所以不能返回 `&scaled`。递归会创建多层调用帧；深度不受控会耗尽栈。遍历未知深度房间图时，显式栈/队列往往比递归更容易设容量、报告失败和复现。

## 5.4 纯计算与有副作用函数

把“计算结果”和“提交状态”分开更容易测试：

```c
int compute_damage(int attack, int armor) {
    /* 本例契约：attack 和 armor 都在 0..INT_MAX，减法结果可表示。 */
    int reduced = attack - armor;
    return reduced > 0 ? reduced : 0;
}

void apply_damage(Player *player, int damage); /* 指针模型见 5.6 与第 9 章；Player 类型是第 10 章的预览 */
```

第一函数只由输入决定，测试简单；第二函数拥有状态改变，必须维护生命值不变量。不要让低层函数偷偷读取全局随机数、当前时间或 UI，这会破坏复现和复用。

## 5.5 递归的边界

阶乘常被用来演示递归，却容易掩盖整数溢出和负输入。更有用的思考是：递归问题是否有明确基例、每次是否缩小、最大深度是否可控。游戏中的行为树、目录扫描和图遍历可能遇到环；没有 visited 集合或深度限制时，“递归写得很优雅”仍然会失败。

## 验证、失败与游戏映射

给函数写表驱动测试，覆盖正常、边界和非法输入；用调试器或打印进入/退出轨迹观察递归深度。常见失败是函数名叫 `get_damage` 却同时修改生命、播放音效和消费 RNG，使调用顺序成为隐藏规则。游戏映射：领域规则函数应独立于场景/UI，Unity 或 UE 只通过薄适配层提交结果。

## 进一步拆解与实验

## 5.6 读调用栈：参数是拷贝还是共享对象

C 的普通参数按值传递。下面的 `health` 在函数内是副本：

```c
void try_damage(int health, int damage) {
    health -= damage;
}
```

调用者的生命值不会改变。若要修改调用者对象，传入指针：

```c
bool apply_damage(int *health, int damage) {
    if (health == NULL || damage < 0 || *health < 0) return false;
    *health = damage >= *health ? 0 : *health - damage;
    return true;
}
```

调用 `apply_damage(&health, 3)` 时，参数 `health` 保存的是调用者对象的地址；函数仍然按值拷贝这个地址，但解引用后访问同一个对象。这个模型同时解释了“指针参数可以修改调用者”和“指针本身的改指向不会回写调用者”之间的区别。

用打印或调试器观察顺序。下面是**依赖前文类型/头文件的教学片段**，省略了 `main` 和完整的调用环境：

```c
static void trace(const char *name, int depth) {
    printf("enter %s depth=%d\n", name, depth);
}
```

更可靠的做法是用 `gdb` 在函数入口和返回前断点，查看参数、局部变量和 `bt` 调用栈。调试器显示的是一次执行的证据，不替代对所有路径的推理。

## 5.7 作用域遮蔽与静态局部状态

```c
int wave = 1;
void next_wave(void) {
    int wave = 99; /* 遮蔽外层名字，不会更新外层 wave */
    wave++;
}
```

同名遮蔽会让读者误判哪个对象被修改。命名清楚通常比依赖作用域规则更好。`static` 局部变量会跨调用保留值：

```c
int next_id(void) {
    static int id = 0;
    return ++id;
}
```

这个示意函数还会在 id 达到 INT_MAX 后触发有符号溢出，不能直接用于长期运行服务。生产接口需要返回成功/耗尽状态，并在递增前检查上限。进程级计数器还让测试顺序影响结果，也不能安全地替代运行时对象字段。需要确定性时，把状态显式放进 `Runtime` 并传递给函数。

## 5.8 递归的栈成本与终止证明

递归每次调用都会创建新的参数和局部对象。必须有：基准情况、朝基准情况缩小的输入，以及可接受的最大深度。房间图搜索可以递归，但深图可能耗尽栈；显式队列/栈能让内存上限和取消机制更清楚。不要把“递归更优雅”当作无条件取舍，比较可读性、深度、错误恢复和性能。

## 5.9 用两个调用帧解释递归

完整程序另存为 `countdown.c`。它不引入动态内存，本例调用输入固定为 2（独立改动时限定在 0–8）：

<!-- executable: countdown.c -->
```c
#include <stdio.h>
static void countdown(unsigned remaining) {
    printf("enter %u\n", remaining);
    if (remaining > 0u) countdown(remaining - 1u);
    printf("leave %u\n", remaining);
}
int main(void) {
    countdown(2u);
    return 0;
}
```

用 `cc -std=c17 -Wall -Wextra -Wpedantic countdown.c -o countdown && ./countdown` 运行。输出依次是 enter 2、enter 1、enter 0、leave 0、leave 1、leave 2。父调用在子调用返回前暂停，每一层 remaining 是不同对象；先到 0 再逆序返回，不是一个共享变量反复修改。基例是不再递归的 0，进度量 remaining 严格递减；只应在已控制深度的调用入口使用。不能由这六行输出推断任意深度不会耗尽栈，编译器也不保证尾调用消除。
## 5.10 按值参数与通过地址写回的对照

保存为 `functions.c`，按第 1 章开关编译运行，预期 `functions: passed`，不带 `-DNDEBUG`。纯函数 damaged_value 的前提是 health/damage 非负；apply_damage 检查该前提后才调用。hp、next 与参数副本是不同对象；把地址传进函数仍是按值复制地址，却能通过它定位同一个 hp。

<!-- executable: functions.c -->
```c
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
static int damaged_value(int health, int damage) {
    return damage >= health ? 0 : health - damage;
}
static bool apply_damage(int *health, int damage) {
    if (health == NULL || damage < 0 || *health < 0) return false;
    *health = damaged_value(*health, damage);
    return true;
}
int main(void) {
    int hp = 20;
    int next = damaged_value(hp, 3);
    assert(hp == 20 && next == 17);
    hp = next;
    assert(apply_damage(&hp, 99) && hp == 0);
    assert(!apply_damage(&hp, -1) && hp == 0);
    hp = -1;
    assert(!apply_damage(&hp, 1) && hp == -1);
    assert(!apply_damage(NULL, 1));
    puts("functions: passed");
    return 0;
}
```

## 本章练习

### C05-Q1：为什么修改参数没有生效

```c
void heal(int health) { health += 5; }
```

调用 `heal(player_health)` 后原值不变。解释机制并给出两种接口方案。

<details><summary>最小提示</summary>

参数对象保存的是值的副本。
</details>

<details><summary>讲解与验证</summary>

按值传递使 `health` 成为局部副本。可返回新值：`player_health = heal(player_health);`，或以后用 `int *` 明确允许修改调用者。返回值方案所有权清楚；指针方案适合多个结果或原地更新，但要检查空指针与别名。测试调用前后值。游戏映射：纯规则计算优先返回值，运行时状态提交才使用明确可变接口。
</details>

### C05-Q2：返回局部地址

`int *make_health(void) { int h=20; return &h; }` 为什么错误？

<details><summary>最小提示</summary>

区分名字离开作用域和对象生命周期结束。
</details>

<details><summary>讲解与验证</summary>

`h` 具有自动存储期，函数返回时对象生命周期结束，返回地址成为悬空指针，解引用是未定义行为。可直接返回 `int`，让调用者提供输出对象，或在确需长期所有权时动态分配并规定释放者。Sanitizer 可能报告栈生命周期错误，但没报告也不代表合法。游戏映射：跨帧保存临时组件或命令缓冲地址属于同类错误。
</details>

下一章把函数分到多个文件，区分声明、定义、内部/外部链接，并让 Makefile 只重建真正变化的输入。
