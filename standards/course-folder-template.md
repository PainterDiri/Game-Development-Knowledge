# 文件职责与可变结构

文件夹用于让人和工具快速找到内容，**不是规定每门课程必须长得一样**。

## 最小骨架

课程处于 `planned/scaffolded` 时，只需要：

```text
knowledge-sets/<slug>/
├── README.md
├── lessons/
│   └── 00-course-map.md
└── references/
    └── research-notes.md
```

不要预填十几个“待填写”页面，也不要用 `.gitkeep` 维持空目录。研究和课程地图确定结构后，再创建真正需要的章节、题目、实践、代码或资源目录。

## 完整课程常见职责

```text
knowledge-sets/<slug>/
├── README.md
├── lessons/
│   ├── 00-course-map.md
│   └── ...                      # 按课程问题自由组织
├── labs/
│   ├── README.md                # 实践题面与验收
│   └── solutions.md             # 折叠提示与参考路线
├── assessments/
│   ├── questions.md
│   ├── answers.md
│   └── rubric.md                # 需要多维评价时使用
├── code/                        # 可运行参考实现
├── notes/
│   └── glossary.md              # 术语较多时使用
├── references/
│   ├── research-notes.md
│   └── bibliography.md
└── assets/
```

### 稳定职责

- `README.md`：课程问题、前置、出口、推荐路径、环境和实践入口；
- `00-course-map.md`：章节为什么这样安排、难点、依赖和验证方式；
- `lessons/`：文件名按阅读顺序编号，但章节结构由课程决定；
- `labs/README.md` / `solutions.md`：题面与解法分开，解法默认折叠；
- `questions.md` / `answers.md`：题目 ID 一一对应；
- `rubric.md`：只在快速自评或开放题确有价值时保留，内容按课程定制；
- `glossary.md`：只收录会反复使用或容易混淆的术语；
- `references/`：记录来源、版本、日期、用途和限制。

课程可以增加 `simulator/`、`benchmarks/`、`unity/`、`unreal/`、`server/` 等目录，也可以把很短的内容合并。改变结构时，在课程地图说明原因即可。

个人练习不进入公开课程目录；若放在本仓库，按需使用被忽略的 `.practice/<slug>/`。
