# The build: Lectern's scripts on the SafetyPage engine, pinned to one commit.
#
#   docker build -f build/Dockerfile -t lectern-build .
#   docker run --rm -v /data:/host/data:ro -v /data/lectern:/work lectern-build \
#     python build/ingest.py --shelf shelf/volumes.jsonl --prefix /host \
#       --catalog /host/data/research-corpus/manifests/catalog.sqlite --work /work
#   docker run --rm -v /data/lectern:/work lectern-build python build/snapshot.py --work /work <id>

FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
ARG ENGINE=a2a9ff63df9bb77b47799513e446765d995837d7
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/engine/.venv
RUN git clone https://github.com/Noah-Airmet/safetypage /engine && git -C /engine checkout ${ENGINE}
WORKDIR /engine
RUN uv sync --locked --no-dev --group ingest --group build --group search --group server
ENV PATH=/engine/.venv/bin:$PATH
WORKDIR /lectern
COPY build ./build
COPY shelf ./shelf
COPY library ./library
