# 实践代码下载

## 先区分网站内容与下载内容

网站是完整学习环境，负责提供：

- 课程地图、正文、术语、推导、示例和来源；
- 实践题面、环境要求、分阶段任务、最小提示、完整解法、验收与失败诊断；
- 练习题、折叠答案、游戏映射和主项目接缝说明。

下载包是降低复制和运行成本的代码交付物，负责提供：

- 可运行的起始代码或参考代码；
- 测试、fixture、配置、构建入口和必要的许可证/来源文件；
- 接入 `RogueSlice` 的稳定契约、schema 或适配器边界。

因此，**不要把网页正文、题面和折叠答案默认复制进 ZIP**。学习者应在网站上学习，再下载代码进行运行、修改、对照和接入。

## 网站下载入口

已发布且带有 `practice-bundle.json` 的 `completed` 课程，会在两个位置显示入口：

1. 课程首页的“下载实践代码”；
2. 网站导航中的“实践代码下载”总页。

下载文件名使用 `<course-slug>-code.zip`，而不是含义模糊的 `practice.zip`。这样学习者能直接判断它是代码/资料下载，不会误以为包含整套网页课程。

尚未完成的课程不会生成空 ZIP 或虚假的参考实现。课程完成后，维护者才把经过审查、可复现的代码加入白名单并发布下载入口。

## ZIP 目录约定

典型代码包如下：

```text
<course>-code/
├── README.md                  # 下载包专用运行说明，不替代网站课程页
├── manifest.json              # 下载类型、版本和源文件白名单
├── starter/                   # 起始代码（若课程提供）
├── reference/                 # 参考实现（若课程提供）
├── code/                      # 不需要区分起始/参考时的公开代码
├── fixtures/                  # 测试输入、数据样本或固定故障样本
├── contracts/                 # 主项目接缝、schema、适配器说明
├── materials/                 # 少量运行所需配置或辅助资料
└── licenses/                  # 第三方/素材许可证（若需要）
```

当前课程如果只有参考基线，必须在包内 README 和课程页面明确写 `reference-code`，不能把参考实现伪装成未完成的 starter。后续课程能够拆分时，优先同时提供 `starter/` 与 `reference/`，让学习者可以先独立完成再对照。

没有独立代码价值的课程也可以提供 CSV/JSON fixture、Python/C 实验、图表脚本、测试输入或参考输出；但不能为了“每门课都有 ZIP”而强行塞入 Unity 工程。

## 清单与角色

课程目录中的 `practice-bundle.json` 是**下载清单**，schema 2 的最小结构为：

```json
{
  "schema": 2,
  "downloadType": "practice-code",
  "slug": "course-slug",
  "bundleName": "course-slug-code",
  "include": [
    {"path": "code/example", "role": "reference-code"},
    {"path": "integration-contract.md", "role": "integration-contract"}
  ]
}
```

支持的角色是：

| 角色 | ZIP 目录 | 用途 |
|---|---|---|
| `code` | `code/` | 已审查但不需要区分起始/参考的公开代码 |
| `starter-code` | `starter/` | 学习者应先修改的起始骨架 |
| `reference-code` | `reference/` | 学习后用于对照的可运行实现 |
| `test-fixture` | `fixtures/` | 固定输入、测试样本、回归样本或参考输出 |
| `integration-contract` | `contracts/` | 主项目接缝、schema、适配器和验收约束 |
| `supporting-material` | `materials/` | 运行所需的少量公开配置或辅助文件 |
| `license` | `licenses/` | 第三方代码/素材的许可证和来源 |

打包器只读取 `include` 白名单，不会因为文件位于 `code/` 就自动发布。每个输入都要说明语言/版本、运行命令、预期结果、已知限制和许可证边界。

## 本地生成与验收

在仓库根目录运行：

```bash
python3 scripts/package_practice.py \\
  --course toolchain-and-git \\
  --output /tmp/toolchain-and-git-code.zip
unzip -t /tmp/toolchain-and-git-code.zip
unzip -l /tmp/toolchain-and-git-code.zip
```

发布前先运行：

```bash
python3 scripts/sync_docs.py
python3 scripts/check_repo.py
git diff --check
.venv/bin/mkdocs build --strict --site-dir /tmp/game-dev-knowledge-mkdocs-site
```

人工检查至少包括：

- 新目录解压后可以按 README 启动，而不是依赖仓库外部文件；
- 角色准确，起始和参考没有混淆；
- 不含 `Library/`、`DerivedDataCache/`、`dist/`、构建产物、`.practice/`、日志、密钥、用户绝对路径或未审查大资产；
- 代码测试、固定 seed/故障样本和主项目冒烟命令可复现；
- 下载链接与网站页面存在，且网页正文仍然能独立完成学习，不要求先下载 ZIP。
