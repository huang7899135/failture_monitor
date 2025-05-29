# Use an official Python runtime as a parent image
FROM dockerpull.cn/python:3.11

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for production
# RUN apt-get update && apt-get install -y \
#     gcc \
#     pkg-config \
#     libmariadb-dev \
#     && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Create log and celery directories with proper permissions
RUN mkdir -p /app/log /app/celery

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set ownership and permissions for directories
RUN chown -R appuser:appuser /app
RUN chmod -R 755 /app/log
RUN chmod -R 777 /app/celery

# Make port 8090 available to the world outside this container
EXPOSE 8090

# Define environment variable for production
ENV FLASK_APP=web_app.py
ENV FLASK_ENV=production
ENV APP_ENV=prod
ENV PYTHONPATH=/app

# USER appuser

# Run gunicorn when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:8090", "--workers", "4", "--timeout", "120", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "50", "web_app:app"]
