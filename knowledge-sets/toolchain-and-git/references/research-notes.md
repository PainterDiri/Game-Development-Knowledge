# 工具链与 Git · 研究笔记

研究日期：2026-08-22。本文只记录进入课程正文的来源；链接用于核对原始定义与版本边界，不把搜索摘要当作证据。

## Git 的对象模型、分支与修复

- **问题**：如何解释 Git 的提交、分支、合并、重写历史和损坏检查，而不是把 Git 当成“文件同步器”？
- **来源**：[Git Book: Getting Started - Git Basics](https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository)、[Git Book: Git Branching](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell)、[git-fsck](https://git-scm.com/docs/git-fsck)、[git-bisect](https://git-scm.com/docs/git-bisect)
- **版本/日期**：Git 官方网站，访问日期：2026-08-22。
- **关键事实（用自己的话）**：仓库由对象和引用组成；分支是可移动引用，提交形成有向无环历史；`fsck` 可检查可达性/悬空对象；`bisect` 通过二分提交范围定位引入回归的提交。
- **对课程的影响**：先建立“快照 DAG + 引用”的心智模型，再讲工作流、冲突与回滚。游戏项目的资产冲突、生成目录和可复现回归都能映射到同一模型。
- **不确定性/冲突**：Git 客户端 UI 和团队分支策略会变；课程不规定唯一的 Git Flow，只规定可审查、可回滚和有证据的历史。
- **是否进入正文**：是。支撑第 2、4 课和主实践。

## Git LFS 与大文件边界

- **问题**：为什么游戏项目不能把所有二进制资产当作普通 Git 文本处理？
- **来源**：[Git LFS](https://git-lfs.com/)、[Git LFS: About Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage)
- **版本/日期**：GitHub 文档与 Git LFS 官方站点，访问日期：2026-08-22。
- **关键事实（用自己的话）**：LFS 在 Git 中保存轻量指针，把大文件内容放在单独的 LFS 存储；克隆/检出必须能访问对应对象。它不是备份系统，也不能替代资产命名、锁定、授权和备份策略。
- **对课程的影响**：把文本配置、源码、元数据和大二进制分别处理，并在验收中验证“干净克隆能拿到真实资产”。
- **不确定性/冲突**：托管服务有配额、带宽和文件大小限制；团队应把容量与恢复演练写进项目约定。
- **是否进入正文**：是。支撑第 2 课的取舍表。

## 可复现构建

- **问题**：什么才算“可复现”，以及它和“能在我电脑上跑”有什么不同？
- **来源**：[Reproducible Builds: Definition](https://reproducible-builds.org/docs/definition/)、[Reproducible Builds: Why reproducible builds are important](https://reproducible-builds.org/docs/why/)
- **版本/日期**：Reproducible Builds 官方文档，访问日期：2026-08-22。
- **关键事实（用自己的话）**：可复现构建强调在相同源代码和构建环境下得到等价输出；环境差异、时间戳、路径、随机数和未锁定依赖会破坏结果。可复现性提高审计、调试和供应链信任，但不自动保证软件正确。
- **对课程的影响**：用“输入—工具—配置—命令—输出—证据”描述构建，不把缓存命中或本地成功当作复现证明。
- **不确定性/冲突**：不同平台的可执行格式、压缩器和签名可能使字节级相同不现实；课程区分字节级相同、内容等价和行为等价。
- **是否进入正文**：是。支撑第 6、7、8、9 章。

## GitHub Actions 工作流与安全

- **问题**：如何把本地命令变成可审查的持续集成/发布流程？
- **来源**：[Workflow syntax for GitHub Actions](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions)、[Store and share data with workflow artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)、[GitHub Actions security hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
- **版本/日期**：GitHub 官方文档，访问日期：2026-08-22。
- **关键事实（用自己的话）**：工作流由事件、作业和步骤组成；缓存用于加速且可丢弃，artifact 用于保留构建结果和诊断证据；权限、第三方 action、密钥和来自不可信分支的输入都属于安全边界。
- **对课程的影响**：先让 CI 运行仓库已有命令，再按需加缓存；发布必须上传可下载产物、测试报告和构建清单，而不是只显示绿色勾。
- **不确定性/冲突**：GitHub UI、action 版本和额度会变化；正文使用工作流概念与最小 YAML，实际版本以仓库锁定值和官方文档为准。
- **是否进入正文**：是。支撑第 9 章和 GitHub Pages 验证。

## Unity 的资产元数据与命令行构建

- **问题**：为什么 Unity 项目中的 `.meta`、序列化文本和编辑器版本会影响协作与复现？
- **来源**：[Unity Manual: Asset Metadata](https://docs.unity3d.com/Manual/AssetMetadata.html)、[Unity Manual: Version control integration](https://docs.unity3d.com/Manual/VersionControlIntegration.html)、[Unity Manual: Unity Editor command line arguments](https://docs.unity3d.com/Manual/EditorCommandLineArguments.html)
- **版本/日期**：Unity 官方 Manual（当前文档站），访问日期：2026-08-22；正文使用跨版本原则，命令行参数需按项目锁定的 Unity 版本复核。
- **关键事实（用自己的话）**：Unity 资产依赖元数据标识和引用；版本控制策略需要纳入 `.meta`，并根据团队合并需求选择文本序列化/可见元数据；Editor 支持 batch/headless 参数和脚本化构建入口，但许可证、平台模块和缓存仍是外部前提。
- **对课程的影响**：把 Library 等生成缓存排除出 Git，保留 Assets/ProjectSettings/Packages 以及必要的 `.meta`，在 CI 中显式指定编辑器版本、目标平台和构建方法。
- **不确定性/冲突**：Unity 不同 LTS 版本和 Package Manager 包会改变参数/项目格式；课程不承诺跨版本无修改可构建。
- **是否进入正文**：是。支撑第 6、7、8、9 章的引擎对照。

## Unreal Engine 的源代码控制与自动化

- **问题**：Unreal 如何把项目文件、插件、派生目录和自动化测试纳入工程边界？
- **来源**：[Epic Developer Community: Source Control in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/source-control-in-unreal-engine)、[Unreal Engine Automation System](https://dev.epicgames.com/documentation/en-us/unreal-engine/automation-system-in-unreal-engine)、[Unreal Engine Command-Line Arguments](https://dev.epicgames.com/documentation/en-us/unreal-engine/command-line-arguments-in-unreal-engine)
- **版本/日期**：Epic 官方文档，访问日期：2026-08-22。
- **关键事实（用自己的话）**：UE 支持源代码控制集成和命令行参数；项目应区分可提交的配置/源码/资产与可再生的 Binaries、Intermediate、DerivedDataCache、Saved 等目录；Automation System 可作为自动化验证入口。
- **对课程的影响**：把 UE 对照写成“同一不变量在另一引擎中的实现”，而不是罗列编辑器按钮。Perforce、Git LFS 等选择应由二进制协作规模和锁定需求决定。
- **不确定性/冲突**：UE 版本、平台工具链和源码/Launcher 安装形态差异很大；示例只表达边界，不声称一条命令适合所有项目。
- **是否进入正文**：是。支撑第 6、7、8、9 章。
