# 12. 文件、序列化与错误模型：读到一半不能覆盖旧存档状态

第 11 章解决内存获取失败后保留旧容器。本章把同样的提交边界放到文件入口：存档头合法，但载荷截断时，游戏必须继续保有原状态，而不是只更新了一半生命和波次。

## 本章核心机制与不变量

文件加载应被视为一个小事务，而不是一串“读到什么就写什么”的赋值：**读取原始字节 → 验证长度与 I/O 状态 → 解码版本化字段 → 检查领域范围和对象关系 → 构造完整候选状态 → 关闭/释放临时资源 → 一次提交**。任何一步失败都丢弃候选，真实运行时保持旧快照。

关键不变量是：格式错误、截断、未知版本和系统 I/O 错误都不能产生半个新状态；资源所有者在每条返回路径上明确关闭或释放；外部格式只依赖声明过的字节序、字段宽度和版本，不依赖结构体填充或宿主 ABI。写入侧还要区分“内存编码成功、库缓冲写入成功、关闭成功、平台持久化完成”这些不同证据层级。

## 12.1 流、文件位置与返回值

`FILE *` 是 C 标准库的流句柄，不是文件全部内容。`fopen(path, "rb")` 以二进制只读方式打开，NULL 表示打开失败；`"wb"` 会创建或截断已有文件，**不要直接用真实存档练习**。成功打开后由明确的所有者最终 `fclose`，关闭后不能再次访问该句柄。

`fread(buffer, element_size, count, file)` 返回读到的完整元素数。这里用 element_size=1，让返回值直接表示字节数；如果要求 8 字节却只读到 5，还要看 `ferror` 判断是否 I/O 错误，否则是提前 EOF/截断。`feof` 是一次读取已经触及末端后的状态，不是预言下一次能不能读；`while (!feof(file))` 常多处理一次无效数据。

`fwrite` 也返回写入元素数，缓冲写成功不代表数据已落盘；`fclose` 还可能在最终写回时失败。`fseek(file, 0L, SEEK_SET)` 请求把位置回到开头，返回 0 表示成功；读写混合的更新流在写后切换为读时需要相应定位/刷新规则，不能把指针回到开头当成理所当然。

## 12.2 先定义格式，再写代码

本章用极小二进制头，避免把第 8 章文本解析重复一遍。文本易手工诊断；二进制可紧凑，但并不天然更快或更安全。两者都需要版本、限长、范围和明确错误。

| 字节偏移 | 含义 | 本版允许值 |
|---|---|---|
| 0–2 | 魔数，即识别格式的固定字节 | ASCII R、G、S |
| 3 | 格式版本 | 1，其他拒绝 |
| 4–5 | 生命，无符号 16 位小端 | 0–100 |
| 6–7 | 波次，无符号 16 位小端 | 0–1000 |

magic 明确采用 ASCII 编码 0x52、0x47、0x53，代码直接写数值，避免依赖宿主执行字符集是否也是 ASCII。文件必须恰好 8 个八位字节；字节 8 之后有任何数据也拒绝。小端的意思是低 8 位先保存：258 = 2 + 1×256，所以末两字节为 2、1。`(unsigned)high << 8` 先转成无符号再位移，避免依赖 signed char 或较窄有符号提升；标准保证 unsigned 至少能表示 0–65535。本例 `_Static_assert(CHAR_BIT == 8, ...)` 在非八位字节实现上直接拒绝编译，**这是显式格式边界，不是声称所有 C 实现字节都是八位**。

这个最小格式没有敌人列表、校验和、加密或完整 RNG 状态，不能拿它恢复整场战斗。后续完整存档还需编码全部权威状态、ID 唯一性、种子与 RNG 当前状态，并约束对象间引用。

## 12.3 完整程序：解码到候选，关闭后再提交

下面保存为新临时目录中的 `save.c`。`tmpfile` 创建临时二进制更新流并在关闭时删除临时文件，因此不会覆盖个人存档。`load_and_close` 接管流，`write_save` 只借用流；函数名和注释把两个所有权契约区别开。

