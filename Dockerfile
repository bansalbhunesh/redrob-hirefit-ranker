# Digest-pinned base (audit-v2 hardening): a July rebuild resolves the exact
# image the byte-identical reproduction was verified on, not whatever
# python:3.11-slim points to that week.
FROM python:3.11-slim@sha256:ef442c44cde6d7aec39ae63dad1ced44fa7290790d68c028686cdd2e31a76a95

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

# Deps come exact-pinned from requirements.txt; the package itself installs
# --no-deps so pyproject's dev-friendly ranges can never widen the image.
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --no-deps -e .

ENTRYPOINT ["python", "rank.py"]
