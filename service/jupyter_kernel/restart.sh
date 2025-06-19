#!/bin/bash

# Ensure all required files exist
required_files=("Dockerfile" "tools.py" "kernel_init.py" "kernel.json")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Error: Required file $file is missing"
        exit 1
    fi
done

# Stop and remove existing container if it exists
docker stop jupyter-kernel-gateway 2>/dev/null
docker rm jupyter-kernel-gateway 2>/dev/null

# Build the Docker image
docker build -t jupyter-kernel-gateway .

# Run the container with resource limits
docker run -d \
    --name jupyter-kernel-gateway \
    -p 8888:8888 \
    --memory=2g \
    --cpus=1.0 \
    --shm-size=256m \
    jupyter-kernel-gateway

# Wait for the server to start
echo "Waiting for Jupyter Kernel Gateway to start..."
sleep 5

# Extract the token from the logs
token=$(docker logs jupyter-kernel-gateway 2>&1 | grep -o 'token=[^&\"]*' | head -n1 | cut -d'=' -f2)

if [ -n "$token" ]; then
    echo "$token" > jupyter_token.txt
    echo "Jupyter token written to jupyter_token.txt: $token"
else
    echo "Could not find Jupyter token in logs."
fi

echo "Jupyter Kernel Gateway is running on ws://localhost:8888" 