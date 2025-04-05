# Use an official Python image as base
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first to install dependencies
COPY requirements.txt .

# Set up virtual environment and install dependencies
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

# Set environment path for venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy all other files
COPY . .

# Expose port (optional)
EXPOSE 8080

# Command to run your bot
CMD ["python", "mallu.py"]
