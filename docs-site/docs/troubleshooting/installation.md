# 安装问题

NeuroFlow 安装问题的故障排除指南。

## 常见问题

### Q1: pip 找不到 neuroflow 包

**错误信息**:
```
ERROR: Could not find a version that satisfies the requirement neuroflow
```

**解决方案**:

```bash
# 1. 升级 pip
pip install --upgrade pip

# 2. 清除缓存
pip cache purge

# 3. 重新安装
pip install neuroflow --no-cache-dir
```

### Q2: 权限错误

**错误信息**:
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**解决方案**:

```bash
# macOS/Linux - 使用 --user
pip install --user neuroflow

# 或使用虚拟环境（推荐）
python -m venv venv
source venv/bin/activate
pip install neuroflow

# Windows - 以管理员身份运行
# 右键 PowerShell -> 以管理员身份运行
pip install neuroflow
```

### Q3: Python 版本不兼容

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

### Q4: 依赖冲突

**错误信息**:
```
ERROR: Cannot install neuroflow and these requirements conflict
```

**解决方案**:

```bash
# 创建新的虚拟环境
python -m venv venv-clean
source venv-clean/bin/activate

# 安装
pip install neuroflow

# 如果还有问题，升级依赖
pip install --upgrade setuptools wheel
```

### Q5: neuroflow 命令找不到

**错误信息**:
```
command not found: neuroflow
```

**解决方案**:

```bash
# 检查虚拟环境是否激活
which python  # Windows: where python

# 手动添加路径到 PATH
# macOS/Linux
export PATH=$PATH:~/.local/bin

# Windows (PowerShell)
$env:Path += ";$env:APPDATA\Python\Python311\Scripts"

# 永久添加到 ~/.bashrc 或 ~/.zshrc
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

### Q6: 依赖安装失败

**错误信息**:
```
ERROR: Failed building wheel for xxx
```

**解决方案**:

```bash
# 安装构建工具
# macOS
xcode-select --install

# Ubuntu
sudo apt install build-essential python3-dev

# 然后重新安装
pip install neuroflow
```

### Q7: SSL 证书错误

**错误信息**:
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**解决方案**:

```bash
# macOS
/Applications/Python 3.11/Install Certificates.command

# 或使用 pip 参数
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org neuroflow
```

### Q8: 下载速度慢

**解决方案**:

```bash
# 使用国内镜像
pip install neuroflow -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像
pip install neuroflow -i https://mirrors.aliyun.com/pypi/simple/
```

## 平台特定问题

### macOS

#### M1/M2芯片问题

```bash
# 使用 Rosetta 2
arch -x86_64 pip install neuroflow

# 或原生支持
pip install --upgrade pip setuptools wheel
pip install neuroflow
```

### Linux

#### 缺少系统库

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-dev libssl-dev libffi-dev

# CentOS/RHEL
sudo yum install -y python3-devel openssl-devel
```

### Windows

#### 路径长度限制

```powershell
# 启用长路径支持
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# 重启后生效
```

## 验证安装

```bash
# 检查版本
neuroflow --version

# 检查导入
python -c "import neuroflow; print(neuroflow.__version__)"

# 运行测试
neuroflow --help
```

## 获取帮助

如果以上方法都无法解决问题：

1. **查看日志**: `pip install -v neuroflow` 查看详细日志
2. **搜索 Issue**: [GitHub Issues](https://github.com/lamWimHam/neuroflow/issues)
3. **提交 Issue**: 提供错误信息和环境信息

---

**相关文档**: [安装指南](installation.md) | [常见问题](faq.md)
