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
# Pin BLAS thread counts to 1 so BM25 float-reduction order (and the generated
# submission.csv) is byte-identical regardless of the host's CPU count. Verified
# identical output at --cpus=2 and --cpus=4; without this a many-core host yields
# a different (still deterministic) ranking.
ENV OPENBLAS_NUM_THREADS=1
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt ./

# Keep third-party dependencies in a cacheable layer so source-only changes do
# not redownload/reinstall NumPy and the BM25 packages on every image rebuild.
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY models ./models
COPY rank.py ./rank.py

# Drop root (audit-v2 hardening): the entrypoint only reads bundled code and
# writes to the path passed via --out (typically a mounted volume), so an
# unprivileged UID suffices. chown /app keeps an in-container --out path writable.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "rank.py"]
