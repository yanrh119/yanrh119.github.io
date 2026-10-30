# YanrhArcheive

一个简单的中英文个人随笔站。文章由 Markdown 和同目录中的图片生成；首页按日期列出，长文自动截取到段落边界，每篇也有独立链接。

**公开仓库提醒：**这个项目将使用公开 GitHub 仓库。`draft: true` 只会让文章和图片不出现在生成的网站上；如果提交到仓库，它们仍然对所有人可见。需要保密的草稿和图片请留在仓库之外，不要提交或推送。

## 写文章

在 `content/` 下为每篇文章建立一个文件夹（名称使用小写英文字母、数字和连字符），里面放 `index.md` 和这篇文章的图片：

```text
content/
  a-summer-day/
    index.md
    photo.jpg
```

`index.md` 示例：

```markdown
---
date: 2026-10-30
title: 一个标题
draft: false
---

从这里开始写正文。标题可以不写；日期必填。

![对图片的简短描述](photo.jpg)
```

把 `draft` 写成 `true`，该文章及其图片不会进入生成的网站，但提交到公开仓库后仍会公开。模板 `content/example/index.md` 就是一篇草稿。删除 `draft` 或写 `false` 后才会显示在网站上。首页的长文自动截取，也可以在希望截断的地方单独放一行 `<!-- more -->`。

## 本地预览

安装 Python 3.9 或更新版本，在项目文件夹执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python journal.py preview
```

在浏览器打开命令行给出的地址；修改文章后重新运行预览命令。也可以用 `python journal.py build` 只生成 `dist/`。

## GitHub Pages

仓库启用 GitHub Pages 的 **GitHub Actions** 发布来源后，向 `main` 推送会自动生成并发布。`dist/` 是生成文件，无需提交。Pages 的项目地址通常为 `https://用户名.github.io/仓库名/`；`用户名.github.io` 仓库可使用根地址。`YanrhArcheive` 是站点名称；如需同名自定义域名，需要另行购买并配置。

**隐私：**GitHub Pages 网页可被任何取得网址的人访问；即使添加了禁止搜索引擎索引的提示，也不是访问控制。公开仓库中的所有文件和 Git 提交历史也可被任何人查看，包括标记为草稿的文章及图片。

