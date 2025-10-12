#!/bin/sh
# wait-for-zookeeper.sh
# Wait for Zookeeper to start and be ready before starting Kafka

set -e

host="$1"
port="$2"
shift 2
cmd="$@"

until nc -z "$host" "$port"; do
  >&2 echo "Zookeeper is unavailable - sleeping"
  sleep 1
done

>&2 echo "Zookeeper is up - executing command"
exec $cmd