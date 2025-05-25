#!/usr/bin/env sh
# Defining ports to shutdown
ports="6274"

# Shutting down services
for port in $ports; do
  echo "\nChecking port $port"
  lsof -i :$port
  PID=$(lsof -ti :$port)
  if [ -n "$PID" ]; then
    echo "Killing process $PID on port $port"
    kill "$PID"
  else
    echo "No process found on port $port"
  fi
done
