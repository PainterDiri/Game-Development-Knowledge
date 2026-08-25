# 4. 分支、循环与不变量：让状态变化有证据

上一章的数值边界必须被控制流正确使用：检测失败后到底返回、跳过、重试还是继续？游戏主循环、敌人扫描和房间生成都在重复执行状态转换。循环正确性的核心不是“写得像”，而是能说出每轮开始和结束时什么一定成立。

## 分支先处理错误路径

```c
int apply_damage(int health, int damage) {
    if (damage < 0) return health;      // 拒绝非法输入
    if (damage >= health) return 0;    // 先处理死亡边界
    return health - damage;
}
```

条件表达式的结果会选择一条路径；条件中不要隐藏会改变关键状态的副作用。把“拒绝输入”“死亡边界”“普通路径”分开，日志和测试都更容易定位。

## 循环不变量

统计数组中的存活敌人：

```c
size_t count_alive(const int health[], size_t count) {
    size_t alive = 0;
    for (size_t i = 0; i < count; ++i) {
        /* 循环不变量：alive 等于 [0, i) 中健康值大于 0 的元素数 */
        if (health[i] > 0) ++alive;
    }
    return alive;
}
```

每轮开始时：`0 <= i <= count`，`alive` 已准确统计前 `i` 项；执行体读取 `health[i]` 并可能增加 `alive`；迭代后 `i` 增加 1，不变量延伸到下一项；当 `i == count` 时，前缀就是全部数组，所以返回正确。这个证明同时暴露了边界：如果写成 `i <= count`，最后一次访问 `health[count]` 越过数组。

## 失败：修改循环条件却不修改状态

```c
int attempts = 0;
while (attempts < 3) {
    puts("reroll");
    /* 忘了 ++attempts：无限循环 */
}
```

循环需要三件事：初始化、保持条件、能让条件最终变假的进展量。游戏中“等待资源”“寻找可用出生点”“重试网络请求”尤其容易无限循环；应该同时设置最大尝试次数和失败返回。

## 验证与映射

为 `count_alive` 测试空数组（`count=0`）、全活、全死、交错状态；使用 `-fsanitize=address,undefined` 查越界。Unity 的 `Update`、UE 的 `Tick` 只是循环入口，不会自动证明每一帧有界；把可事件驱动的工作移出逐帧轮询，能降低成本。下一章把稳定的循环逻辑封装进函数，并观察局部变量何时存在。
