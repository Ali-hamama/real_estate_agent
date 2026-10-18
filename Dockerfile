FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

COPY pyproject.toml requirements.txt ./
COPY app ./app
COPY scripts ./scripts
COPY data/__init__.py ./data/
COPY data/scripts ./data/scripts
RUN python -m pip install -r requirements.txt

CMD ["sleep", "infinity"]
