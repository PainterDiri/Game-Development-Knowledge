# 课程知识集目录契约

`knowledge-sets/<course-slug>/` 是可公开分享的课程源文件。阅读进度由网站在浏览器本地自动保存，课程目录不包含任何个人状态或作业。

```text
knowledge-sets/<course-slug>/
├── README.md
├── lessons/
│   └── 00-course-map.md
├── labs/
│   ├── README.md              # 实验题面、起始材料、验收标准
│   └── solutions.md           # 折叠提示、参考路线、验证与故障解析
├── assessments/
│   ├── questions.md
│   ├── answers.md
│   └── rubric.md
├── code/                      # 可公开复用的参考代码
├── notes/
│   └── glossary.md
├── references/
│   ├── research-notes.md
│   └── bibliography.md
└── assets/
```

## 文件职责

- `README.md`：课程定位、前置、出口能力、学习顺序、与游戏开发/主实践的关系。
- `lessons/`：公开知识正文；文件名用两位数字前缀保证阅读顺序。
- `labs/README.md`：实验题面、输入、预期输出、验收标准、故意失败和缩减版。
- `labs/solutions.md`：折叠提示、参考实现路线、验证方法、常见失败与替代方案；不能只给最终代码。
- `assessments/questions.md`：少而精的公开题目，题目 ID 稳定且唯一。
- `assessments/answers.md`：与题目 ID 对应的最小提示、答案、推理和常见误区，使用 `<details>` 折叠。
- `assessments/rubric.md`：帮助快速判断回答是否覆盖机制、边界和验证。
- `code/`：公开参考代码和构建配置；禁止提交缓存、编译产物和密钥。
- `notes/glossary.md`：公开术语中英对照和定义，不是个人笔记本。
- `references/`：来源、版本、访问日期和使用范围。

个人实践代码可放在任意位置。若在本仓库中工作，按需使用被 Git 忽略的 `.practice/<course-slug>/`，不要预生成空目录或强制撰写学习日志。
