FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Pin the hash seed so the bm25s vocabulary ordering (and therefore float
# accumulation in BM25 scoring) is identical across runs -> byte-stable output.
# Rank order is already reproducible regardless; this makes the CSV bit-identical.
ENV PYTHONHASHSEED=0

WORKDIR /app

COPY pyproject.toml requirements.txt README.md ./
COPY src ./src
COPY rank.py ./rank.py

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["python", "rank.py"]
