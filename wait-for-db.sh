#!/bin/bash
# filepath: /bonpreu-data-engineer-demo/wait-for-db.sh

set -e

host="$1"
port="$2"

echo "Waiting for MySQL at $host:$port..."
while ! nc -z "$host" "$port"; do
  sleep 2
done

echo "MySQL available at $host:$port. Running ETL..."
exec "${@:3}"