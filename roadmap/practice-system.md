# 课程实践体系

> **2026-09-01 调整**：每门课程只保留一个与本课知识直接相关的主实践，不再要求逐课向同一个 RogueSlice 提交接缝。完整游戏由“Unity 肉鸽动作游戏生产”和“发行工程与毕业项目”集中推进。

## 为什么改成课程独立主实践

逐课强行接入同一 Unity 项目会产生三类问题：底层课被引擎 API 掩盖，理论课为了“接缝”制造无价值胶水，学习者还可能在同一 Git 仓库中混入大量个人修改。新的实践体系优先让每门课把自己的核心机制讲透、做实、验收清楚。

## 统一规则

1. 每门课一个主实践，正文中的短实验直接放在对应章节；
2. 实践必须和游戏开发有具体关系，但载体由知识决定：C/算法/系统可用命令行或测试，玩法/工具/资源优先 Unity，UE 课程使用独立 UE 项目；
3. 主实践包含最小版本、分阶段指导、关键代码、故意失败、验收、常见失败、清理和拓展；
4. 公开 `knowledge-sets/<slug>/code/` 是只读教材资产；个人修改进入 `.practice/<slug>/` 或仓库外；
5. 课程索引用 `practiceProject` 记录唯一主实践名称，不再维护 `practiceTrack`、`integrationMode` 和 `projectSlice`；
6. 最终游戏在专门课程中集中设计目录、系统接缝、测试、构建和发行，不让前置课程预先承担未知集成成本。

## 实践开始前的 Git 安全检查

在仓库根目录执行：

```bash
python3 scripts/init_practice.py --course c-programming
git check-ignore -v .practice/c-programming
git status --short --untracked-files=all
```

第二条必须显示 `.gitignore` 中的 `.practice/` 规则；第三条不应列出个人实践文件。学习者只编辑复制后的目录，不使用 `git add -f .practice/...`。`.gitignore` 不会保护已经被 Git 跟踪的文件，因此不要直接修改 `knowledge-sets/.../code/`。

若想在实践里练习 Git，可在 `.practice/<slug>/<project>/` 内执行 `git init`，然后用 `git rev-parse --show-toplevel` 确认自己操作的是个人小仓库而不是课程主仓库。不要在主仓库根目录执行 `git clean -fdx`，它会删除被忽略的 `.practice/`。

## 主实践与完整项目的关系

课程实践可以产出未来可迁移的代码、数据、测试或经验，但“迁移”不是本课验收条件。直到 Unity 生产课，才建立统一的动作游戏工程；毕业项目课再处理内容冻结、平台构建、商店材料和上线回滚。
