# from vllm.entrypoints.openai.protocol import ChatCompletionRequest, CompletionRequest
import json
import warnings

import pydantic
import vllm.envs as envs
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from vllm.entrypoints.openai.api_server import logger


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


# TODO: optimize log output for long streaming response
def _log_streaming_response(request_id: str, path: str, response_body: list) -> None:
    """Log streaming response with robust SSE parsing."""
    sse_decoder = SSEDecoder()
    chunk_count = 0

    for chunk in response_body:
        chunk_count += 1

        # Parse SSE events from chunk
        events = sse_decoder.decode_chunk(chunk)

        for event in events:
            if event["type"] == "data":
                content = sse_decoder.extract_content(event["data"])
                sse_decoder.add_content(content)
                if chunk_count % 10 == 0:
                    logger.info(f"[request_id={request_id}] Streaming response of {path}: {chunk_count}-th content='{content}'")
            elif event["type"] == "done":
                # Log complete content when done
                full_content = sse_decoder.get_complete_content()
                if full_content:
                    # Truncate if too long
                    if len(full_content) > 2048:
                        full_content = full_content[:2048] + "...[truncated]"
                    logger.info(f"[request_id={request_id}] Streaming response of {path} completed: full_content='{full_content}', chunks={chunk_count}")
                else:
                    logger.info(f"[request_id={request_id}] Streaming response of {path} completed: no_content, chunks={chunk_count}")
                return
    logger.info(f"[request_id={request_id}] Streaming response of {path} ended")


def _log_non_streaming_response(request_id: str, path: str, response_body: list) -> None:
    """Log non-streaming response."""
    try:
        decoded_body = response_body[0].decode()
        logger.info(f"[request_id={request_id}] Non-streaming response of {path}:\n{json.dumps(json.loads(decoded_body), ensure_ascii=False, indent=2)}")
    except UnicodeDecodeError:
        logger.info(f"[request_id={request_id}] Non-streaming response of {path}: <binary_data>")


def _is_completion_endpoint(path: str) -> bool:
    """Check if the request is for a completion endpoint."""
    return path in ["/v1/chat/completions", "/v1/completions"]


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
            logger.info(f"[request_id={request_id}] Request body of {path}:\n{json.dumps(json_data, ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError:
            # Not valid JSON, log as plain text
            logger.info(f"[request_id={request_id}] Request body of {path}:\n{body_str}")

    except UnicodeDecodeError:
        # Binary data
        logger.info(f"[request_id={request_id}] Request body of {path}: <binary_data: {len(request_body)} bytes>")


class LogRequestResponseMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get the request path
        path = scope.get("path", "")

        # Create a custom receive function to capture the request body
        request_body = b""
        request_complete = False

        async def receive_wrapper() -> Message:
            nonlocal request_body, request_complete
            message = await receive()
            request_id = message.get("headers", {}).get(b"x-request-id", b"").decode()

            if message["type"] == "http.request":
                # Accumulate request body data
                chunk = message.get("body", b"")
                request_body += chunk

                # Check if this is the last chunk
                if not message.get("more_body", False):
                    request_complete = True
                    _log_request_body(request_id, path, request_body)

            return message

        headers_dict = {}
        response_request_id = ""
        response_body = []

        async def send_wrapper(message: Message) -> None:
            nonlocal headers_dict, response_request_id, response_body
            if message["type"] == "http.response.start":
                # Store headers as a list of tuples
                headers_list = message.get("headers", [])
                headers_dict = dict(headers_list)
                response_request_id = headers_dict.get(b"x-request-id", b"").decode()
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_body.append(body)
            await send(message)

        await self.app(scope, receive_wrapper, send_wrapper)

        if not response_body:
            logger.info(f"[request_id={response_request_id}] Response body of {path}: <empty>")
        else:
            content_type = headers_dict.get(b"content-type", b"").decode()
            is_streaming = content_type == "text/event-stream; charset=utf-8"
            logger.info(f"[request_id={response_request_id}] Response pattern of {path} is {'streaming' if is_streaming else 'non-streaming'}")

            if is_streaming:
                _log_streaming_response(response_request_id, path, response_body)
            else:
                _log_non_streaming_response(response_request_id, path, response_body)



def register_log_request_response_plugin():
    """Register the log request response plugin."""
    if not envs.VLLM_DEBUG_LOG_API_SERVER_RESPONSE:
        warnings.warn(
            "vllm-kubernetes-plugin's `LogRequestResponseMiddleware` is somehow duplicated when VLLM_DEBUG_LOG_API_SERVER_RESPONSE is set"
        )
        return

    # TODO: dynamic change vllm cli args `middleware` according to env var `VLLM_LOG_REQUEST_RESPONSE_MIDDLEWARE_ENABLED`
    logger.info(
        "Please register log request response plugin by adding middleware in vllm cli args: `--middleware vllm_kubernetes_plugin.middleware.LogRequestResponseMiddleware`"
    )
