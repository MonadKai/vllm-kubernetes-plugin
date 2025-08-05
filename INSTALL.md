# 安装指南

本项目支持多种安装方式，您可以根据偏好选择最适合的方式。

## 快速安装

### 🚀 使用 UV (推荐)

```bash
# 安装基础包
uv pip install vllm-kubernetes-plugin

# 安装开发环境
uv pip install "vllm-kubernetes-plugin[dev]"

# 安装特定功能
uv pip install "vllm-kubernetes-plugin[test,docs]"
```

### 📦 使用 Pip (传统方式)

```bash
# 基础安装
pip install vllm-kubernetes-plugin

# 从源码安装
pip install git+https://github.com/MonadKai/vllm-kubernetes-plugin.git

# 开发模式安装
pip install -e ".[dev]"
```

### 🎯 使用 Poetry

```bash
# 添加到项目
poetry add vllm-kubernetes-plugin

# 开发依赖
poetry add --group dev vllm-kubernetes-plugin[dev]
```

## 传统 Requirements.txt 方式

项目提供了多个 requirements 文件支持不同场景：

### 基础安装
```bash
pip install -r requirements.txt
```

### 开发环境
```bash
pip install -r requirements-dev.txt
```

### 测试环境
```bash
pip install -r requirements-test.txt
```

### 文档生成
```bash
pip install -r requirements-docs.txt
```

## 可选依赖组

使用现代包管理工具时，可以安装特定的依赖组：

| 依赖组 | 用途 | 安装命令 |
|--------|------|----------|
| `dev` | 完整开发环境 | `pip install ".[dev]"` |
| `test` | 测试工具 | `pip install ".[test]"` |
| `docs` | 文档生成 | `pip install ".[docs]"` |
| `lint` | 代码质量检查 | `pip install ".[lint]"` |
| `build` | 构建工具 | `pip install ".[build]"` |

### 组合安装
```bash
# 安装多个组
pip install ".[test,docs,lint]"

# UV 方式
uv pip install ".[dev]"

# Poetry 方式
poetry install --extras "test docs"
```

## 开发环境设置

### 使用 UV (推荐)
```bash
# 克隆项目
git clone https://github.com/MonadKai/vllm-kubernetes-plugin.git
cd vllm-kubernetes-plugin

# 创建虚拟环境并安装
uv venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

uv pip install -e ".[dev]"
```

### 使用 Poetry
```bash
git clone https://github.com/MonadKai/vllm-kubernetes-plugin.git
cd vllm-kubernetes-plugin

# 安装依赖
poetry install --extras "dev"

# 激活虚拟环境
poetry shell
```

### 使用传统 Pip
```bash
git clone https://github.com/MonadKai/vllm-kubernetes-plugin.git
cd vllm-kubernetes-plugin

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements-dev.txt
pip install -e .
```

## 验证安装

安装完成后，验证是否正确安装：

```python
import vllm_kubernetes_plugin
print(vllm_kubernetes_plugin.__version__)
```

## 常见问题

### vLLM 依赖问题
确保您的系统满足 vLLM 的要求：
```bash
# 检查 CUDA 版本 (如果使用 GPU)
nvidia-smi

# 安装对应的 PyTorch 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

### 权限问题
如果遇到权限问题：
```bash
# 使用用户安装
pip install --user vllm-kubernetes-plugin

# 或使用虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate
pip install vllm-kubernetes-plugin
```

### 网络问题
如果遇到网络问题：
```bash
# 使用国内镜像
pip install vllm-kubernetes-plugin -i https://pypi.tuna.tsinghua.edu.cn/simple

# UV 使用镜像
uv pip install vllm-kubernetes-plugin --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

## 卸载

```bash
# Pip
pip uninstall vllm-kubernetes-plugin

# UV  
uv pip uninstall vllm-kubernetes-plugin

# Poetry
poetry remove vllm-kubernetes-plugin
```