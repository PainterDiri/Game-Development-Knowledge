# 自测题与折叠解析

建议顺序：先心答/纸答，再展开最小提示；只有答案展开后仍说不清“为什么”，才回到对应章节运行代码。每道题都要求写出边界和验证证据。

### C-Q1：编译、链接还是运行时？

你执行：

```bash
cc -std=c17 -Wall -Wextra -pedantic main.c -o game
```

随后得到 `undefined symbol: apply_damage`。判断失败阶段、最可能原因和一个验证命令。

<details><summary>最小提示</summary>

把“声明存在”和“定义被链接”分开；先看编译命令是否包含实现文件或目标文件。
</details>

<details><summary>完整答案、推理、边界、常见错误、验证与游戏映射</summary>

这是**链接阶段**失败：`main.c` 可能包含了 `apply_damage` 的声明，所以单独编译通过，但命令没有把 `damage.c`/`damage.o` 的定义交给链接器。验证：

```bash
cc -std=c17 -Wall -Wextra -pedantic -c damage.c
cc -std=c17 -Wall -Wextra -pedantic -c main.c
cc damage.o main.o -o game
```

若这样成功，根因就是链接输入缺失；若编译 `damage.c` 失败，再处理声明/类型问题。常见错误是把链接错误归因于“函数运行时找不到”，或在头文件复制函数体而产生多重定义。游戏映射：Unity/UE 的模块、插件和平台库同样区分编译输入与链接输入；CI 要记录最终链接命令和 artifact。
</details>

### C-Q2：数组长度与边界

函数如下：

```c
void update(int values[]) {
    size_t count = sizeof values / sizeof values[0];
    for (size_t i = 0; i < count; ++i) values[i] += 1;
}
```

指出至少两个问题，并改写函数签名。

<details><summary>最小提示</summary>

数组作为参数会发生什么？空数组如何表示？
</details>

<details><summary>完整答案、推理、边界、常见错误、验证与游戏映射</summary>

参数中的 `values[]` 调整为 `int *values`，所以函数内 `sizeof values` 得到指针大小，不是调用者数组元素数；第二个问题是接口没有长度，无法判断合法访问范围。改为：

```c
void update(int *values, size_t count) {
    for (size_t i = 0; i < count; ++i) values[i] += 1;
}
```

契约还应说明 `values == NULL` 与 `count == 0` 的组合是否允许；若允许空区间，应在循环前安全返回。常见错误是用 `sizeof` 猜动态数组长度，或把 `count` 当容量。验证：测试 0、1、最大容量，并用 ASan 跑一个 `i <= count` 的故意失败版本。游戏映射：敌人批处理、顶点缓冲、输入帧和网络包都需要显式长度；`TArray`/`NativeArray` 的高层 API 也依赖相同不变量。
</details>

### C-Q3：指针参数、所有权与失败状态

设计一个函数，将一段 `int` 数组的最小值写入输出参数。要求：空输入失败，成功写入，失败不能修改输出参数；函数不拥有输入内存。

<details><summary>最小提示</summary>

返回 `bool`，输入用 `const int * + size_t`，输出用 `int *`；先在局部变量中计算。
</details>

<details><summary>完整答案、推理、边界、常见错误、验证与游戏映射</summary>

```c
#include <stdbool.h>
#include <stddef.h>

bool find_min(const int *values, size_t count, int *out_min) {
    if (!values || count == 0 || !out_min) return false;
    int result = values[0];
    for (size_t i = 1; i < count; ++i) {
        if (values[i] < result) result = values[i];
    }
    *out_min = result;
    return true;
}
```

`const` 表示函数不通过该参数修改输入；`count==0` 时不能读 `values[0]`；输出只在成功末尾写入，所以失败不留下半结果。函数不 `malloc`、不 `free`，输入和输出对象均由调用者拥有。常见错误是失败时先把 `*out_min` 设成 0，或返回局部变量地址。验证：空数组、单元素、负值、NULL 输出、输入输出别名；游戏映射：查询敌人最小血量、碰撞范围或帧统计时，API 的所有权和失败语义决定能否安全组合。
</details>

### C-Q4：动态内存与固定容量取舍

有人写：每生成一个敌人就 `malloc`，每次波次结束才统一 `free`。另一个方案是在运行时里预留 32 个 `Enemy`。比较两者，给出至少三个工程维度，并说明何时选哪一个。

<details><summary>最小提示</summary>

不要只说“malloc 慢”；考虑上限、失败、碎片、指针失效、生命周期和可预测性。
</details>

<details><summary>完整答案、推理、边界、常见错误、验证与游戏映射</summary>

逐敌人分配适合数量不确定、编辑器工具或加载阶段，但需要每个对象的创建/销毁责任，可能出现泄漏、碎片、分配失败和不稳定的延迟；若容器扩容，还可能移动对象使内部指针失效。固定容量适合实时波次：内存上限明确、失败可在写入前拒绝、帧内成本可预测，代价是容量上限和可能的空间浪费。第三个维度是数据局部性：连续数组通常更适合批量更新。

