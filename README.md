# vllm-kubernetes-plugin

Common vllm plugins for kubernetes deployment.


## Description

`vllm-kubernetes-plugin` is a set of plugins for vllm to enhance kubernetes deployment.


## 快速开始

### 安装

选择您偏好的安装方式：

```bash
# 🚀 使用 UV (推荐)
uv pip install vllm-kubernetes-plugin

# 📦 使用 Pip (传统)
pip install vllm-kubernetes-plugin

# 🎯 使用 Poetry
poetry add vllm-kubernetes-plugin

# 📄 使用 requirements.txt
pip install -r requirements.txt
```

### 开发环境安装

```bash
# 克隆项目
git clone https://github.com/MonadKai/vllm-kubernetes-plugin.git
cd vllm-kubernetes-plugin

# 使用 UV (推荐)
uv pip install -e ".[dev]"

# 或使用传统方式
pip install -r requirements-dev.txt
pip install -e .
```

详细安装指南请参考 [INSTALL.md](./INSTALL.md)。

### 构建项目

```bash
# 自动构建 (推荐)
python3 build_with_config.py

# 或手动构建
python3 scripts/generate_config.py
uv build
```

### 部署到容器/K8s

```bash
# 构建项目
python3 build_with_config.py

# 1. Docker 部署
docker cp ./dist/vllm_kubernetes_plugin-0.1.0-py3-none-any.whl <container-id>:/tmp/
docker exec -it <container-id> pip install /tmp/vllm_kubernetes_plugin-0.1.0-py3-none-any.whl

# 2. Kubernetes 部署
kubectl cp ./dist/vllm_kubernetes_plugin-0.1.0-py3-none-any.whl <pod-name>:/tmp/
kubectl exec -it <pod-name> -- pip install /tmp/vllm_kubernetes_plugin-0.1.0-py3-none-any.whl
```


### Usage


```
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<your-served-model-name>",
    "messages": [{"role": "user", "content": "hello"}]
  }'
```

Check log content in docker container or kubernetes pod:

```
# in docker way
docker exec -it <your-vllm-container-id> /bin/bash

tail -f /vllm-workspace/logs/server.log

# in kubernetes way
kubectl exec -it <your-vllm-pod-name> -- bash

tail -f /vllm-workspace/logs/server.log
```

## 文档

- 📖 [安装指南](./INSTALL.md) - 详细的安装说明和故障排除
- 🔧 [构建系统](./BUILD.md) - 构建配置和自动化构建
- 🎯 [使用示例](./docs/examples/) - 实际使用案例和配置

## Roadmap


## Contributing


## Authors and acknowledgment

This project is developed by the AI infra team of bairong-inc.

## License

This project is licensed under the Apache 2.0 License. See the LICENSE file for details.

