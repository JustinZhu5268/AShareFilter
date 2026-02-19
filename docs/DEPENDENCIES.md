# AShareFilter 依赖说明文档

本文档详细说明 AShareFilter 项目所需的依赖包及其版本要求。

---

## 1. 环境要求

| 要求 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.9 | 3.11+ |
| pip | 20.0 | 最新版本 |

---

## 2. 依赖清单

### 2.1 核心依赖

| 包名 | 版本要求 | 说明 |
|------|----------|------|
| pandas | >=1.5.0 | 数据处理与分析 |
| numpy | >=1.21.0 | 数值计算 |
| tushare | >=1.3.0 | A股数据接口 |

### 2.2 测试框架

| 包名 | 版本要求 | 说明 |
|------|----------|------|
| pytest | >=7.0.0 | 单元测试框架 |
| pytest-cov | >=4.0.0 | 测试覆盖率 |
| pytest-xdist | >=3.0.0 | 并行测试 |
| pytest-timeout | >=2.1.0 | 测试超时控制 |
| pytest-mock | >=3.10.0 | Mock 框架 |

### 2.3 代码质量

| 包名 | 版本要求 | 说明 |
|------|----------|------|
| pylint | >=2.17.0 | 代码检查 |
| black | >=23.0.0 | 代码格式化 |
| flake8 | >=6.0.0 | 代码风格检查 |
| isort | >=5.12.0 | import 排序 |

### 2.4 文档工具

| 包名 | 版本要求 | 说明 |
|------|----------|------|
| sphinx | >=6.0.0 | 文档生成 |
| sphinx-rtd-theme | >=1.2.0 | ReadTheDocs 主题 |

### 2.5 其他工具

| 包名 | 版本要求 | 说明 |
|------|----------|------|
| requests | >=2.28.0 | HTTP 请求库 |
| python-dateutil | >=2.8.2 | 日期处理工具 |

---

## 3. 安装方式

### 3.1 安装所有依赖

```bash
pip install -r requirements.txt
```

### 3.2 安装开发依赖

```bash
pip install -r requirements-dev.txt
```

### 3.3 安装生产依赖

```bash
pip install pandas numpy tushare
```

---

## 4. requirements.txt 完整内容

```text
# AShareFilter 依赖包

# 数据处理
pandas>=1.5.0
numpy>=1.21.0

# Tushare API
tushare>=1.3.0

# 测试框架
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-xdist>=3.0.0
pytest-timeout>=2.1.0
pytest-mock>=3.10.0

# 代码质量
pylint>=2.17.0
black>=23.0.0
flake8>=6.0.0
isort>=5.12.0

# 文档
sphinx>=6.0.0
sphinx-rtd-theme>=1.2.0

# 其他工具
requests>=2.28.0
python-dateutil>=2.8.2
```

---

## 5. 依赖版本兼容性

### 5.1 Python 版本兼容性

| Python 版本 | pandas | numpy | tushare |
|-------------|--------|-------|---------|
| 3.9 | 1.5.x | 1.21.x | 1.3.x+ |
| 3.10 | 1.5.x+ | 1.23.x+ | 1.3.x+ |
| 3.11 | 2.0.x+ | 1.24.x+ | 1.3.x+ |

### 5.2 已知兼容性问题

| 组合 | 状态 | 说明 |
|------|------|------|
| Python 3.11 + pandas 1.5.x | ✅ 兼容 | 推荐组合 |
| Python 3.9 + numpy 1.24.x | ⚠️ 警告 | 可能有性能问题 |
| Python 3.9 + tushare 1.4.x | ✅ 兼容 | 新版本更好 |

---

## 6. 虚拟环境建议

### 6.1 使用 venv 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 6.2 使用 conda 创建环境

```bash
# 创建环境
conda create -n asharefilter python=3.11

# 激活环境
conda activate asharefilter

# 安装依赖
pip install -r requirements.txt
```

---

## 7. 依赖更新检查

### 7.1 检查过期依赖

```bash
pip list --outdated
```

### 7.2 更新依赖

```bash
# 更新所有依赖
pip install --upgrade -r requirements.txt

# 更新单个包
pip install --upgrade pandas
```

---

## 8. 故障排除

### 8.1 常见问题

| 问题 | 解决方案 |
|------|----------|
| 安装失败 | 使用 `pip install --no-cache-dir` |
| 版本冲突 | 创建新的虚拟环境 |
| 编译失败 | 安装 Visual C++ Build Tools (Windows) |

### 8.2 Tushare Token 配置

在 `config/config.py` 中配置：

```python
TUSHARE_TOKEN = "your_token_here"
```

获取 Token: [Tushare Pro](https://tushare.pro/)

---

*文档版本: V1.0*  
*更新时间: 2026-02-19*