在拥有硬实体上限、追求确定性和固定帧预算的房间运行时，优先固定容量；在工具/内容导入中，动态容器更灵活，但仍要有溢出检查、RAII/清理路径或等价的所有权封装。常见错误是把固定容量当成绝对正确：容量不足仍要返回错误，不能静默覆盖。验证：基准分配次数/峰值内存，故意请求第 33 个敌人，检查状态未变；游戏映射：敌人、投射物、粒子和对象池都需要这种取舍。
</details>

### C-Q5：结构体能否直接写入存档？

判断下面代码是否适合作为跨平台、可长期迁移的存档格式，并说明原因：

```c
fwrite(&state, sizeof state, 1, file);
```

<details><summary>最小提示</summary>

看 `padding`、字节序、字段表示、版本、未初始化字节和短写。
</details>

<details><summary>完整答案、推理、边界、常见错误、验证与游戏映射</summary>

默认不适合。结构体可能有 padding；`int`/`float` 的尺寸和表示、字节序、编译器布局可能不同；新增字段会改变 `sizeof`；padding 可能包含未初始化数据；`fwrite` 返回值还必须检查，`fclose` 也可能失败。更稳妥的格式写 magic、schemaVersion、字段长度，并逐字段以约定的整数宽度/编码写入，读取时校验版本、范围和完整长度。

如果只是同一构建、短期临时缓存，直接写结构体可以是明确的性能/实现取舍，但必须把限制写入文档，不能冒充稳定存档。常见错误是认为“字段声明顺序固定”就等于“字节协议固定”。验证：改变字段顺序、编译目标或加入版本字段，比较文件；用截断和错误 magic fixture 测试拒绝。游戏映射：存档、回放、网络同步、资产缓存都需要版本化边界。
</details>

### C-Q6：用 Sanitizer 解释一个偶现崩溃

```c
int *make_value(void) {
    int value = 42;
    return &value;
}

int main(void) {
    int *p = make_value();
    return *p;
}
```

说明问题属于哪种生命周期错误，给出两个修复方向和验证证据。

<details><summary>最小提示</summary>

函数返回后，局部自动对象是否仍存在？修复可以改变所有权或改为调用者提供输出。
</details>

<details><summary>完整答案、推理、边界、常见错误、验证与游戏映射</summary>

`value` 是函数块内的自动对象，函数返回后生命周期结束；返回它的地址形成悬空指针，解引用是未定义行为。修复一：返回值而不是地址：`int make_value(void) { return 42; }`。修复二：让调用者提供输出参数：`bool make_value(int *out) { if (!out) return false; *out=42; return true; }`。若确实需要跨函数/跨帧存在，则由明确所有者动态分配并在恰好一次的销毁路径释放，但不能为了“活得久”无条件 `malloc`。

验证命令：

```bash
cc -std=c17 -Wall -Wextra -pedantic -fsanitize=address,undefined -g demo.c -o demo
./demo
```

Sanitizer 可能报告 stack-use-after-return；即使某平台没有报告，行为仍然不合法。常见错误是加 `printf` 后不崩就认为修好，或把 `static` 当成通用修复而引入全局共享状态。游戏映射：返回场景临时缓冲、保存实体裸指针、跨帧持有已销毁对象都属于同一生命周期类别。
</details>

### 综合题：从需求到可测试 C API

为“固定容量敌人波次”写一页设计说明，至少包含：状态拥有者、字段与单位、初始化/销毁、容量失败、随机 seed、查询 API、测试和 Unity/UE 接缝。

<details><summary>最小提示</summary>

先列不变量，再列每个公开函数的输入/输出/失败/所有权，最后列证据；不要从引擎类开始。
</details>

<details><summary>完整答案、推理、边界、常见错误、验证与游戏映射</summary>

一种合格方案：

- `RgRuntime` 由调用者拥有，包含固定数组、`enemy_count`、RNG 状态；不把 UI/场景指针放入其中；
- 不变量 `0 <= enemy_count <= capacity`，有效敌人都在 `[0, enemy_count)`；
- `init(runtime, seed)` 清空计数并规范化 seed；相同 seed/调用序列可重现；
- `spawn_wave(runtime, count)` 先检查剩余容量，失败返回 `RG_ERR_CAPACITY` 且不修改状态，成功后生成位置/血量；
- `get_enemy(runtime, index, out)` 检查空指针和范围，成功复制快照，调用者不释放内部内存；
- `destroy` 只在动态句柄版本需要，必须与 create 成对；固定内嵌数组版本可用显式 reset；
- 测试覆盖正常、0、恰好满容量、超容量原子性、NULL、越界、同 seed、不同 seed 和 Sanitizer；
- Unity C#/UE C++ 通过薄适配器消费标量/快照，适配器拥有句柄和引擎对象，C 核心不依赖引擎；构建记录 ABI、编译器、平台和可回滚 artifact。

边界：教学 RNG 不是密码学；浮点快照跨平台回放需要更严格的定点/序列化协议；并发调用尚未支持，若以后并发必须增加线程归属或同步契约。常见错误是让 `spawn_wave` 直接实例化 Prefab、让错误只写日志、或把 `sizeof(struct)` 当存档格式。验证以 `make test`、`make asan`、主项目冒烟和失败报告为证据。
</details>
