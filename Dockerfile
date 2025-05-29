# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 8090 available to the world outside this container
EXPOSE 8090

# Define environment variable
ENV FLASK_APP web_app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 8090
# ENV APP_ENV dev # This is already set in main.py, but good to be explicit if needed for web_app.py directly

# Run web_app.py when the container launches
CMD ["flask", "run"]
