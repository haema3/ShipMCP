FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SHIP_MCP_TRANSPORT=streamable-http \
    SHIP_MCP_HOST=0.0.0.0 \
    SHIP_MCP_PORT=8000 \
    SHIP_MCP_DB_PATH=/data/ship_terms.db

WORKDIR /app

COPY pyproject.toml README.md ./
COPY ship_mcp ./ship_mcp

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir . \
    && useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

EXPOSE 8000

VOLUME ["/data"]

USER appuser

CMD ["sh", "-c", "ship-mcp --transport ${SHIP_MCP_TRANSPORT} --host ${SHIP_MCP_HOST} --port ${SHIP_MCP_PORT} --db-path ${SHIP_MCP_DB_PATH}"]