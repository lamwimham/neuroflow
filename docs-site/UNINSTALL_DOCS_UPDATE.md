# 文档网站更新完成

**更新日期**: 2026-02-18  
**更新内容**: 添加卸载指南文档

---

## 更新内容

### 1. 新增文档

- **`docs/getting-started/uninstall.md`** - 完整的卸载指南
  - 4 种卸载方法
  - 平台特定指南 (macOS/Linux/Windows)
  - 验证卸载步骤
  - 常见问题解答
  - 快速卸载脚本

### 2. 更新安装文档

- **`docs/getting-started/installation.md`** - 添加卸载章节
  - 在文档末尾添加了完整的卸载指南
  - 包含多种卸载方法
  - 平台特定说明

### 3. 更新导航

- **`mkdocs.yml`** - 添加卸载指南到导航
  ```yaml
  nav:
    - 快速开始:
      - 安装：getting-started/installation.md
      - 卸载：getting-started/uninstall.md  # 新增
      - 30 分钟快速入门：...
  ```

---

## 卸载指南内容

### 快速卸载（推荐）

```bash
pip uninstall neuroflow-sdk
```

### 完全清理

```bash
# 1. 卸载包
pip uninstall neuroflow-sdk

# 2. 清理 pip 缓存
pip cache purge

# 3. 删除安装文件
rm -rf $(python3 -c "import site; print(site.getsitepackages()[0])")/neuroflow*
```

### 平台特定

#### macOS/Linux
```bash
sudo pip uninstall neuroflow-sdk  # 系统模式
pip uninstall --user neuroflow-sdk  # 用户模式
```

#### Windows
```powershell
pip uninstall neuroflow-sdk
Remove-Item -Recurse -Force $env:APPDATA\Python\Python311\site-packages\neuroflow*
```

### 验证卸载

```bash
python3 -c "import neuroflow"
# 应该显示 ModuleNotFoundError
```

---

## 文档结构

```
docs-site/docs/getting-started/
├── installation.md    (已更新：添加卸载章节)
├── uninstall.md       (新增：完整卸载指南)
├── quickstart.md
├── first-agent.md
└── next-steps.md
```

---

## 访问路径

### 在线文档

卸载指南可通过以下路径访问：

- **直接访问**: `/getting-started/uninstall.html`
- **从导航**: 快速开始 → 卸载
- **从安装文档**: 滚动到末尾"卸载 NeuroFlow"章节

### 本地预览

```bash
cd docs-site
mkdocs serve
# 访问 http://127.0.0.1:8000/getting-started/uninstall/
```

---

## 文档特点

### 完整性

- ✅ 4 种卸载方法
- ✅ 3 大平台支持 (macOS/Linux/Windows)
- ✅ 验证步骤
- ✅ 常见问题解答
- ✅ 自动化脚本

### 易用性

- ✅ 快速卸载命令（一行命令）
- ✅ 预期输出示例
- ✅ 错误处理说明
- ✅ 快速卸载脚本

### 安全性

- ✅ 强调虚拟环境使用
- ✅ 权限处理说明
- ✅ 残留文件清理
- ✅ 验证步骤

---

## 下一步

### 待完成

1. **添加多语言支持**
   - 英文版卸载指南
   - 其他语言版本

2. **视频教程**
   - 录制卸载操作视频
   - 添加到文档中

3. **交互式卸载工具**
   - 创建 Web 版卸载向导
   - 自动检测安装位置
   - 一键卸载

---

## 测试清单

- [x] 文档创建
- [x] 导航更新
- [x] 链接检查
- [ ] 构建测试
- [ ] 部署测试
- [ ] 用户反馈收集

---

**状态**: ✅ 文档更新完成
