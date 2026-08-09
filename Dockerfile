FROM python:3.11-slim

WORKDIR /app

# Install the packaged application and its dependencies.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Use the installed console entry point from any mounted working directory.
ENTRYPOINT ["codesmith"]
