# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY BackEnd/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for search engine (optional)
RUN pip install --no-cache-dir \
    faiss-cpu \
    sentence-transformers \
    flask \
    flask-socketio \
    python-socketio

# Copy application code
COPY BackEnd/ ./BackEnd/
COPY FrontEnd/ ./FrontEnd/

# Create necessary directories
RUN mkdir -p /app/campaigns \
    /app/search_index \
    /app/BackEnd/prompts \
    /app/srd_story_cycle

# Copy SRD content if it exists
COPY srd_story_cycle/ ./srd_story_cycle 

# Set environment variables
ENV FLASK_APP=BackEnd/main.py
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
WORKDIR /app/BackEnd
CMD ["python", "main.py"]