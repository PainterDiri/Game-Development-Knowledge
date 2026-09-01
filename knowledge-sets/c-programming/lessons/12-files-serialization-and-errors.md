# 12. 文件、序列化与错误模型：存档不是把内存倒进文件

程序退出后，运行时状态要么消失，要么被编码成外部格式。文件 I/O 可能遇到不存在、权限、短读、截断、错误版本和损坏内容。可靠的存档流程必须把“打开流”“解析字节”“验证领域规则”“提交新状态”分开。

## 12.1 文本与二进制的取舍

文本格式容易检查、调试和迁移，例如：

```text
RGSAVE 1
wave 2
player_health 17
enemy_count 1
```

二进制通常更紧凑、解析更快，但需要明确字节序、固定宽度和版本。直接 `fwrite(&state, sizeof state, 1, file)` 会把 padding、实现相关类型布局和未初始化字节一并写入，不应当冒充长期格式。短期同一编译器的缓存可以采用，但限制必须写出来。

## 12.2 文件函数的返回值

```c
FILE *file = fopen(path, "rb");
if (file == NULL) return RG_ERR_OPEN;
size_t got = fread(buffer, 1, capacity, file);
if (ferror(file)) { fclose(file); return RG_ERR_READ; }
if (fclose(file) != 0) return RG_ERR_CLOSE;
```

`fread` 返回实际读到的元素数，不等于“没有错误”；EOF 与 I/O 错误要通过 `feof`/`ferror` 区分。写入和关闭也可能失败。错误码应让调用者决定展示、重试还是回滚，而不是低层函数只打印一句日志。

## 12.3 版本化与失败原子性

读取存档先到临时 `candidate`：

```text
打开 → 解析 magic/version → 解析全部字段 → 检查范围与相互关系
→ 全部成功才把 candidate 赋给 runtime
```

若 wave 解析成功但 enemy_count 越界，真实运行时必须保持不变。未知版本不能“尽量读取”并默默丢字段；应明确拒绝或有写清楚的迁移器。保存也可以先写临时文件、刷新并原子替换，具体保证随平台而变，不能把 `rename` 当跨所有文件系统的万能事务。

## 12.4 错误分类与证据

区分用法错误、环境错误、格式错误、领域拒绝和内部不变量破坏。命令行可把错误码映射到类别，日志包含路径（必要时仓库相对路径）、schema、seed 和操作，但不泄露私密绝对路径。损坏 fixture 应可重复运行。

## 验证与游戏映射

准备正常、空文件、截断、错误 magic、未知版本、负生命和重复 ID fixture；断言失败后原状态和输出参数不变。游戏映射：存档、回放、关卡配置、mod 内容和网络消息都是“外部字节进入可信状态”的边界。

## 进一步拆解与实验

## 12.5 文件 I/O 的逐步错误检查

文件操作不是一个“读/写成功”的布尔值，至少要区分打开、读写、格式和关闭阶段。下面是**教学片段，不可独立编译**：`path`、`SaveHeader` 和 `RG_ERR_*` 是本章前文/实践中的占位定义，重点是错误分支的顺序；完整实现还要补齐这些定义并确保所有路径关闭文件。

```c
FILE *file = fopen(path, "rb");
if (file == NULL) {
    perror(path);             /* 解释 errno 对应的系统错误 */
    return RG_ERR_IO;
}

SaveHeader header;
if (fread(&header, sizeof header, 1, file) != 1) {
    if (ferror(file)) { /* 设备/权限等 I/O 错误 */ }
    if (feof(file)) {   /* 文件提前结束或截断 */ }
    fclose(file);
    return RG_ERR_FORMAT;
}
if (fclose(file) != 0) return RG_ERR_IO;
```

`fread` 返回“完整对象数”，不是字节数；文本函数如 `fgets` 还要处理换行和截断。错误码只能告诉调用者类别，诊断信息要保留路径、字段、偏移或版本，便于定位损坏来源。关闭也可能失败（例如写回缓冲区时），不能无条件忽略。

## 12.6 版本化格式的解析顺序

读取保存数据时先检查魔数（识别格式）、版本和长度，再按版本解析字段：

```text
RGSAVE 1
wave 2
player_health 17
enemy_count 3
...
```

解析器应拒绝未知版本，而不是“尽量猜”；否则未来字段变化可能被误解释为合法状态。对每个字段检查范围、重复出现、缺失和尾随垃圾。若格式允许扩展，明确未知字段是忽略还是拒绝，不能让实现细节成为隐含协议。

## 12.7 临时文件与提交式保存

为了避免程序在写存档中途崩溃留下半个文件，可写入同目录临时文件，完成并关闭后再用平台提供的原子替换方式提交。注意：原子替换保护的是目录项切换，不自动保证硬件断电时数据已持久化；关键存档还需考虑 flush/fsync、备份槽和损坏恢复。

加载同样使用 candidate。下面仍是**依赖前文类型与解析函数的片段**，不可独立编译：

```c
RgRuntime candidate = *runtime;
if (!parse_save(file, &candidate)) {
    return RG_ERR_FORMAT; /* runtime 未改变 */
}
*runtime = candidate;
return RG_OK;
```

若运行时包含指针、文件句柄或互斥锁，就不能简单浅拷贝，必须定义深拷贝/移动或按字段构造 candidate。这里的关键不是“复制结构体”本身，而是失败路径不半更新。

## 本章练习

### C12-Q1：为什么要先读 candidate

存档已解析前半部分，后半部分损坏。若直接写入运行时会发生什么？如何修复？

<details><summary>最小提示</summary>

解析状态和生效状态应该是两个对象。
</details>

<details><summary>讲解与验证</summary>

直接写入会留下半更新状态，例如 wave 已变而敌人仍是旧集合。先解析到临时 candidate，完成版本、范围和关系校验，最后一次赋值/交换提交；失败丢弃 candidate，原状态不动。用截断 fixture 比较调用前后 checksum。游戏映射：损坏存档不能把玩家运行时置于不可恢复中间态。
</details>

### C12-Q2：文本存档和结构体 fwrite 怎么选

为“同版本本地缓存”和“跨平台长期存档”分别选择方案并说明边界。

<details><summary>最小提示</summary>

比较可读性、布局稳定性、体积、迁移和错误诊断。
</details>

<details><summary>讲解与验证</summary>

同版本短期缓存可直接写固定布局，但必须绑定构建/版本并能失效；跨平台长期存档应使用带 magic/schema 的明确编码，逐字段检查宽度、字节序和范围。验证改变编译器/字段顺序或截断文件。常见错误是把“本机能读回”当格式稳定。游戏映射：玩家存档和网络协议的兼容成本远高于一次文件读写。
</details>

下一章用预处理、警告、未定义行为和 Sanitizer 解释“偶尔正确”的代码为何仍是缺陷。
