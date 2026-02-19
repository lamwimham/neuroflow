# Deploy Documentation to GitHub Pages

# 安装依赖
pip install mkdocs mkdocs-material mike

# 构建文档
cd docs-site
mkdocs build

# 部署到 gh-pages 分支
mike deploy --push main

# 或者使用 mkdocs gh-deploy
# mkdocs gh-deploy --force
