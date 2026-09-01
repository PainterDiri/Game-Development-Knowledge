# 4. 分支、循环与不变量：代码为什么会停，而且没有越界

表达式只能算一次；游戏逻辑需要根据状态选择路径并重复更新。`if` 和 `for` 的语法很短，真正困难的是证明所有路径都满足不变量、循环会终止、数组访问保持在合法区间。

## 4.1 条件表达式读取状态

```c
if (health <= 0) {
    is_alive = false;
} else if (health < 5) {
    is_enraged = true;
}
```

条件中的 0 表示假，非 0 表示真。赋值 `=` 与比较 `==` 不同；把常量放左边不能替代警告和清晰代码。多个布尔条件要写清短路的用途：

```c
if (enemy != NULL && enemy->health > 0) { /* 安全地先检查指针 */ }
```

`&&` 保证左侧为假时不求值右侧，因此这里的顺序是安全边界的一部分。

## 4.2 循环不变量

遍历数组的经典区间是半开区间 `[0, count)`：

```c
for (size_t i = 0; i < count; ++i) {
    enemies[i].health -= 1;
}
```

循环不变量可写成：

```text
进入每次迭代前：0 <= i <= count
[0, i) 的元素已经处理
[i, count) 尚未处理
```

当 `i < count` 时访问 `enemies[i]` 合法；每次 `i++` 让未处理区间缩小；退出时 `i == count`，全部元素处理完成。这比“看起来循环了 count 次”更能发现 `<=` 越界。

## 4.3 `while` 与状态机

不知道确切次数时用 `while`，但必须指出进度量：

```c
while (player_health > 0 && alive_enemy_count > 0) {
    run_turn();
}
```

若 `run_turn` 可能既不降低玩家生命也不减少敌人，循环可能永不终止。可以把回合状态建模为枚举并给最大回合数作为诊断保险；上限不是修复逻辑错误，而是避免工具永久挂起并保存证据。

## 4.4 `break`、`continue` 与早返回

控制转移能简化代码，也可能隐藏不变量。搜索第一个活敌人时，早返回很清楚：

```c
bool find_alive(const Enemy *items, size_t count, size_t *out_index) {
    if (items == NULL || out_index == NULL) return false;
    for (size_t i = 0; i < count; ++i) {
        if (items[i].health > 0) {
            *out_index = i;
            return true;
        }
    }
    return false;
}
```

这里失败时不写输出参数。注意 `count > 0` 且 `items == NULL` 必须拒绝；若决定允许空区间 `count == 0, items == NULL`，应在 API 契约中明确。

## 4.5 故意失败与验证

把条件改成 `i <= count`，用 AddressSanitizer 运行最后一次迭代，观察越界报告；修复后保留 0、1、最大容量测试。若循环依赖随机数，还应固定 seed 和最大迭代次数，确保失败可复现。

游戏映射：敌人更新、投射物扫描、波次状态机和资源导入队列都依赖范围不变量与终止条件。常见错误是删除循环中的元素却继续递增索引，导致跳过元素；解决方案可以是反向遍历、交换删除后不递增，或把删除延迟到单独阶段。

## 进一步拆解与实验

## 4.6 循环正确性：初始化、保持、终止

分析一个循环至少回答三件事：

1. **初始化**：第一次进入循环前，不变量是否成立？
2. **保持**：每次迭代执行后，不变量是否仍成立？
3. **终止**：循环变量是否朝终止条件前进，并且不会溢出或卡住？

搜索数组的典型不变量是“已经检查过 `[0, i)`，目标若存在且未返回，只可能在 `[i, count)`”：

```c
size_t find_enemy(const int *ids, size_t count, int wanted) {
    for (size_t i = 0; i < count; ++i) {
        if (ids[i] == wanted) return i;
    }
    return count; /* sentinel：未找到 */
}
```

`i < count` 让访问范围是 `[0, count)`；当 `count == 0` 时循环一次也不执行，仍然安全。若把条件改成 `i <= count`，最后一次会访问 `ids[count]`，这正是数组末端之外的元素。

## 4.7 `break`、`continue` 与状态机的取舍

`break` 提前结束当前循环，`continue` 跳过本次剩余循环体；它们不是错误，但会增加“哪些状态更新一定执行”的证明成本。在战斗命令处理里，与其把多个 `break` 藏在深层条件中，不如显式写状态机。下面是**依赖前文的伪代码片段**：`read_command` 和 `resolve_turn` 代表尚未展开的领域函数，因此复制后不能单独链接；重点是观察状态转移，而不是直接构建它。

```c
typedef enum { INPUT, RESOLVE, GAME_OVER } Phase;
Phase phase = INPUT;
while (phase != GAME_OVER) {
    switch (phase) {
    case INPUT:  phase = read_command() ? RESOLVE : GAME_OVER; break;
    case RESOLVE: resolve_turn(); phase = INPUT; break;
    case GAME_OVER: break;
    }
}
```

状态机的重点不是 `switch` 语法，而是有限状态、允许的转移和每个转移的后置条件。若状态不断增加却没有表格或转移约束，代码会退化成难以测试的条件嵌套。

## 4.8 循环中的可变集合

遍历并删除元素时，删除动作会改变后续索引。安全方案有三种常见取舍：

- 从后向前删除：不影响尚未访问的较小索引；
- 交换末元素删除：O(1)，但改变顺序；
- 保留 tombstone/死亡标志：遍历简单，但需要周期性压缩。

选择方案前先写出“顺序是否是游戏规则”的答案。敌人生成池通常不需要稳定顺序，可以交换删除；回放或 UI 排序可能需要稳定顺序。每种实现都要测空集合、单元素、最后元素和连续删除。

## 本章练习

### C04-Q1：证明一个遍历不会越界

为 `for (size_t i=0; i<count; ++i)` 写初始化、保持和终止三步证明。

<details><summary>最小提示</summary>

使用“已处理 `[0,i)`，未处理 `[i,count)`”。
</details>

<details><summary>讲解与验证</summary>

初始化时 `i=0`，已处理区间为空；若迭代前 `i<count`，则索引合法，处理后递增仍有 `i<=count`；终止时条件为假，所以 `i==count`，全部元素位于已处理区间。边界测试 count 为 0、1、容量。常见错误是把区间写成闭区间并多访问一次。游戏映射：批量组件更新与碰撞候选扫描使用同一证明。
</details>

### C04-Q2：删除时为何跳过敌人

交换删除 `items[i] = items[count-1]; --count;` 后仍执行 `++i`，会漏掉什么？给出修复。

<details><summary>最小提示</summary>

新换到 `i` 的元素还没有被检查。
</details>

<details><summary>讲解与验证</summary>

删除后末尾元素被移到当前索引，若递增就跳过它。可用 `while (i < count)`，仅在不删除时递增；或者反向遍历并确保删除策略匹配。用连续两个“应删除”元素测试。常见错误是只测稀疏删除。游戏映射：敌人、子弹和状态效果容器常用交换删除，顺序语义必须单独声明。
</details>

下一章会把重复逻辑放入函数，同时解释参数传值、局部对象和调用栈的生命周期。
