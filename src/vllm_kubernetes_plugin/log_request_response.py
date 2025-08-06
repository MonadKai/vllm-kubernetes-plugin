import json
import warnings
from typing import Optional

import pydantic
import vllm.envs as envs
from fastapi import FastAPI, Request
from starlette.concurrency import iterate_in_threadpool
from vllm.entrypoints.openai.api_server import logger
from vllm.entrypoints.openai.protocol import ChatCompletionRequest, CompletionRequest
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat
from vllm.entrypoints.openai.serving_completion import OpenAIServingCompletion
from starlette.middleware.base import BaseHTTPMiddleware
import os

__all__ = ["log_response", "register_log_request_response_plugin"]


def add_log_request_response_env_vars() -> None:
    additional_env_vars = {
        "VLLM_DEBUG_LOG_API_SERVER_REQUEST_RESPONSE": lambda: os.getenv(
            "VLLM_DEBUG_LOG_API_SERVER_REQUEST_RESPONSE", "False"
        ).lower()
        in ("true", "1"),
    }
    envs.environment_variables.update(additional_env_vars)


def _extract_content_from_chunk(chunk_data: dict) -> str:
    """Extract content from a streaming response chunk."""
    try:
        from vllm.entrypoints.openai.protocol import (
            ChatCompletionStreamResponse,
            CompletionStreamResponse,
        )

        # Try using Completion types for type-safe parsing
        if chunk_data.get("object") == "chat.completion.chunk":
            chat_response = ChatCompletionStreamResponse.model_validate(chunk_data)
            if chat_response.choices and chat_response.choices[0].delta.content:
                return chat_response.choices[0].delta.content
        elif chunk_data.get("object") == "text_completion":
            completion_response = CompletionStreamResponse.model_validate(chunk_data)
            if completion_response.choices and completion_response.choices[0].text:
                return completion_response.choices[0].text
    except pydantic.ValidationError:
        # Fallback to manual parsing
        if "choices" in chunk_data and chunk_data["choices"]:
            choice = chunk_data["choices"][0]
            if "delta" in choice and choice["delta"].get("content"):
                return choice["delta"]["content"]
            elif choice.get("text"):
                return choice["text"]
    return ""


class SSEDecoder:
    """Robust Server-Sent Events decoder for streaming responses."""

    def __init__(self):
        self.buffer = ""
        self.content_buffer = []

    def decode_chunk(self, chunk: bytes) -> list[dict]:
        """Decode a chunk of SSE data and return parsed events."""
        import json

        try:
            chunk_str = chunk.decode("utf-8")
        except UnicodeDecodeError:
            # Skip malformed chunks
            return []

        self.buffer += chunk_str
        events = []

        # Process complete lines
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            line = line.rstrip("\r")  # Handle CRLF

            if line.startswith("data: "):
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    events.append({"type": "done"})
                elif data_str:
                    try:
                        event_data = json.loads(data_str)
                        events.append({"type": "data", "data": event_data})
                    except json.JSONDecodeError:
                        # Skip malformed JSON
                        continue

        return events

    def extract_content(self, event_data: dict) -> str:
        """Extract content from event data."""
        return _extract_content_from_chunk(event_data)

    def add_content(self, content: str) -> None:
        """Add content to the buffer."""
        if content:
            self.content_buffer.append(content)

    def get_complete_content(self) -> str:
        """Get the complete buffered content."""
        return "".join(self.content_buffer)


def _is_completion_endpoint(path: str) -> bool:
    """Check if the request is for a completion endpoint."""
    return path in ["/v1/chat/completions", "/v1/completions"]


# DEPRECATED due to performance issue
def _log_request_body(request_id: str, path: str, request_body: bytes) -> None:
    """Log request body as JSON if it's a completion endpoint."""
    if not _is_completion_endpoint(path):
        return

    try:
        # Try to decode as UTF-8
        body_str = request_body.decode("utf-8")

        # Try to parse as JSON
        try:
            json_data = json.loads(body_str)
            # TODO: ignore multi-modal content
            # Truncate if too long
            logger.info(
                f"[request_id={request_id}] Request body of {path}:\n{json.dumps(json_data, ensure_ascii=False, indent=2)}"
            )
        except json.JSONDecodeError:
            # Not valid JSON, log as plain text
            logger.info(
                f"[request_id={request_id}] Request body of {path}:\n{body_str}"
            )

    except UnicodeDecodeError:
        # Binary data
        logger.info(
            f"[request_id={request_id}] Request body of {path}: <binary_data: {len(request_body)} bytes>"
        )


def serialize_request_without_media(request):
    data = request.model_dump()

    if "messages" in data:
        for message in data["messages"]:
            if "content" in message and isinstance(message["content"], list):
                filtered_content = []
                for content_part in message["content"]:
                    if isinstance(content_part, dict):
                        content_type = content_part.get("type", "")
                        if content_type not in ["audio_url", "image_url", "video_url"]:
                            filtered_content.append(content_part)
                        else:
                            filtered_content.append(
                                {"type": content_type, "url": "[FAKE_MEDIA_CONTENT]"}
                            )
                    else:
                        filtered_content.append(content_part)
                message["content"] = filtered_content

    return data


