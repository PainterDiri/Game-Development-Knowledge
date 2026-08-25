# 主实践：固定容量房间/波次运行时组件库

## 目标与边界

你要实现一个不依赖 Unity/UE 的 C17 组件，模拟肉鸽房间运行时中的一小段规则：给定 `seed` 和波次数量，生成固定容量的敌人快照；调用者可以读取快照、计算诊断摘要，并在容量不足或参数非法时得到明确错误。

这不是“做一个游戏”，也不是追求最短代码。验收关注：对象生命周期、数组边界、所有权、失败原子性、确定性和可观测证据。

## 最小版本

```text
c-programming-practice/
├── include/rg_runtime.h
├── rg_runtime.c
├── test_runtime.c
└── Makefile
```

只需要 C17 编译器；不得引入第三方库。可以从 `code/runtime-kit/` 复制参考基线到自己的 `.practice/c-programming/`，但先阅读题面再对照。

## 分阶段题面

### 阶段 A：值与数据布局

定义 `RgVec2`、`RgEnemy`、`RgRuntime`。至少包含位置、生命值、旗标、有效元素数、容量和 RNG 状态。写出每个字段的单位、允许范围、所有者和生命周期；不要把动态数组指针留在结构体里而不说明释放者。

### 阶段 B：确定性和状态转换

实现 `rg_runtime_init(runtime, seed)` 和 `rg_runtime_spawn_wave(runtime, count)`。同一个 seed 和同一调用序列必须产生相同快照；不同 seed 的输出应在测试中有可观察差异。容量检查必须先于任何写入，失败后 `enemy_count`、已有敌人和 RNG 状态都不应改变。

### 阶段 C：读取与错误路径

实现只读查询 API，例如 `rg_runtime_get_enemy(runtime, index, out_enemy)`。对 `NULL`、空运行时、越界索引、容量不足给出错误码；失败时输出参数不能留下“半个新结果”。

### 阶段 D：证据和工程边界

写至少 5 个测试：正常生成、空波次、容量边界、失败原子性、同 seed 重现、不同 seed 差异、越界查询中选 5 个以上。为至少一个故意 bug 保留 Sanitizer 复现命令和修复后的回归测试。

## 最小提示

<details><summary>提示 1：先写状态不变量</summary>

核心不变量可以是 `0 <= enemy_count <= RG_RUNTIME_MAX_ENEMIES`。所有写入位置都应是 `enemies[enemy_count + i]` 且先证明 `enemy_count + count <= capacity`。失败路径不要先增加 `enemy_count` 再回滚。
</details>

<details><summary>提示 2：不要用全局随机状态</summary>

把 RNG 状态放在 `RgRuntime` 中，`init` 设置 seed，生成函数只通过 `runtime` 消费状态。这样两个实例可以并行测试，改变 `runId` 也不会改变规则结果。
</details>

<details><summary>提示 3：查询 API 的返回值和输出参数分工</summary>

返回值表示成功/哪一种失败；`out_enemy` 只在成功时写入。调用者拥有输出对象，不需要释放库内部内存。
</details>

## 参考路线

1. 先让 `make test` 编译一个空的 `main`，确认工具链而不是代码逻辑出了问题；
2. 先实现 `init`、计数查询和一个固定敌人，再加入 RNG；
3. 用固定 seed 打印一份 checksum，随后把打印改为断言；
4. 用容量恰好填满、再请求 1 个的测试证明失败原子性；
5. 加入 `NULL`/越界测试和 Sanitizer；
6. 最后才考虑导出符号、结构体布局和引擎适配，不要先写 Unity/UE 代码。

## 验收方法

在干净目录运行：

```bash
make clean test
make asan
```

通过标准：

- 编译无 `-Wall -Wextra -Wconversion -Wshadow -pedantic` 警告；
- 普通测试输出明确的通过信息；
- Sanitizer 运行无报告；
- 相同 seed 的 checksum/快照一致，不同 seed 有差异；
- 容量不足、参数为空、索引越界都走可判断的错误路径；
- 失败调用不修改已有状态；
- README 写清运行命令、字段单位、所有权和已知限制；
- `git diff --check` 通过，代码没有机器私有路径、缓存或密钥。

## 常见失败与诊断

| 现象 | 可能原因 | 先查什么 |
|---|---|---|
| `make` 找不到头文件 | `-Iinclude` 缺失或路径错误 | 编译命令和工作目录 |
| 同 seed 结果不同 | 使用 `time()`/全局 RNG 或调用次数不同 | seed 所有者和 RNG 消费点 |
| 失败后已有敌人改变 | 先写入再做容量检查 | 失败原子性测试 |
| ASan 报 heap/stack overflow | `<=` 边界、错误容量或 `sizeof` 误用 | `[0, count)` 和函数参数退化 |
| 退出时崩溃 | 重复释放或把栈对象当堆对象释放 | 所有权表 |
| Unity/UE 接入链接失败 | C++ 名字改编、调用约定或结构体不一致 | `extern "C"`、ABI 和构建目标 |

## 两个微实验

### A：生命周期诊断（15–30 分钟）

分别制造“返回局部数组地址”和“释放后读取”的最小程序；用 `-fsanitize=address,undefined -g` 运行，记录报告中的源行、访问类型和修复方案。不要把“加一个 `printf` 后不崩”当修复。

### B：布局与标志测量（20–40 分钟）

调整 `RgEnemy` 字段顺序，打印 `sizeof`/`offsetof`；再用位标志表示三种伤害属性，测试组合、检查和清除。写一段说明：为什么内存更小不等于协议更稳定，为什么序列化需要显式版本。

## 主项目接缝

完成独立验收后，按 [integration-contract.md](integration-contract.md) 导出 `create/init → spawn → snapshot → destroy` 的最小 API。Unity/UE 适配层只能消费快照和错误码，不能把场景对象指针塞进 C 核心；任何失败都可以回滚到没有 C 组件的主项目版本。
