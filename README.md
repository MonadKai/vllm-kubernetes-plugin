# vllm-kubernetes-plugin

Common vllm plugins for kubernetes deployment.


## Description

`vllm-kubernetes-plugin` is a set of plugins for vllm to enhance kubernetes deployment.


## Getting started


```
# Build and install the package
python setup.py sdist bdist_wheel


# Install the package
# 1. in docker way
docker cp ./dist/vllm_kubernetes_plugin-0.0.1.tar.gz <your-vllm-container-id>:/vllm-workspace/vllm_kubernetes_plugin-0.0.1.tar.gz
docker exec -it <your-vllm-container-id> bash
pip install ./vllm_kubernetes_plugin-0.0.1-py3-none-any.whl

# 2. in kubernetes way
kubectl cp ./dist/vllm_kubernetes_plugin-0.0.1.tar.gz <your-vllm-pod-name>:/vllm-workspace/vllm_kubernetes_plugin-0.0.1.tar.gz
kubectl exec -it <your-vllm-pod-name> -- bash
pip install ./vllm_kubernetes_plugin-0.0.1-py3-none-any.whl
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

## Roadmap


## Contributing


## Authors and acknowledgment

This project is developed by the AI infra team of bairong-inc.

## License

This project is licensed under the Apache 2.0 License. See the LICENSE file for details.

