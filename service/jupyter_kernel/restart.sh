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

# Run the container
docker run -d \
    --name jupyter-kernel-gateway \
    -p 8888:8888 \
    jupyter-kernel-gateway

echo "Jupyter Kernel Gateway is running on http://localhost:8888" 