<!-- executable: save.c -->
```c
#include <assert.h>
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

_Static_assert(CHAR_BIT == 8, "this teaching format uses 8-bit octets");
typedef struct { unsigned health; unsigned wave; } Save;
typedef enum { SAVE_OK, SAVE_IO, SAVE_FORMAT, SAVE_DOMAIN } SaveResult;

/* Exactly 8 octets: 'R','G','S',version,healthLE16,waveLE16. */
static SaveResult decode(const unsigned char bytes[8], Save *out) {
    if (bytes[0] != 0x52u || bytes[1] != 0x47u || bytes[2] != 0x53u || bytes[3] != 1u)
        return SAVE_FORMAT;
    Save candidate = {
        (unsigned)bytes[4] | ((unsigned)bytes[5] << 8),
        (unsigned)bytes[6] | ((unsigned)bytes[7] << 8)
    };
    if (candidate.health > 100u || candidate.wave > 1000u) return SAVE_DOMAIN;
    *out = candidate;
    return SAVE_OK;
}

/* Borrows a valid writable stream; caller must also check fclose. */
static SaveResult write_save(FILE *file, Save value) {
    if (value.health > 100u || value.wave > 1000u) return SAVE_DOMAIN;
    unsigned char bytes[8] = {0x52u, 0x47u, 0x53u, 1u,
        (unsigned char)(value.health & 255u),
        (unsigned char)(value.health >> 8),
        (unsigned char)(value.wave & 255u),
        (unsigned char)(value.wave >> 8)};
    return fwrite(bytes, 1u, sizeof bytes, file) == sizeof bytes ? SAVE_OK : SAVE_IO;
}

/* Takes ownership of file (non-NULL); closes it on EVERY path.
   out points to independent live storage. Failure never modifies *out. */
static SaveResult load_and_close(FILE *file, Save *out) {
    unsigned char bytes[8];
    Save candidate = {0};
    SaveResult result;
    size_t got = fread(bytes, 1u, sizeof bytes, file);
    if (ferror(file)) result = SAVE_IO;
    else if (got != sizeof bytes) result = SAVE_FORMAT;
    else {
        int tail = fgetc(file);
        if (ferror(file)) result = SAVE_IO;
        else if (tail != EOF) result = SAVE_FORMAT;
        else result = decode(bytes, &candidate);
    }
    if (fclose(file) != 0) result = SAVE_IO;
    if (result == SAVE_OK) *out = candidate;
    return result;
}

static bool check_fixture(const unsigned char *bytes, size_t size, SaveResult expected) {
    FILE *file = tmpfile();
    if (file == NULL) return false;
    if (fwrite(bytes, 1u, size, file) != size || fseek(file, 0L, SEEK_SET) != 0) {
        (void)fclose(file); /* already failing; cleanup must not hide the failure */
        return false;
    }
    Save output = {88u, 99u};
    SaveResult actual = load_and_close(file, &output); /* file is now closed */
    assert(actual == expected);
    if (actual != SAVE_OK) assert(output.health == 88u && output.wave == 99u);
    else assert(output.health == 17u && output.wave == 258u);
    return true;
}

int main(void) {
    const unsigned char valid[9] = {0x52u,0x47u,0x53u,1u,17u,0u,2u,1u,0u};
    for (size_t length = 0u; length < 8u; ++length)
        if (!check_fixture(valid, length, SAVE_FORMAT)) return 1;
    if (!check_fixture(valid, 8u, SAVE_OK) ||
        !check_fixture(valid, 9u, SAVE_FORMAT)) return 1;
    unsigned char invalid[8];
    memcpy(invalid, valid, sizeof invalid);
    invalid[3] = 2u;
    if (!check_fixture(invalid, sizeof invalid, SAVE_FORMAT)) return 1;
    invalid[3] = 1u;
    invalid[4] = 101u;
    if (!check_fixture(invalid, sizeof invalid, SAVE_DOMAIN)) return 1;
    invalid[4] = 17u;
    invalid[6] = 255u; invalid[7] = 255u;
    if (!check_fixture(invalid, sizeof invalid, SAVE_DOMAIN)) return 1;
    invalid[0] = 0u;
    if (!check_fixture(invalid, sizeof invalid, SAVE_FORMAT)) return 1;
    FILE *file = tmpfile();
    if (file == NULL) return 1;
    Save original = {17u, 258u};
    if (write_save(file, original) != SAVE_OK || fseek(file, 0L, SEEK_SET) != 0) {
        (void)fclose(file);
        return 1;
    }
    unsigned char encoded[8];
    if (fread(encoded, 1u, sizeof encoded, file) != sizeof encoded ||
        memcmp(encoded, valid, sizeof encoded) != 0 || fseek(file, 0L, SEEK_SET) != 0) {
        (void)fclose(file);
        return 1;
    }
    Save output = {0};
    if (load_and_close(file, &output) != SAVE_OK) return 1;
    assert(output.health == original.health && output.wave == original.wave);
    puts("save: all checks passed");
    return 0;
}
```

