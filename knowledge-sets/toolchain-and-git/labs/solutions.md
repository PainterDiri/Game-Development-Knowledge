# 实践提示、路线与失败诊断

## 最小提示

先不要加引擎。先运行现有测试，确认 `generate_room` 的输入、输出和不变量；再检查 `build.py` 是否清理输出、排序输入、计算哈希和写 manifest。

## 推荐拆解顺序

1. 运行测试，记录基线；
2. 只阅读 `src/game.py`，画出 seed → room → checksum 的数据流；
3. 运行一次构建，检查 `dist/` 内容；
4. 删除 `dist/` 后重建，比较两个目录；
5. 改 seed 和 version，各只改一个输入；
6. 用 `git status --ignored` 与 `git check-ignore -v` 验证生成目录边界；
7. 最后制造 seed 回归并保留测试。

## 验收命令

```bash
cd knowledge-sets/toolchain-and-git/code/repro-game
python3 -m unittest discover -s tests -v
rm -rf dist /tmp/repro-first /tmp/repro-second
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-first
python3 src/build.py --output dist --seed 42 --version 1.0.0
cp -R dist /tmp/repro-second
diff -ru /tmp/repro-first /tmp/repro-second
python3 dist/game.py --seed 42
git check-ignore -v dist/game.py
```

预期：测试通过，差异命令无输出，产物启动并打印稳定 checksum，忽略规则命中。

## 参考路线

参考实现保留了几个有意的教学点：

- `random.Random(derived_seed)` 避免共享全局随机状态；
- `build.py` 在写输出前删除旧目录；
- manifest 使用排序 JSON、相对输入路径和源文件哈希；
- 测试验证性质，不硬编码全部房间文本；
- 失败通过非零退出码暴露，而不是只打印 warning。

参考实现不是唯一答案。可以用 Make、PowerShell、CMake 或其他语言重写，只要输入、输出、失败码和证据边界相同。

## 常见失败

<details>
<summary>两次 manifest 不同</summary>

查当前时间、绝对路径、无序遍历、随机构建 ID。把确定性字段与 provenance 分开，路径归一化，列表排序；不要通过“忽略所有差异”掩盖问题。
</details>

<details>
<summary>删掉 dist 后测试仍通过，但产物不能运行</summary>

测试只验证源码，没有产物冒烟。构建后运行 `python3 dist/game.py --seed 42`，并把退出码纳入验收。
</details>

<details>
<summary>改 seed 后源码哈希也变化</summary>

构建脚本把生成结果写回 `src/`。随机输出应进入临时目录或产物目录，不能污染源。
</details>

<details>
<summary>Windows 与 Unix 结果不同</summary>

检查路径分隔符、大小写、编码和 shell 语法；Python 代码优先用 `pathlib`，manifest 使用稳定的 UTF-8 和相对路径。
</details>

<details>
<summary>bisect 结果不稳定</summary>

测试依赖时间、网络、脏工作树或未固定 seed。让测试只写临时目录、固定输入，并确保每一步退出码可判定。
</details>

## 迁移到主项目

- Unity：把 manifest 思路迁移到 Editor 构建脚本，把 seed/内容版本写入开发构建 HUD 和日志，保留 `Library/` 为缓存；
- UE：把入口迁移到 Automation/BuildGraph/项目脚本，把引擎、目标平台、配置和插件列入 manifest，保留 `DerivedDataCache/` 为缓存；
- 专业项目：将 manifest 与符号、测试报告、资产版本和构建服务 ID 关联，回滚直接复用已验证 artifact。