def log_request():
    raw_create_chat_completion = OpenAIServingChat.create_chat_completion
    raw_create_completion = OpenAIServingCompletion.create_completion

    async def create_chat_completion(
        self,
        request: ChatCompletionRequest,
        raw_request: Optional[Request] = None,
    ):
        request_id = self._base_request_id(raw_request, request.request_id)
        path = raw_request.url.path
        logger.info(
            f"[request_id={request_id}] Request body of {path}:\n{json.dumps(serialize_request_without_media(request), ensure_ascii=False, indent=2)}"
        )
        return await raw_create_chat_completion(self, request, raw_request)

    async def create_completion(
        self,
        request: CompletionRequest,
        raw_request: Optional[Request] = None,
    ):
        request_id = self._base_request_id(raw_request, request.request_id)
        path = raw_request.url.path
        logger.info(
            f"[request_id={request_id}] Request body of {path}:\n{json.dumps(serialize_request_without_media(request), ensure_ascii=False, indent=2)}"
        )
        return await raw_create_completion(self, request, raw_request)

    OpenAIServingChat.create_chat_completion = create_chat_completion
    OpenAIServingCompletion.create_completion = create_completion


def _log_streaming_response_with_context(
    request_id: str, path: str, response, response_body: list
) -> None:
    """Log streaming response with request context."""
    if not _is_completion_endpoint(path):
        return

    from starlette.concurrency import iterate_in_threadpool

    sse_decoder = SSEDecoder()
    chunk_count = 0

    def buffered_iterator():
        nonlocal chunk_count

        for chunk in response_body:
            chunk_count += 1
            yield chunk

            # Parse SSE events from chunk
            events = sse_decoder.decode_chunk(chunk)

            for event in events:
                if event["type"] == "data":
                    content = sse_decoder.extract_content(event["data"])
                    sse_decoder.add_content(content)
                    if chunk_count % 10 == 0:
                        logger.info(
                            f"[request_id={request_id}] Streaming response of {path}: {chunk_count}-th content={repr(content)}"
                        )
                elif event["type"] == "done":
                    # Log complete content when done
                    full_content = sse_decoder.get_complete_content()
                    if len(full_content) > 1024:
                        full_content = (
                            full_content[:128] + "...[omitted]..." + full_content[-128:]
                        )
                    logger.info(
                        f"[request_id={request_id}] Streaming response of {path} completed (chunks={chunk_count}): full_content={repr(full_content)}"
                    )
                    return

    response.body_iterator = iterate_in_threadpool(buffered_iterator())
    logger.info(
        f"[request_id={request_id}] Streaming response of {path} started: chunks=%d",
        len(response_body),
    )


def _log_non_streaming_response_with_context(
    request_id: str, path: str, response_body: list
) -> None:
    """Log non-streaming response with request context."""
    if not _is_completion_endpoint(path):
        return

    try:
        decoded_body = response_body[0].decode()
        logger.info(
            f"[request_id={request_id}] Non-streaming response of {path}:\n{json.dumps(json.loads(decoded_body), ensure_ascii=False, indent=2)}"
        )
    except UnicodeDecodeError:
        logger.info(
            f"[request_id={request_id}] Non-streaming response of {path}: <binary_data>"
        )


async def log_response(request: Request, call_next):
    path = request.url.path
    response = await call_next(request)
    response_body = [section async for section in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(response_body))
    # Check if this is a streaming response by looking at content-type
    response_request_id = response.headers.get("x-request-id", "")
    content_type = response.headers.get("content-type", "")
    is_streaming = content_type == "text/event-stream; charset=utf-8"

    # Log response body based on type
    if not response_body:
        logger.info(
            f"[request_id={response_request_id}] Response body of {path}: <empty>"
        )
    elif is_streaming:
        _log_streaming_response_with_context(
            response_request_id, path, response, response_body
        )
    else:
        _log_non_streaming_response_with_context(
            response_request_id, path, response_body
        )
    return response


# HINT: patch `FastAPI.middleware` to replace vllm's log_response middleware with our customized version
def replace_log_response_middleware():
    def patched_middleware(self, middleware_type):
        def decorator(func):
            if func.__name__ == "log_response":
                func = log_response
            self.add_middleware(BaseHTTPMiddleware, dispatch=func)
            return func

        return decorator

    FastAPI.middleware = patched_middleware


def register_log_request_response_plugin():
    """Register the log request response plugin."""
    add_log_request_response_env_vars()
    if envs.VLLM_DEBUG_LOG_API_SERVER_REQUEST_RESPONSE:
        warnings.warn(
            "vLLM cli args `--disable-log-requests` is recommended to be turned off"
        )
        log_request()
        if (
            hasattr(envs, "VLLM_DEBUG_LOG_API_SERVER_RESPONSE")
            and envs.VLLM_DEBUG_LOG_API_SERVER_RESPONSE
        ):
            warnings.warn(
                "Instead of using vLLM's `log_response` middleware, a customized version is used to enable full-featured response logging"
            )
            replace_log_response_middleware()
        else:
            warnings.warn(
                "We highly recommend to set the log_response middleware in vLLM cli args: `--middleware vllm_kubernetes_plugin.middleware.log_response`"
            )
