#!/bin/sh

# Start the Django development server
echo "Starting Django server..."
python airport_simulator/manage.py runserver 0.0.0.0:8000 &

# Start the Kafka consumer
echo "Starting Kafka consumer..."
python airport_simulator/manage.py kafka_consumer &

wait -n

exit $?