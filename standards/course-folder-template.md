# 文件职责与可变结构

课程目录用于让学习者和工具快速找到**可学习内容**，不是规定每门课必须长得一样。页面数量不是质量指标；优先合并能连续阅读、验证和实践的内容。

## 默认骨架：先少后增

`planned/scaffolded` 课程只需要定位页和维护用研究记录：

```text
knowledge-sets/<slug>/
├── README.md                    # 课程定位 + 地图 + 学习入口
└── references/
    └── research-notes.md        # 维护资料，不是主学习路径
```

不要预填 `lessons/00-course-map.md`、十几个“待填写”章节、空实验目录或 `.gitkeep`。研究后再创建真正需要的正文、实践、题目、代码和资产。

## 完成课程的推荐形态

```text
knowledge-sets/<slug>/
├── README.md                    # 首页、课程地图、前置、出口、顺序和验收
├── lessons/                     # 一个页面解决一个可验证的大问题
│   ├── 01-...md
│   └── ...
├── practice.md                  # 默认合并题面、提示、解法、验收和代码入口
├── assessments.md               # 题目 + 最小提示 + 折叠解析
├── code/                        # 可运行参考实现；按需创建
├── references/                  # 研究与审计资料，默认不放入主导航
│   ├── research-notes.md
│   └── bibliography.md
└── assets/                      # 有明确许可证和用途时才创建
```

### 文件职责

- `README.md`：**课程首页就是课程地图**。直接回答学什么、为什么这样排、先读什么、如何验收、实践和练习在哪里；不再强制单独的 `lessons/00-course-map.md`。
- `lessons/`：正文。章节结构由课程问题决定；每页应有可观察问题、机制/示例、失败边界和验证步骤，不能只有提纲或 API 清单。
- `practice.md`：默认把实践题面、环境、最小版本、参考路线、折叠提示、代码入口、验收、常见失败和 Unity/UE 迁移放在同一页。只有实践很大或多人协作确有收益时才拆 `labs/`。
- `assessments.md`：题目和答案同页。用 `<details>` 隐藏提示与解析；只保留可判定、能区分理解层次并能迁移到游戏工程的问题。
- `references/`：用于记录来源、版本、访问日期、用途、限制和不确定点，服务维护与审计，不是学习者必须逐页阅读的主路径。
- `notes/glossary.md`：非默认文件。术语首次出现时就地解释；只有大量反复混淆的术语才值得单独索引。
- `code/`：说明语言/版本、运行命令、预期结果、已知限制；不提交引擎缓存、构建输出或个人练习状态；有起始/参考两套代码时分目录维护。
- `integration-contract.md`：说明课程产物如何与 `RogueSlice` 主项目相接，包含输入/输出、状态所有者、适配器、回滚和主项目冒烟；不要求所有课程都直接改 Unity。
- `practice-bundle.json`：实践代码下载清单（schema 2）。仅在有公开代码、fixture、配置或接缝契约时创建；打包器不会自动收集未列出的文件，也不会默认把网页正文和答案放进 ZIP。

旧版 `lessons/00-course-map.md`、`labs/README.md` + `labs/solutions.md`、分离的 `assessments/questions.md` + `answers.md` 仍可兼容维护，但新课程不要为了格式而拆页。

个人实践不进入公开课程目录；若放入本仓库，按需使用被忽略的 `.practice/<slug>/`。
