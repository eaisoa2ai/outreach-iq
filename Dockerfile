# --- Builder: resolve and install dependencies into site-packages ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

# --- Runtime: copy only what's needed to run, drop root ---
FROM python:3.11-slim

WORKDIR /app

RUN useradd --create-home --uid 1000 outreachiq
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY main.py ./
COPY config ./config
COPY src ./src
COPY scripts ./scripts
COPY ui ./ui
COPY data/seed ./data/seed

RUN mkdir -p /app/logs /app/outbox /app/data \
    && chown -R outreachiq:outreachiq /app

USER outreachiq
ENV PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:///./data/outreachiq.sqlite

EXPOSE 7860

# Default: launch the dashboard. Override for the CLI, e.g.:
#   docker run --env-file .env outreachiq python main.py --customer-id C100
CMD ["python", "ui/app.py"]
