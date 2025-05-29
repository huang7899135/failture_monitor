#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Output commands being executed
# set -x

echo "Building and starting services (app, db, redis, celery)..."
docker-compose up -d --build

# Wait for the database to be ready.
# A more robust solution would involve polling the DB port or using a tool like wait-for-it.sh or
# checking the health status via docker inspect.
echo "Waiting for database service to initialize (approx. 15-30 seconds)..."
sleep 20 # Increased sleep duration slightly for more reliability

# Check if the db service is healthy (optional, but good practice)
# This requires the service name 'db' to match what's in docker-compose.yml
# And that the healthcheck in docker-compose.yml is reliable.
# max_attempts=10
# attempt_num=1
# until [ "$(docker inspect -f '{{.State.Health.Status}}' $(docker-compose ps -q db))" == "healthy" ]; do
# if [ "$attempt_num" -eq "$max_attempts" ]; then
# echo "Database health check failed after $max_attempts attempts."
# exit 1
# fi
# echo "Waiting for database to be healthy (attempt $attempt_num/$max_attempts)..."
# sleep 5
# attempt_num=$((attempt_num+1))
# done
# echo "Database is healthy."


echo "Running database schema initialization (init_db.py)..."
docker-compose exec app python init_db.py

echo ""
echo "Deployment complete!"
echo "--------------------------------------------------"
echo "Access the web application at: http://localhost:8090"
echo "MySQL database is running on port 3306 (host)."
echo "Redis is running on port 6379 (host)."
echo "Celery worker and beat scheduler are running in the 'celery' service."
echo "You can view logs using: docker-compose logs -f"
echo "To stop services: docker-compose down"
echo "--------------------------------------------------"
