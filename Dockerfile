FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY cli.py llm.py tools.py init.py ./

# Make scripts executable
RUN chmod +x cli.py init.py

# Set the entry point
ENTRYPOINT ["python3", "init.py"]