```bash
cc -std=c17 -Wall -Wextra -Wpedantic -Wconversion -g save.c -o save && ./save
cc -std=c17 -Wall -Wextra -Wpedantic -g -fsanitize=address,undefined save.c -o save-san && ./save-san
```

预期 `save: all checks passed`、退出 0。不带 `-DNDEBUG`。程序先用逐字节 fixture 检验长度 0–7 的所有截断、合法长度、尾随字节、未知版本、错误魔数、生命/波次超范围，再把写出字节与独立手工 fixture 比较，最后回读。不能只做 encode→decode：如果两边都错用了大端，自洽的 round-trip 会掩盖协议错误。

解码前 candidate 初始化为空；读完整、无尾部、解码及领域检查成功后，还要关闭流。**只有所有检查成功才赋给调用者输出**。检查失败时输出保持 `{88,99}`；这里按字段断言，不比较 Save 结构体填充。比较 unsigned char 编码缓冲区的 memcmp 则是比较格式定义的实际字节，含义不同。

## 12.4 错误分类与资源清理

- 打开、读写或关闭失败是环境/I/O 错误；未知版本、长度不符是格式错误；生命越界是领域错误。
- 本例若先发生格式错、随后关闭又失败，最终返回 SAVE_IO；这是明确的优先级。更完整工具可以保留主错误和清理错误两个字段。
- 已确定失败的清理分支用 `(void)fclose`，意思不是“关闭不会失败”，而是已经返回失败、不再用清理错误覆盖它。成功路径必须检查关闭结果。
- 不能用 `perror` 解释所有错误：它打印 errno 的含义，而坏版本这种领域判断不一定设置 errno。诊断应保存错误类别、字段/偏移和格式版本，不把整个私人路径或损坏存档内容上传公共日志。

本例自然执行真实文件读写及关闭，**没有稳定模拟操作系统级短写、介质故障或 fclose 失败**；这些分支要结合平台故障注入/可替换 I/O 层验证，不能从正常路径通过推出无风险。章节已把返回值和清理顺序教清，不将本地实验称为断电测试。

## 12.5 三种不同的“原子性”

1. **内存提交**：candidate 成功后才替换输出，失败不改旧状态。本例验证了它；若状态包含拥有的指针，浅拷贝会共享资源，需要深拷贝/转移设计。
2. **文件名替换**：平台支持时，在目标同目录创建唯一临时文件，写完、检查刷新和关闭，再原子替换目标。路径切换前读者看旧文件，切换后看新文件；不能靠先删旧文件再 rename 获得这种保证。
3. **断电持久性**：用户看见保存成功后，断电重启是否仍保留。`fflush` 主要把 C 缓冲交给宿主环境，不等于设备持久化。fsync 等属于平台 API，文件与目录持久化顺序、文件系统与备份恢复策略需要专门设计。

C17 的 rename 对目标已存在等情形并不提供跨平台统一替换事务。这里不提供伪装成“通用可靠保存”的三行 rename 代码。游戏存档、回放、MOD 配置与服务端消息都有输入验证边界；服务器还需身份、授权和重放保护，合法二进制格式不代表可信请求。

## 本章练习

### C12-Q1：截断存档必须原子失败

**题型**：二进制格式偏移计算与错误恢复
**作答产物**：字节偏移表；首次失败读取；加载后真实状态断言。

格式使用显式小端字段：

```text
offset  size  field
0       4     magic "RGS1"
4       1     version (=1)
5       4     player_health (u32)
9       4     enemy_count (u32)
13      4*N   enemy_health[N] (u32 each)
```

