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

- `roadmap/`：学习路线、课程元数据和实践主线；
- `knowledge-sets/`：课程源文件、题目、解析、实践与参考代码；
- `standards/`：维护和 AI 生成规范，普通学习者无需优先阅读；
- `docs/`：MkDocs 页面、样式和浏览器本地续学逻辑；
- `scripts/`：课程创建、同步与检查工具；
- `.practice/`：可选的个人练习区，已被 Git 忽略。

课程内容按 `roadmap/course-index.json` 的顺序逐门生成。未生成课程只展示简洁的课程目标，不公开成套占位页。
