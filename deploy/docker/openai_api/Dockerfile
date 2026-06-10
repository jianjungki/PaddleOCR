FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /PaddleOCR

COPY . /PaddleOCR

RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
RUN python -m pip install paddlehub==2.1.0 fastapi uvicorn[standard] requests -i https://mirrors.aliyun.com/pypi/simple/
RUN python -m pip install -r requirements.txt
RUN chmod +x /PaddleOCR/deploy/docker/openai_api/entrypoint.sh

EXPOSE 8080
EXPOSE 8868

ENTRYPOINT ["/PaddleOCR/deploy/docker/openai_api/entrypoint.sh"]
