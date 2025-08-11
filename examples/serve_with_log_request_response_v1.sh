#!/bin/bash

# traditional vLLM environment variables
export CUDA_VISIBLE_DEVICES="0,1"
export PYDEVD_WARN_SLOW_RESOLVE_TIMEOUT="999999999"
export VLLM_USE_V1="1"
export VLLM_ATTENTION_BACKEND="FLASHINFER"
export VLLM_ENABLE_V1_MULTIPROCESSING="4"
export VLLM_AUDIO_FETCH_TIMEOUT="999999999"
export VLLM_RPC_TIMEOUT="999999999"
export VLLM_ENGINE_ITERATION_TIMEOUT_S="999999999"

# additional vllm-kubernetes-plugin logging environment variables (basic)
export VLLM_LOGGING_CONFIG_PATH=""
export VLLM_CONFIGURE_LOGGING="0"

export APP_NAME="qwen2-5-7b-instruct"
export LOG_ROOT_MODULES="vllm,lmcache"
export VLLM_LOG_FORMAT="%(asctime)s.%(msecs)03d [{app_name}] [%(threadName)s] %(levelname)s [%(name)s.%(funcName)s] [-] %(message)s"
export VLLM_LOG_DATE_FORMAT="%Y-%m-%d %H:%M:%S"
export VLLM_LOG_FILENAME="api_server.log"
export VLLM_LOG_FILE_MAX_BYTES="8388608"
export VLLM_LOG_FILE_BACKUP_COUNT="5"

# additional vllm-kubernetes-plugin trace environment variables
export VLLM_TRACE_METHODS_WITH_REQUEST_ID="true"

# additional vllm-kubernetes-plugin log request response environment variables
export VLLM_DEBUG_LOG_API_SERVER_REQUEST_RESPONSE="true"
export VLLM_DEBUG_LOG_API_SERVER_RESPONSE="true"


# Run the vLLM server
# since environment variables are enabled, we don't need to add the middleware manually, and the log_response middleware is already replaced by vllm_kubernetes_plugin
python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --dtype auto \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.7 \
    --tensor-parallel-size 2 \
    --enforce-eager \
    --enable-prefix-caching \
    --served-model-name model \
    --port 8000 \
    --enable-request-id-headers \
    --disable-fastapi-docs \
    --disable-log-requests \
    # --middleware vllm_kubernetes_plugin.log_request_response.log_response
