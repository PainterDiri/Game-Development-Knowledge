# 主实践：C17 命令行房间战斗模拟器

## 目标

实现一个可以用文本命令驱动的小型战斗运行时：显式 seed 生成敌人波次，玩家攻击指定敌人，存活敌人执行反击，程序打印状态和 checksum。验收重点不是美术，而是 C 的状态、边界、生命周期、错误和证据。

## Git 隔离：先复制，绝不直接改教材代码

`knowledge-sets/c-programming/code/runtime-kit/` 是公开、已跟踪的只读参考。直接修改它会出现在主仓库 `git status` 中，未来可能被误提交。请在仓库根目录执行：

```bash
python3 scripts/init_practice.py --course c-programming
git check-ignore -v .practice/c-programming
git status --short --untracked-files=all
cd .practice/c-programming/runtime-kit
```

预期：`git check-ignore` 显示 `.gitignore` 中的 `.practice/` 规则；主仓库 `git status` 不列出你的练习文件。不要使用 `git add -f .practice/...` 绕过保护；不要在主仓库根目录运行 `git clean -fdx`，它会删除个人实践。重要代码请另做仓库外备份。

如果你已经误改 `knowledge-sets/.../code/`：先用 `git diff -- <path>` 检查并把文件复制到 `.practice/`；确认副本可用后，才考虑用 `git restore <path>` 恢复教材文件。`.gitignore` 不会保护已经跟踪的文件。

## 环境与最小版本

- C17 编译器：Clang 或 GCC；
- Make；
- C 程序不依赖第三方库；CLI 集成测试另需 Python 3.9+（仅标准库）；
- 规则模块：`include/rg_runtime.h` 与 `rg_runtime.c`；输入模块：`include/rg_cli.h` 与 `rg_cli.c`；入口：`arena.c`；测试：`test_runtime.c`、`test_cli.c`、`test_arena.py`；构建：`Makefile`。

先验证参考基线：

```bash
make clean && make all
make test
make asan
printf 'wave 2\nstatus\nhit 0 99\nenemy\nstatus\nquit\n' | ./arena --seed 42
```

## 先独立做，再查参考

下载包角色是 `reference-code`，不是留空的作业。先运行基线理解入口；随后在个人副本内保留测试，独立重写一个函数，再与参考比较。不要把原样运行参考代码算作已经会实现。本实践的最小版本覆盖固定数组、状态、解析和错误契约；动态内存与文件读写分别由第 11–12 章的 buffer.c、save.c 做章节验证，第 13 章另检验调试器与地址错误；它们不是第二个主实践。固定数组项目不能一并证明这些能力，save.c 也不证明断电持久性。

## 明确的规则契约

- 先调用 `rg_runtime_init`，之后由规则函数修改状态；公开结构体方便教学观察，不是任意损坏内存都能恢复的安全边界。测试中的人工字段修改仅用于指定边界 fixture。
- 单线程调用；有效指针必须指向活着的正确类型对象；输出对象不得与运行时内部状态重叠。输入校验不能证明任意非空地址有效。
- 玩家存活时 `wave 0` 成功但不改变波次、RNG 或敌人；正数量波次成功后编号加一；容量不足和 ID 空间不足均失败且不改状态。
- 死亡敌人保留在数组，占用槽位；`enemy_count` 是已创建记录数，不是存活数。这个基线最多保存 32 个敌人记录，不支持无限刷怪。
- 零伤害不改变活敌人；对已经死亡的敌人再次命中成功并返回 `defeated=true`；玩家死亡后 `wave/hit/enemy` 都拒绝，查询仍可用。
- seed 0 映射到固定非零初始状态；同版本算法、同 seed 和同命令顺序可复现。教学 RNG 的取模有偏差，不用于密码学，也不作为公平抽样的完整实现。
- checksum 只作快速诊断，不是唯一状态身份或防作弊校验。失败测试还要逐字段比较，不比较结构体填充字节。

## 分阶段指导

### 阶段 1：写出状态和不变量

用 `RgRuntime` 拥有玩家生命、波次编号、RNG 状态、固定容量敌人数组和有效计数。用 `RgEnemy` 表示 ID、位置、生命、攻击与标志。先在纸上写：

```text
0 <= enemy_count <= RG_RUNTIME_MAX_ENEMIES
有效敌人在 enemies[0, enemy_count)
health == 0 的敌人不得参与敌人阶段
失败调用不得修改既有状态或输出参数
同 seed + 同命令序列 => 同 checksum
```

关键代码：

```c
typedef struct {
    RgEnemy enemies[RG_RUNTIME_MAX_ENEMIES];
    size_t enemy_count;
    int player_health;
    uint32_t wave_index;
    uint32_t rng_state;
} RgRuntime;
```

数组由运行时对象直接拥有，因此无需逐个 `free`；容量上限是明确设计，不是假装无限。

### 阶段 2：实现确定性生成和失败原子性

