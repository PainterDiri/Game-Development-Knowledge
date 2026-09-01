# 游戏开发究极知识包

以计算机科学培养方案为基础、以游戏开发为主线的公开知识库。长期目标是做出并发行一个范围受控的 2D 肉鸽动作游戏，同时建立可迁移到 Unity、Unreal Engine、大型客户端与在线服务的工程能力。

## 在线阅读

https://painterdiri.github.io/Game-Development-Knowledge/

网站会在当前浏览器自动保存最后阅读位置；不需要账号、进度表、作答日志或错题本。每个访问者的记录互相独立，也不会上传 GitHub。

## 维护命令

```bash
make install      # 首次安装 MkDocs
make docs-serve   # 同步并本地预览
make check        # 仓库检查与严格构建
```

## 仓库结构

- `roadmap/`：学习路线、课程元数据、课程实践体系和下载规则；
- `knowledge-sets/`：课程源文件、题目、解析、实践与参考代码；
- `standards/`：维护和 AI 生成规范，普通学习者无需优先阅读；
- `docs/`：MkDocs 页面、样式和浏览器本地续学逻辑；
- `scripts/`：课程创建、同步、检查与实践代码下载工具；
- `.practice/`：可选的个人练习区，已被 Git 忽略。

课程内容按 `roadmap/course-index.json` 的顺序逐门生成。未生成课程只展示简洁目标。每门课只有一个与本课直接相关的主实践；完整 Unity 肉鸽项目在专门课程中集中推进。有公开实践代码的课程会生成下载包，个人修改必须复制到 `.practice/` 或仓库外。

截至 **2026-09-01**，工具链与 Git、C 程序设计已经发布；其余课程仍是准备中的课程骨架。学习基础纵切片时请优先参考[知识集现状审计与优化方案](roadmap/knowledge-set-audit.md)中的核心主线、支撑课程和方向拓展分层。
