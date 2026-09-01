# 实践代码下载规则

课程网站承载完整教学：正文、章末练习、折叠讲解、实践题面、指导和验收。ZIP 只用于降低复制代码、测试、fixture 和配置的成本。

## 可以进入下载包

- 起始代码、参考实现、测试 fixture、示例数据、构建脚本和许可证；
- 代码目录自己的 README，说明版本、命令、预期结果和限制。

## 不进入下载包

- 课程网页正文和章末练习讲解；
- `.practice/`、个人进度、日志、密钥、Cookie 和机器绝对路径；
- Unity `Library/Temp/Build/Logs/UserSettings`、UE `Binaries/Intermediate/Saved/DerivedDataCache`；
- Python/Node 缓存、编译产物、平台发布包和未经审查的大型资产。

## manifest

有公开代码的课程使用 schema 2 `practice-bundle.json`，显式列出 `starter-code`、`reference-code`、`test-fixture`、`supporting-material`、`license` 等角色。下载包不再使用 `integration-contract` 角色。

参考代码必须标明“只读基线”。学习者应解压到仓库外，或使用 `scripts/init_practice.py` 复制到 `.practice/<slug>/` 后再修改。

## 验收

- ZIP 能在新目录解压；
- README 给出语言/引擎版本、运行命令和预期输出；
- 代码测试通过，缓存和生成物未被打包；
- 搜索不到私人绝对路径、秘密或个人状态；
- 网站正文仍可不下载 ZIP 独立完成学习；
- `git check-ignore` 能证明本仓库内的个人实践副本不会出现在普通 `git status` 中。
