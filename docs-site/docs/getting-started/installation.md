# 安装 NeuroFlow

本指南将帮助你在不同平台上安装 NeuroFlow SDK 和相关工具。

## 📋 系统要求

### 最低要求

- **Python**: 3.9+
- **操作系统**: macOS 10.15+, Linux (Ubuntu 20.04+), Windows 10+
- **内存**: 至少 2GB RAM
- **磁盘空间**: 至少 500MB 可用空间

### 推荐配置

- **Python**: 3.10 或 3.11
- **操作系统**: macOS 12+, Ubuntu 22.04+, Windows 11
- **内存**: 4GB+ RAM
- **磁盘空间**: 1GB+ 可用空间

### 可选：Rust 开发环境

如果你需要开发 Rust 内核或使用高级功能：

- **Rust**: 1.70+
- **Cargo**: 1.70+
- **Protobuf 编译器**: protoc 3.15+

## 🚀 快速安装

### 方法 1: 使用 pip (推荐)

```bash
# 安装 NeuroFlow SDK (包含 CLI 工具)
pip install neuroflow

# 验证安装
neuroflow --version
```

**预期输出**:
```
neuroflow, version 0.3.0
```

### 方法 2: 从源码安装

```bash
# 克隆仓库
git clone https://github.com/lamwimham/neuroflow.git
cd neuroflow/sdk

# 安装开发版本
pip install -e .

# 验证安装
neuroflow --version
```

## 📦 平台特定指南

### macOS

#### 1. 安装 Python (如果未安装)

```bash
# 使用 Homebrew (推荐)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.11

# 验证 Python 版本
python3 --version
```

#### 2. 创建虚拟环境

```bash
# 创建项目目录
mkdir -p ~/projects/neuroflow
cd ~/projects/neuroflow

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

#### 3. 安装 NeuroFlow

```bash
# 安装 SDK
pip install neuroflow

# 验证
neuroflow --version
```

### Linux (Ubuntu/Debian)

#### 1. 安装系统依赖

```bash
# 更新包列表
sudo apt update

# 安装 Python 和 pip
sudo apt install -y python3 python3-pip python3-venv

# 安装开发工具 (可选)
sudo apt install -y build-essential python3-dev
```

#### 2. 创建虚拟环境

```bash
# 创建项目目录
mkdir -p ~/projects/neuroflow
cd ~/projects/neuroflow

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

#### 3. 安装 NeuroFlow

```bash
# 安装 SDK
pip install neuroflow

# 验证
neuroflow --version
```

### Linux (CentOS/RHEL)

#### 1. 安装 Python

```bash
# 安装 EPEL 仓库
sudo yum install -y epel-release

# 安装 Python 3.11
sudo yum install -y python311 python311-pip python311-devel

# 验证
python3 --version
```

#### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装 NeuroFlow

```bash
pip install neuroflow
neuroflow --version
```

### Windows

#### 1. 安装 Python

1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载 Python 3.11 安装程序
3. 运行安装程序
4. **重要**: 勾选 "Add Python to PATH"

#### 2. 验证安装

```powershell
# 打开 PowerShell 或 CMD
python --version
pip --version
```

#### 3. 创建虚拟环境

```powershell
# 创建项目目录
mkdir C:\projects\neuroflow
cd C:\projects\neuroflow

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate
```

#### 4. 安装 NeuroFlow

```powershell
# 安装 SDK
pip install neuroflow

# 验证
neuroflow --version
```

## 🔧 可选：安装 Rust 开发环境

如果你需要开发 Rust 内核：

### 1. 安装 Rust

```bash
# macOS/Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Windows: 下载并运行 rustup-init.exe
# https://rustup.rs/
```

### 2. 验证 Rust 安装

```bash
rustc --version
cargo --version
```

**预期输出**:
```
rustc 1.75.0 (...)
cargo 1.75.0 (...)
```

### 3. 安装 Protobuf 编译器

```bash
# macOS (使用 Homebrew)
brew install protobuf

# Linux (Ubuntu/Debian)
sudo apt install -y protobuf-compiler

# Windows
# 下载预编译二进制文件
# https://github.com/protocolbuffers/protobuf/releases
```

### 4. 验证 Protobuf

```bash
protoc --version
```

## ✅ 验证安装

### 1. 检查 CLI 工具

```bash
# 查看版本
neuroflow --version

# 查看帮助
neuroflow --help

# 查看可用命令
neuroflow --help
```

### 2. 创建测试项目

```bash
# 创建测试项目
neuroflow new test-project

# 进入项目目录
cd test-project

# 检查项目结构
ls -la
```

**预期输出**:
```
test-project/
├── agents/
├── tools/
├── config/
├── tests/
├── requirements.txt
└── README.md
```

### 3. 运行测试

```bash
# 安装项目依赖
pip install -r requirements.txt

# 运行测试
pytest

# 启动开发服务器
neuroflow run
```

## 🐛 常见问题

### Q1: pip 找不到 neuroflow 包

**解决方案**:

```bash
# 升级 pip
pip install --upgrade pip

# 清除缓存
pip cache purge

# 重新安装
pip install neuroflow --no-cache-dir
```

### Q2: 权限错误 (Permission Denied)

**macOS/Linux**:

```bash
# 不要使用 sudo，而是使用 --user 标志
pip install --user neuroflow

# 或者使用虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate
pip install neuroflow
```

**Windows**:

```powershell
# 以管理员身份运行 PowerShell
# 或者使用 --user 标志
pip install --user neuroflow
```

### Q3: 依赖冲突

**解决方案**:

```bash
# 创建新的虚拟环境
python -m venv venv-clean
source venv-clean/bin/activate  # Windows: .\venv-clean\Scripts\Activate

# 安装
pip install neuroflow

# 如果还有问题，尝试升级依赖
pip install --upgrade setuptools wheel
```

