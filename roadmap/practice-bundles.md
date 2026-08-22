# 实践包与下载

实践页面负责解释机制，实践包负责降低复制和运行成本。两者不是两套答案：包内的 `brief/`、`answers/`、`integration-contract/` 和代码必须与课程源文件同步生成。

## 网站下载

已发布且带有 `practice-bundle.json` 的课程，会在课程首页显示“下载实践包”。包是公开源码压缩包，不包含 Unity `Library/`、UE `DerivedDataCache/`、构建产物、个人练习、密钥或机器路径。

包内通常包含：

```text
<course>-practice/
├── README.md                  # 解压后的使用顺序和角色说明
├── manifest.json              # 包版本与源文件清单
├── brief/                     # 实践题面与运行说明
├── answers/                   # 题目解析或答案；自学后再展开
├── integration-contract/      # 接入主 RogueSlice 的稳定接缝
├── starter/                   # 起始代码（若课程提供）
├── reference/                 # 参考实现（若课程提供）
└── course/                    # 课程地图、补充说明和其他公开文件
```

如果一个老课程的代码还没有拆成“起始代码/参考实现”，包会明确标记为 `starter-and-reference`，不会假装隐藏答案。后续课程生成时优先拆分两者；没有代码的课程可以只打包题面、答案、数据和实验脚本。

## 本地生成

在仓库根目录运行：

```bash
python3 scripts/package_practice.py \\
  --course toolchain-and-git \\
  --output /tmp/toolchain-and-git-practice.zip
```

课程目录中的 `practice-bundle.json` 是唯一的打包白名单。新增文件不会自动进入包，避免把缓存、私人资料或未审查代码发布出去。打包前先运行：

```bash
python3 scripts/sync_docs.py
python3 scripts/check_repo.py
```

## 课程作者的打包规则

- `practice.md` 或拆分实践文件放入 `brief`；
- 题目和折叠解析放入 `answers`，保持题目 ID 一一对应；
- 主项目接缝必须单独有 `integration-contract.md` 或等价文档；
- 起始实现与参考实现分别使用 `starter`、`reference`；
- 不把 `dist/`、`Library/`、`Build/`、`.practice/`、日志、密钥和绝对路径列入白名单；
- 代码写清语言/版本、命令、预期结果、限制和许可证；
- 通过完整门禁后才在课程首页显示下载入口。
