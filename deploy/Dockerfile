# The search and MCP server: the SafetyPage engine at one commit, with Lectern's tool
# descriptions and name (library/). It serves one sealed snapshot, mounted read-only at /snapshot.

FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
ARG ENGINE=35e5443254c45a0037c8aa2e5854970c6c1b14ed
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/app/.venv
RUN git clone https://github.com/Noah-Airmet/safetypage /src && git -C /src checkout ${ENGINE}
WORKDIR /src
RUN uv sync --locked --no-dev --group server --group search --no-editable

FROM python:3.13-slim
COPY --from=build /app/.venv /app/.venv
COPY library /app/library
ENV SAFETYPAGE_SNAPSHOT=/snapshot \
    SAFETYPAGE_SURFACES=/app/library \
    SAFETYPAGE_OPS_DB=/ops/ops.sqlite \
    PATH=/app/.venv/bin:$PATH
RUN mkdir -p /ops && chown nobody /ops
USER nobody
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["python", "-m", "safetypage.server", "--host", "0.0.0.0", "--port", "8000"]
