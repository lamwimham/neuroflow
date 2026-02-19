# 卸载 NeuroFlow

本指南将帮助你完全卸载 NeuroFlow SDK 和相关组件。

## 📋 目录

- [快速卸载](#快速卸载)
- [完全清理](#完全清理)
- [平台特定指南](#平台特定指南)
- [验证卸载](#验证卸载)
- [常见问题](#常见问题)

---

## 🚀 快速卸载

### 标准卸载（推荐）

```bash
# 卸载 NeuroFlow SDK
pip uninstall neuroflow-sdk

# 或者使用 pip3
pip3 uninstall neuroflow-sdk
```

**预期输出**:
```
Found existing installation: neuroflow-sdk 0.3.0
Uninstalling neuroflow-sdk-0.3.0:
  Successfully uninstalled neuroflow-sdk-0.3.0
```

---

## 🧹 完全清理

### 方法 1: 清理所有残留

```bash
# 1. 卸载包
pip uninstall neuroflow-sdk

# 2. 清理 pip 缓存
pip cache purge

# 3. 删除安装文件
rm -rf $(python3 -c "import site; print(site.getsitepackages()[0])")/neuroflow*

# 4. 清理构建缓存
rm -rf ~/.cache/pip
```

### 方法 2: 开发模式清理

```bash
# 进入 SDK 目录
cd /path/to/NeuroFlow/sdk

# 卸载
pip uninstall neuroflow-sdk

# 清理构建文件
rm -rf build/ dist/ *.egg-info

# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 清理虚拟环境（如果有）
rm -rf venv/ .venv/
```

### 方法 3: 完全删除项目

```bash
# 删除整个项目
cd /path/to/parent/
rm -rf NeuroFlow/

# 验证删除
ls NeuroFlow  # 应该显示 "No such file or directory"
```

---

## 🖥️ 平台特定指南

### macOS

```bash
# 标准卸载
pip uninstall neuroflow-sdk

# 使用 sudo（如果以系统模式安装）
sudo pip uninstall neuroflow-sdk

# 使用用户模式
pip uninstall --user neuroflow-sdk

# 清理 Homebrew 相关
brew cleanup

# 清理用户缓存
rm -rf ~/Library/Caches/pip
rm -rf ~/Library/Python/*/lib/python/site-packages/neuroflow*
```

### Linux (Ubuntu/Debian)

```bash
# 标准卸载
pip uninstall neuroflow-sdk

# 使用 sudo
sudo pip uninstall neuroflow-sdk

# 使用用户模式
pip uninstall --user neuroflow-sdk

# 清理系统缓存
sudo rm -rf /usr/local/lib/python*/dist-packages/neuroflow*
sudo rm -rf /usr/lib/python*/dist-packages/neuroflow*

# 清理用户缓存
rm -rf ~/.cache/pip
rm -rf ~/.local/lib/python*/site-packages/neuroflow*
```

### Linux (CentOS/RHEL)

```bash
# 卸载
pip uninstall neuroflow-sdk

# 清理系统安装
sudo rm -rf /usr/lib/python*/site-packages/neuroflow*
```

### Windows

#### PowerShell

```powershell
# 标准卸载
pip uninstall neuroflow-sdk

# 以管理员身份运行
Start-Process powershell -Verb RunAs -ArgumentList "pip uninstall neuroflow-sdk"

# 使用用户模式
pip uninstall --user neuroflow-sdk

# 清理残留文件
Remove-Item -Recurse -Force $env:APPDATA\Python\Python311\site-packages\neuroflow* -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $env:LOCALAPPDATA\Programs\Python\Python311\Lib\site-packages\neuroflow* -ErrorAction SilentlyContinue
```

#### CMD

```cmd
REM 标准卸载
pip uninstall neuroflow-sdk

REM 清理残留
del /s /q %APPDATA%\Python\Python311\site-packages\neuroflow*
del /s /q %LOCALAPPDATA%\Programs\Python\Python311\Lib\site-packages\neuroflow*
```

---

## ✅ 验证卸载

### 检查 Python 模块

```bash
# 尝试导入（应该失败）
python3 -c "import neuroflow"
```

**预期输出** (卸载成功):
```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'neuroflow'
```

### 检查 CLI 命令

```bash
# 检查命令（应该显示命令未找到）
neuroflow --version
```

**预期输出** (卸载成功):
```
command not found: neuroflow
```

### 检查文件残留

```bash
# macOS/Linux
ls -la $(python3 -c "import site; print(site.getsitepackages()[0])")/ | grep neuroflow

# Windows (PowerShell)
Get-ChildItem $(python -c "import site; print(site.getsitepackages()[0])") | Where-Object { $_.Name -like "*neuroflow*" }
```

**预期输出** (卸载成功):
```
# 无输出或空列表
```

---

## ❓ 常见问题

### Q1: 提示权限不足

**错误信息**:
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**解决方案**:

```bash
# 使用 sudo
sudo pip uninstall neuroflow-sdk

# 或使用用户模式
pip uninstall --user neuroflow-sdk

# 或使用虚拟环境
python -m venv venv
source venv/bin/activate
pip uninstall neuroflow-sdk
```

### Q2: 多个 Python 版本

**问题**: 不知道从哪个 Python 版本卸载

**解决方案**:

```bash
# 列出所有 Python 版本
which -a python python3 python3.9 python3.10 python3.11

# 分别卸载
python3.9 -m pip uninstall neuroflow-sdk
python3.10 -m pip uninstall neuroflow-sdk
python3.11 -m pip uninstall neuroflow-sdk
```

### Q3: Conda 环境

**问题**: 在 Conda 环境中安装

**解决方案**:

```bash
# 激活环境
conda activate your_env_name

# 卸载
pip uninstall neuroflow-sdk

# 如果 Conda 安装
conda remove neuroflow-sdk
```

### Q4: 卸载后仍有问题

**问题**: 卸载后导入仍然成功

**解决方案**:

```bash
# 完全清理
pip uninstall neuroflow-sdk
pip cache purge
pip cache remove neuroflow

# 查找所有相关文件
find /usr -name "*neuroflow*" 2>/dev/null
find ~/.local -name "*neuroflow*" 2>/dev/null

# 手动删除
rm -rf /path/to/found/neuroflow*
```

### Q5: 虚拟环境中的卸载

**问题**: 在虚拟环境中安装后忘记激活

**解决方案**:

```bash
# 激活虚拟环境
source venv/bin/activate  # Windows: .\venv\Scripts\Activate

# 确认环境
which python  # Windows: where python

# 卸载
pip uninstall neuroflow-sdk

# 退出虚拟环境
deactivate
```

---

## 🔧 快速卸载脚本

### macOS/Linux 脚本

创建 `uninstall_neuroflow.sh`:

```bash
#!/bin/bash

echo "=================================================="
echo "  NeuroFlow 卸载脚本"
echo "=================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查虚拟环境
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  检测到虚拟环境：$VIRTUAL_ENV${NC}"
    read -p "是否在当前环境中卸载？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 卸载包
echo -e "${GREEN}✓ 卸载 NeuroFlow SDK...${NC}"
pip uninstall -y neuroflow-sdk 2>/dev/null
pip3 uninstall -y neuroflow-sdk 2>/dev/null

# 清理缓存
echo -e "${GREEN}✓ 清理 pip 缓存...${NC}"
pip cache purge 2>/dev/null || true

# 清理构建文件
if [ -d "sdk" ]; then
    echo -e "${GREEN}✓ 清理构建文件...${NC}"
    cd sdk
    rm -rf build/ dist/ *.egg-info
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -type f -name "*.pyc" -delete 2>/dev/null
    cd ..
fi

# 验证卸载
echo ""
echo -e "${GREEN}✓ 验证卸载...${NC}"
if python3 -c "import neuroflow" 2>/dev/null; then
    echo -e "${RED}✗ 卸载可能未完成，请手动检查${NC}"
else
    echo -e "${GREEN}✓ 卸载成功！${NC}"
fi

echo ""
echo "=================================================="
echo "  卸载完成"
echo "=================================================="
```

使用方法：

```bash
# 创建脚本
cat > uninstall_neuroflow.sh << 'EOF'
# 粘贴上面的脚本内容
EOF

# 添加执行权限
chmod +x uninstall_neuroflow.sh

# 运行
./uninstall_neuroflow.sh
```

### Windows PowerShell 脚本

创建 `Uninstall-NeuroFlow.ps1`:

```powershell
Write-Host "=================================================="
Write-Host "  NeuroFlow 卸载脚本" -ForegroundColor Cyan
Write-Host "=================================================="
Write-Host ""

# 卸载包
Write-Host "✓ 卸载 NeuroFlow SDK..." -ForegroundColor Green
pip uninstall -y neuroflow-sdk 2>$null
pip3 uninstall -y neuroflow-sdk 2>$null

# 清理缓存
Write-Host "✓ 清理 pip 缓存..." -ForegroundColor Green
pip cache purge 2>$null

# 清理残留文件
Write-Host "✓ 清理残留文件..." -ForegroundColor Green
$sitePackages = python -c "import site; print(site.getsitepackages()[0])" 2>$null
if ($sitePackages) {
    Remove-Item -Recurse -Force "$sitePackages\neuroflow*" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$sitePackages\neuroflow_sdk*" -ErrorAction SilentlyContinue
}

# 验证卸载
Write-Host ""
Write-Host "✓ 验证卸载..." -ForegroundColor Green
try {
    python -c "import neuroflow" 2>$null
    Write-Host "✗ 卸载可能未完成，请手动检查" -ForegroundColor Red
} catch {
    Write-Host "✓ 卸载成功！" -ForegroundColor Green
}

Write-Host ""
Write-Host "=================================================="
Write-Host "  卸载完成" -ForegroundColor Cyan
Write-Host "=================================================="
```

使用方法：

```powershell
# 创建脚本
@"
粘贴上面的脚本内容
"@ | Out-File -FilePath Uninstall-NeuroFlow.ps1 -Encoding utf8

# 运行（需要允许执行脚本）
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\Uninstall-NeuroFlow.ps1
```

---

## 📚 相关文档

- [安装指南](installation.md)
- [常见问题](faq.md)
- [故障排除](../troubleshooting/faq.md)

---

**需要重新安装？**: [安装指南](installation.md)

**遇到问题？**: [故障排除](../troubleshooting/faq.md)
