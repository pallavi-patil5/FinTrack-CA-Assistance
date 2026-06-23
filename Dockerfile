FROM python:3.11-slim-bookworm

WORKDIR /app

# Install Python dependencies
# Uses opencv-python-headless to avoid needing system libGL/libSM
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure runtime directories exist
RUN mkdir -p uploads .EasyOCR

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
