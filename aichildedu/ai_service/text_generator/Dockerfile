FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy service code
COPY . /app/

# Expose port
EXPOSE 8010

# Run service command
CMD ["uvicorn", "aichildedu.ai_service.text_generator.main:app", "--host", "0.0.0.0", "--port", "8010"] 