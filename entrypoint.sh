#!/bin/bash

# Print the arguments for debugging (optional)
echo "Running with arguments: $@"

# Run the Python script with the arguments provided from the command line
exec python app/main.py "$@"