FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml requirements.txt README.md ./
COPY src ./src
COPY rank.py ./rank.py

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["python", "rank.py"]
