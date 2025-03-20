FROM python:3.10-slim

WORKDIR /app

# Installing dependencies
RUN apt-get update && apt-get install -y git

# Copying files
COPY requirements.txt .
COPY scripts/analysis_script.py ./scripts/
COPY system_prompt.md .

# Installing Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Entry point for Action
ENTRYPOINT ["python", "/app/scripts/analysis_script.py"]