FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    jupyter_kernel_gateway==2.5.0 \
    jupyter_client==8.6.0 \
    ipykernel==6.28.0 \
    websockets==12.0 \
    duckduckgo-search==8.0.2

# Create a non-root user
# RUN useradd -m -s /bin/bash jupyter
# USER jupyter
WORKDIR /home/jupyter

# Copy tools and kernel initialization
# COPY --chown=jupyter:jupyter tools.py /home/jupyter/
# COPY --chown=jupyter:jupyter kernel_init.py /home/jupyter/

COPY tools.py /home/jupyter/
COPY kernel_init.py /home/jupyter/

# Create kernel configuration
RUN mkdir -p /home/jupyter/.jupyter/kernels/python3
# COPY --chown=jupyter:jupyter kernel.json /home/jupyter/.jupyter/kernels/python3/
ENV JUPYTER_PATH=/home/jupyter/.jupyter
COPY kernel.json /home/jupyter/.jupyter/kernels/python3/


# Expose the Jupyter Kernel Gateway port
EXPOSE 8888

# Start Jupyter Kernel Gateway
CMD ["jupyter", "kernelgateway", "--KernelGatewayApp.ip=0.0.0.0", "--KernelGatewayApp.port=8888", "--KernelGatewayApp.token=''", "--KernelGatewayApp.allow_origin='*'"]
# CMD ["jupyter", "kernelgateway", "--KernelGatewayApp.ip=0.0.0.0", "--KernelGatewayApp.port=8888", "--KernelGatewayApp.token=''"] 