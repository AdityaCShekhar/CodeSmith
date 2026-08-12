FROM python:3.11-slim

WORKDIR /app

# Repository tools execute inside this container, so install their command-line
# dependencies rather than relying on binaries available on the host.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Install the packaged application and its dependencies.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Use the installed console entry point from any mounted working directory.
ENTRYPOINT ["codesmith"]
