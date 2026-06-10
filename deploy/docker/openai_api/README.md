# PaddleOCR OpenAI-Compatible Docker Image

This image builds a PaddleOCR HubServing backend and exposes a lightweight OpenAI-compatible proxy.

## Build

```bash
docker build -t paddleocr-openai -f deploy/docker/openai_api/Dockerfile .
```

## Run

```bash
docker run --rm -p 8080:8080 paddleocr-openai
```

## Example Request

```bash
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/sample.jpg"}'
```

The service proxies requests to the PaddleOCR HubServing backend on `http://127.0.0.1:8868/predict/ocr_system`.