### Q4: neuroflow 命令找不到

**解决方案**:

```bash
# 检查虚拟环境是否激活
which python  # Windows: where python

# 手动添加路径到 PATH
# macOS/Linux
export PATH=$PATH:~/.local/bin

# Windows (PowerShell)
$env:Path += ";$env:APPDATA\Python\Python311\Scripts"
```

### Q5: Python 版本不兼容

**错误信息**:
```
ERROR: Package 'neuroflow' requires a different Python: 3.8.10 not in '>=3.9'
```

**解决方案**:

```bash
# 安装 Python 3.11
# macOS
brew install python@3.11

# Ubuntu
sudo apt install python3.11

# 创建虚拟环境时指定版本
python3.11 -m venv venv
source venv/bin/activate
pip install neuroflow
```

## 📚 下一步

安装完成后，请继续:

1. **[30 分钟快速入门](quickstart.md)** - 创建第一个 Agent
2. **[创建第一个 Agent](first-agent.md)** - 详细教程
3. **[概念指南](../concepts/architecture.md)** - 理解核心概念

## 🆘 获取帮助

如果遇到问题:

- 📖 查看 [故障排除指南](../troubleshooting/faq.md)
- 💬 加入 [Discord 社区](https://discord.gg/neuroflow)
- 🐛 提交 [GitHub Issue](https://github.com/lamwimham/neuroflow/issues)
- 📧 发送邮件至 support@neuroflow.ai (即将上线)

## 📝 参考资源

- [Python 官方文档](https://docs.python.org/3/)
- [pip 用户指南](https://pip.pypa.io/en/stable/)
- [虚拟环境指南](https://docs.python.org/3/library/venv.html)
- [NeuroFlow GitHub](https://github.com/lamwimham/neuroflow)

---

## 🗑️ 卸载 NeuroFlow

如果你需要卸载 NeuroFlow，请按照以下步骤操作：

### 方法 1: 使用 pip 卸载（推荐）

```bash
# 进入 SDK 目录（如果是从源码安装）
cd /path/to/NeuroFlow/sdk

# 卸载
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

### 方法 2: 完全清理

```bash
# 1. 卸载包
pip uninstall neuroflow-sdk

# 2. 清理 pip 缓存
pip cache purge

# 3. 删除安装文件（如果需要）
# 查找安装位置
python3 -c "import neuroflow; print(neuroflow.__file__)"

# 手动删除残留文件
rm -rf ~/Library/Python/*/lib/python/site-packages/neuroflow*
# 或者
rm -rf /usr/local/lib/python*/site-packages/neuroflow*
```

### 方法 3: 开发模式安装清理

```bash
# 进入 SDK 目录
cd /path/to/NeuroFlow/sdk

# 卸载开发模式安装
pip uninstall neuroflow-sdk

# 清理构建文件
rm -rf build/
rm -rf dist/
rm -rf *.egg-info

# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 方法 4: 完全删除项目

如果你想完全删除整个 NeuroFlow 项目：

```bash
# 返回上级目录
cd /path/to/indie/

# 删除整个项目
rm -rf NeuroFlow/

# 验证删除
ls NeuroFlow  # 应该显示 "No such file or directory"
```

### 平台特定卸载

#### macOS/Linux

```bash
# 使用 sudo（如果以系统模式安装）
sudo pip uninstall neuroflow-sdk

# 或者使用用户模式
pip uninstall --user neuroflow-sdk

# 清理 Homebrew 安装的 Python 包（如果适用）
brew cleanup
```

#### Windows

```powershell
# 以管理员身份运行 PowerShell
pip uninstall neuroflow-sdk

# 或者使用用户模式
pip uninstall --user neuroflow-sdk

# 清理残留文件
Remove-Item -Recurse -Force $env:APPDATA\Python\Python311\site-packages\neuroflow* -ErrorAction SilentlyContinue
```

### 验证卸载

```bash
# 验证是否卸载成功
python3 -c "import neuroflow"

# 如果显示 ModuleNotFoundError，说明卸载成功
# 如果导入成功，说明还有残留
```

**预期输出** (卸载成功):
```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'neuroflow'
```

### 常见问题

#### Q1: 提示权限不足

**解决方案**:

```bash
# 使用 sudo
sudo pip uninstall neuroflow-sdk

# 或使用用户模式
pip uninstall --user neuroflow-sdk
```

#### Q2: 多个 Python 版本

```bash
# 指定 Python 版本卸载
python3.9 -m pip uninstall neuroflow-sdk
python3.10 -m pip uninstall neuroflow-sdk
python3.11 -m pip uninstall neuroflow-sdk
```

#### Q3: Conda 环境

```bash
# 如果使用 Conda
conda activate your_env
pip uninstall neuroflow-sdk
```

#### Q4: 卸载后仍有问题

```bash
# 完全清理
pip uninstall neuroflow-sdk
pip cache purge
pip cache remove neuroflow

# 重新安装（如果需要）
pip install neuroflow
```

### 快速卸载脚本

创建一个快速卸载脚本 `uninstall.sh`:

```bash
#!/bin/bash
echo "开始卸载 NeuroFlow..."

# 卸载包
pip uninstall -y neuroflow-sdk
pip3 uninstall -y neuroflow-sdk

# 清理缓存
pip cache purge 2>/dev/null || true

# 清理构建文件
cd /path/to/NeuroFlow/sdk 2>/dev/null && {
    rm -rf build/ dist/ *.egg-info
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
}

echo "✓ 卸载完成！"
```

使用方法：

```bash
chmod +x uninstall.sh
./uninstall.sh
```

---

**继续学习**: [30 分钟快速入门](quickstart.md) →