文件只有 11 字节：完整 magic、version、player_health，再加 `enemy_count` 的前 2 字节。加载前真实运行时为 `player_health=17, enemy_count=2`。回答：

1. 哪个字段在什么偏移首次读取失败；
2. 为什么“前面字段都读成功就立即写入真实运行时”会留下什么半状态；
3. 写出候选对象加载流程和至少 5 个拒绝条件；
4. 失败后真实运行时应满足哪些断言。

<details><summary>讲解、判定与验证</summary>

magic 覆盖 0–3，version 在 4，player_health 覆盖 5–8，均完整；enemy_count 需要偏移 9–12 的 4 字节，但文件只有 9–10 两字节，因此首次失败发生在读取 enemy_count。不能把短读的缓冲剩余字节当 0，也不能继续依据伪 count 分配。

若边读边写，真实 `player_health` 可能已被文件值覆盖，但 enemy_count/敌人仍是旧状态，形成从未存在过的混合快照。安全流程：初始化局部 `candidate`；精确读取并验证 magic/version；解码固定宽度整数；验证 health 领域范围；读取完整 count；检查 count 上限以及 `13 + 4*N` 的溢出/文件长度；逐项读取并验证 enemy health；根据格式策略拒绝意外尾随数据或明确允许扩展；只有全部成功才 `runtime = candidate` 或通过提交函数交换状态。

至少拒绝：坏 magic、未知 version、任一字段短读、count 超容量、长度计算溢出、元素越界、意外尾随/校验失败。失败后断言返回错误；真实 `player_health==17`、`enemy_count==2`，所有原敌人逐字段不变；没有泄漏或半初始化资源；输入流错误被区分为 EOF/格式/系统 I/O（在 API 能表达时）。评分点：偏移定位精确；候选对象与最后提交；验证顺序在分配/循环前证明范围。常见错误是用 `fread(&struct, sizeof struct,1,fp)` 依赖填充、字节序和 ABI。游戏映射：存档、回放与网络快照都必须拒绝截断数据而不污染当前世界状态。
</details>

### C12-Q2：两种测试为何不能互相替代

**题型**：测试设计与证据比较
**作答产物**：两组不能互相替代的测试、各自断言和证据边界。

写出和读取函数都错误使用大端，encode→decode 的波次 258 测试通过。请写出本协议的末两字节，再设计能抓住该缺陷的判定。

<details><summary>讲解、判定与验证</summary>

协议规定低字节先写，应是 2、1；大端错误会写 1、2。用独立手算 fixture 比较实际编码，再用 fixture 作为输入断言波次为 258。往返测试证明两函数在样例上互相兼容，不证明它们遵守外部格式。网络客户端与服务器实现若同抄错算法，也会与其他版本不兼容；常见错误是把自洽误当标准符合性。
</details>

### C12-Q3：写出成功等于保存成功吗

**题型**：持久化边界与故障分析
**作答产物**：成功层级表、故障场景和能/不能保证的结论。

fwrite 返回完整长度，但 fclose 返回非零；另一种情况是关闭成功后断电。分别能宣布什么，不能宣布什么？

<details><summary>讲解、判定与验证</summary>

第一种必须报告 I/O 失败，不能向玩家显示可靠保存完成，因为缓冲写回可能失败。第二种只能确认库调用成功，不能由 C 标准 I/O 推出断电持久性，需要平台持久化协议与恢复测试。候选内存未修改、文件名原子替换和数据持久化是三件事。可先用正常临时文件验证编码和错误传播顺序，不伪称完成了断电演练。
</details>

## 来源与适用范围

核对日期：2026-09-07。课程仍按 C17 编译；以下 N1570 是 C11 草案，仅用于核对共通条款，不冒称已读取本轮未能解密的 N2176 PDF。[WG14 C11 草案 N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)：7.21.4（rename/tmpfile）、7.21.5（打开、关闭和刷新）、7.21.8（块 I/O）、7.21.9–10（定位和错误指示器）。只核对上述语言/库契约，不把平台持久化推断当作 C 标准承诺。

下一章用预处理输出、诊断器与调试器找到第一次破坏这些边界的位置。
