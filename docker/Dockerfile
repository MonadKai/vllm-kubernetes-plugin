ARG VLLM_IMAGE=vllm/vllm-openai:v0.10.1.1

FROM ${VLLM_IMAGE}

# add vllm kubernetes plugin support
COPY dist/vllm_kubernetes_plugin-0.1.0.tar.gz /tmp/vllm_kubernetes_plugin-0.1.0.tar.gz
RUN pip install /tmp/vllm_kubernetes_plugin-0.1.0.tar.gz --no-deps && rm -rf /tmp/vllm_kubernetes_plugin-0.1.0.tar.gz

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
