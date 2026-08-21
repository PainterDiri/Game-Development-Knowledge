# 网站发布

## GitHub Pages 常驻网站

仓库包含 `.github/workflows/pages.yml`。每次向 `main` 推送后，GitHub Actions 会安装依赖、同步公开内容、运行检查、严格构建并部署到：

```text
https://painterdiri.github.io/Game-Development-Knowledge/
```

首次需要在仓库的 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。此后普通学习者只需打开网站，不需要本地服务器或桌面启动脚本。

## 自动续学

`docs/javascripts/learning-progress.js` 会在当前浏览器自动保存最后阅读的课程页面、章节和滚动位置。数据只在浏览器 `localStorage` 中：

- 不上传 GitHub；
- 不包含作答或个人信息；
- 不同访问者互不影响；
- 清除浏览器网站数据或更换设备后不会自动迁移。

## 更新网站

维护者完成内容并通过 `make check` 后推送 `main`，Pages 会自动重新部署。不得提交 `.practice/`、`.venv/`、Unity/UE 缓存或 `site/`。
