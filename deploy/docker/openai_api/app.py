import base64
import json
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="PaddleOCR OpenAI Compatible API",
    description="A lightweight OpenAI-compatible proxy for PaddleOCR HubServing.",
    version="1.0.0",
)

OCR_SERVER_URL = os.getenv("OCR_SERVER_URL", "http://127.0.0.1:8868/predict/ocr_system")
REQUEST_TIMEOUT = int(os.getenv("OCR_REQUEST_TIMEOUT", "60"))


def _strip_data_url(base64_data: str) -> str:
    if base64_data.startswith("data:"):
        return base64_data.split(",", 1)[1]
    return base64_data


def _decode_image_source(payload: Dict[str, Any]) -> List[str]:
    images = []

    if "images" in payload and isinstance(payload["images"], list):
        for image in payload["images"]:
            if isinstance(image, str):
                images.append(_strip_data_url(image))
    elif "image_base64" in payload and isinstance(payload["image_base64"], str):
        images.append(_strip_data_url(payload["image_base64"]))
    elif "image_url" in payload and isinstance(payload["image_url"], str):
        response = requests.get(payload["image_url"], timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        encoded = base64.b64encode(response.content).decode("utf-8")
        images.append(encoded)
    elif "messages" in payload and isinstance(payload["messages"], list):
        for message in payload["messages"]:
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                if re.search(r"^data:image|^[A-Za-z0-9+/=\\s]+$", content.strip()):
                    images.append(_strip_data_url(content.strip()))
    if not images:
        raise ValueError("No valid image payload found. Provide `images`, `image_base64`, or `image_url`.")
    return images


def _build_ocr_request(images: List[str]) -> Dict[str, Any]:
    return {"images": images}


def _request_ocr(images: List[str]) -> Any:
    response = requests.post(
        OCR_SERVER_URL,
        json=_build_ocr_request(images),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _normalize_result(results: Any) -> Dict[str, Any]:
    if isinstance(results, dict) and "results" in results:
        results_list = results["results"]
    else:
        results_list = results
    if not isinstance(results_list, list):
        raise ValueError("Unexpected OCR response format")
    if len(results_list) == 0:
        return {"text": "", "raw": results}
    first_result = results_list[0]
    if isinstance(first_result, dict) and "text" in first_result:
        return first_result
    return {"text": json.dumps(first_result, ensure_ascii=False), "raw": first_result}


def _format_choice_text(result: Dict[str, Any]) -> str:
    if not result:
        return ""
    if "text" in result and isinstance(result["text"], str):
        return result["text"]

    if isinstance(result.get("raw"), dict):
        try:
            return json.dumps(result["raw"], ensure_ascii=False, indent=2)
        except Exception:
            return str(result["raw"])

    return json.dumps(result, ensure_ascii=False)


def _build_openai_response(model: str, result: Dict[str, Any]) -> Dict[str, Any]:
    content = _format_choice_text(result)
    return {
        "id": f"paddleocr-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "healthy"}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    payload = await request.json()
    model = payload.get("model", "paddleocr-openai")
    try:
        images = _decode_image_source(payload)
        ocr_response = _request_ocr(images)
        normalized = _normalize_result(ocr_response)
        result = _build_openai_response(model, normalized)
        return JSONResponse(status_code=200, content=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except requests.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"OCR backend HTTP error: {exc}")
    except requests.RequestException as exc:
        raise HTTPException(status_code=504, detail=f"OCR backend request failed: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}")


@app.post("/v1/completions")
async def completions(request: Request) -> JSONResponse:
    return await chat_completions(request)
