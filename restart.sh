#!/bin/bash

# file: restart.sh

# Usage: ./restart.sh [test|prod|all]

# Define server addresses
TEST_SERVER="david@142.132.188.109"
PROD_SERVER="david@5.161.179.223"

# Define the remote directory where the script is located
REMOTE_DIR="v2trading"

# Check for argument
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 [test|prod|all]"
  exit 1
fi

# Function to restart a server
restart_server() {
  local server=$1
  echo "Connecting to $server to restart the Python app..."
  ssh -t $server "cd $REMOTE_DIR && . ~/.bashrc && ./run.sh restart"  # Sourcing .bashrc here
  echo "Operation completed on $server."
}

# Select the server based on the input argument
case $1 in
  test)
    restart_server $TEST_SERVER
    ;;
  prod)
    restart_server $PROD_SERVER
    ;;
  all)
    restart_server $TEST_SERVER
    restart_server $PROD_SERVER
    ;;
  *)
    echo "Invalid argument: $1. Use 'test', 'prod', or 'all'."
    exit 1
    ;;
esac

