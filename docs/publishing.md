# 网站发布与维护

普通学习者直接访问 GitHub Pages，不需要安装 MkDocs。以下命令只面向维护者。

```bash
make install      # 首次安装
make docs-serve   # 同步内容并本地预览
make check        # 同步、仓库检查与严格构建
```

推送 `main` 后，GitHub Actions 会构建 MkDocs 并发布 `site/`。发布前必须确认：

- 自动检查和严格构建通过；
- 没有个人信息、密钥、缓存、个人练习或构建产物；
- 课程状态与实际公开内容一致；
- 引擎、库和工具版本已记录。

## 实践代码下载

`make docs-sync` 会根据已发布课程的 `practice-bundle.json` 生成 `docs/downloads/<course-slug>-code.zip` 和集中下载页。`docs/downloads/` 是构建产物，不提交到 Git；GitHub Pages 会把它随 `site/` 一起发布，因此课程首页和“实践代码下载”页面都可以直接提供下载。

下载 ZIP 只包含经过白名单审核的代码、测试、fixture、配置和接入契约。课程正文、题面、提示、答案和验收说明继续由网站页面承载。