`rg_runtime_spawn_wave` 先检查剩余容量，再生成。参考实现把 RNG 状态复制到局部变量，全部成功后才提交回运行时；当前循环内没有失败分支，所以所有可失败检查都在写入前完成。仅复制 RNG 不会自动保护敌人数组：未来若在生成中增加分配或资源加载失败，必须把整批候选敌人也暂存，全部成功后一次提交，否则会留下半批敌人。

至少测试：0 个、1 个、恰好填满、超过容量、相同 seed、不同 seed。不要用当前时间作为规则 seed；可以在 CLI 入口生成随机 seed，但必须打印实际值。

### 阶段 3：实现攻击、位标志和输出参数

`rg_runtime_hit_enemy(runtime, index, damage, &defeated)` 用返回值表示调用是否成功，用 `out_defeated` 返回业务结果。检查顺序应是空指针/负伤害 → 游戏结束 → 索引 → 修改敌人 → 最后写输出。失败时输出保持调用前的值。

死亡使用 `RG_ENEMY_ALIVE` 位标志；精英用另一位。练习组合、检查与清除：

```c
enemy->flags &= ~RG_ENEMY_ALIVE;
if ((enemy->flags & RG_ENEMY_ELITE) != 0u) { /* ... */ }
```

### 阶段 4：实现 CLI 输入边界

使用第 8 章的“整行读取 → 候选命令 → 领域执行”。参考 `rg_read_line` 用 `fgetc` 恢复物理行边界，`rg_parse_command` 用 `strtoumax` 检查数字和类型范围。至少支持：

```text
wave N
hit INDEX DAMAGE
enemy
status
quit
```

为过长行、负数、非法 seed、越界索引和未知命令给出明确消息。这不是进阶选项，而是最小版本的输入契约：拒绝 `wave 3x`、`statusx`、多余参数和 NUL；超长行必须丢弃到换行/EOF，不执行前缀；下一条合法命令仍可执行。

### 阶段 5：加入存档（拓展，但建议完成）

设计一个文本格式：

```text
RGSAVE 1
seed_state 123
wave 2
player_health 17
enemy_count 2
...
```

读取时先解析到临时 `RgRuntime candidate`，完整校验后再赋给真实运行时；损坏、截断或未知版本时保持原状态。这把“失败原子性”从函数扩展到存档加载。

### 阶段 6：测试与诊断

测试至少覆盖：

- spawn 成功和容量失败原子性；
- 相同 seed/命令序列 checksum 一致；
- 越界、负伤害和空指针；
- 已死亡敌人不攻击；
- 玩家生命不低于 0；
- 损坏存档拒绝且原状态不变（若实现存档）；
- Sanitizer 无报告。

故意把一个循环条件改成 `i <= enemy_count`，运行 `make asan` 观察越界报告；修复后保留一个能覆盖最后元素边界的回归测试。

## 验收

```bash
make clean && make all
make test
make asan
printf 'wave 3\nhit 0 999\nenemy\nstatus\nquit\n' | ./arena --seed 42 > run-a.txt
printf 'wave 3\nhit 0 999\nenemy\nstatus\nquit\n' | ./arena --seed 42 > run-b.txt
diff -u run-a.txt run-b.txt
```

上面的命令仍在个人副本中。回到主仓库根目录（从 `.practice/c-programming/runtime-kit` 可用 `cd ../../..`），再运行：

```bash
git check-ignore -v .practice/c-programming
git status --short --untracked-files=all
```

通过标准：编译无课程启用的警告；测试和 Sanitizer 通过；相同输入无 diff；非法输入可诊断；错误路径不半更新；主仓库状态不含个人练习。

## 常见失败

| 现象 | 原因 | 诊断与修复 |
|---|---|---|
| 第 33 个敌人写坏内存 | 写入前没证明剩余容量 | 用减法形式检查 `count > capacity - used`，ASan 验证 |
| 同 seed 结果变化 | 全局 RNG、隐式时间或失败调用消耗随机数 | RNG 放入运行时，失败前用局部副本 |
| `hit` 失败却改了 `defeated` | 过早写输出参数 | 局部计算，成功末尾再写 |
| 命令 `wave -1` 变成巨大数 | 有符号/无符号转换或解析未检查 | 使用 `strtol`，检查范围后转 `size_t` |
| 死亡敌人仍攻击 | 健康和标志不变量不同步 | 只设一个权威规则并写测试 |
| 个人代码出现在 Git 状态 | 修改了已跟踪教材文件或强制添加 `.practice` | 复制差异到 `.practice`，恢复教材文件，撤销强制 staged 项 |
| `.practice` 突然消失 | 在根目录执行了 `git clean -fdx` | 从备份恢复；以后只在明确目录清理 |

## 可选拓展

加入物品、伤害类型、回放命令日志、版本化存档或动态敌人容器。每次拓展先写状态所有者、失效规则和测试，再写代码；不要把所有功能塞进 `main` 的无限 `if` 链。
