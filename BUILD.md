# Build System Documentation

这个项目支持在构建过程中自动生成 vLLM 配置。**推荐使用 `build_with_config.py` 自动构建脚本**，它会自动处理配置生成和构建过程。

对于手动构建，配置文件需要在构建前先生成，使用任何现代 Python 构建工具都可以。

## Automatic Configuration Generation

The build system automatically:
1. Scans the vLLM installation for modules containing loggers
2. Identifies methods with `request_id` or `req_id` parameters  
3. Generates configuration files in `src/vllm_kubernetes_plugin/config/`
4. Includes these files in the built package

## Automated Build (推荐方式)

### 使用自动构建脚本 (最简单)
```bash
# 自动生成配置并构建项目 (推荐)
python3 build_with_config.py
```

这个脚本会：
1. 🧹 清理之前的构建文件 (build/, dist/, *.egg-info/)
2. 🔄 自动运行 vLLM 配置生成
3. 📦 构建源码包和轮子包
4. 📊 显示构建进度和结果

## 手动构建工具

### Using UV (需要手动生成配置)
```bash
# 首先生成配置
python3 scripts/generate_config.py

# 然后构建
uv build

# Install in development mode
uv pip install -e .
```

### Using Poetry
```bash
# 首先生成配置
python3 scripts/generate_config.py

# Build wheel and source distribution
poetry build

# Install in development mode
poetry install
```

### Using Build (PEP 517)
```bash
# generate package scanned information
python3 scripts/generate_config.py

# Build wheel and source distribution
python3 -m build

# Build only wheel
python3 -m build --wheel
```

### Using Pip
```bash
# generate package scanned information
python3 scripts/generate_config.py

# Install in development mode (editable install)
pip install -e .

# Build and install
pip install .
```

### Legacy Setup.py
```bash
# 首先生成配置
python3 scripts/generate_config.py

# Build using setup.py (legacy)
python3 setup.py build
python3 setup.py bdist_wheel

```

## Configuration Output

After building, you'll find these generated files:

- `src/vllm_kubernetes_plugin/config/vllm_mappings.py` - Python module with configuration
- `src/vllm_kubernetes_plugin/config/__init__.py` - Package initialization
- `scripts/test_output/vllm_mappings.json` - JSON validation file (not included in package)

## Testing the Build System

Run the build validation test:
```bash
python3 scripts/test_build.py
```

This will:
1. Test configuration generation
2. Test wheel building
3. Verify configuration files exist

## Manual Configuration Generation

If you need to generate configurations manually:
```bash
python3 scripts/generate_config.py
```

## Validation and Testing

Test the generated configurations:
```bash
# Test request_id methods scanning
python scripts/test_find_methods.py

# Test logger modules scanning  
python scripts/test_find_loggers.py
```

## Build Backend Details

这个项目使用标准的 Hatchling 构建后端。为了自动化配置生成，我们提供了 `build_with_config.py` 包装脚本，它在构建前自动运行配置生成。这确保了与所有现代 Python 构建工具的兼容性。

## Troubleshooting

### 推荐解决方案
如果遇到构建问题，首先尝试使用自动构建脚本：
```bash
python3 build_with_config.py
```

### Configuration Generation Fails
- 确保 vLLM 已安装: `pip install vllm>=0.5.5`
- 检查 Python 版本兼容性 (>=3.9)
- 验证 scripts 目录存在并包含 `generate_config.py`
- 如果手动生成失败，自动构建脚本会继续执行但可能缺少运行时配置

### Build Fails
- 安装构建依赖: `pip install build hatchling uv`
- 检查 `pyproject.toml` 中缺失的依赖
- 先运行手动配置生成: `python3 scripts/generate_config.py`
- 或使用自动构建脚本: `python3 build_with_config.py`

### Import Errors
- 确保包已正确安装
- 检查配置文件是否已生成
- 验证 `src/vllm_kubernetes_plugin/` 中的包结构
- 尝试重新运行配置生成或自动构建脚本 