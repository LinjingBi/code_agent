from typing import Dict, Optional
import websockets
import json
import asyncio
from fastapi import Depends
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class JupyterKernelManager:
    def __init__(self, kernel_gateway_url: str = "http://localhost:8888"):
        self.kernel_gateway_url = kernel_gateway_url
        self.kernel_id: Optional[str] = None
        self.ws_url: Optional[str] = None

    async def create_kernel(self):
        """Create a new kernel and get its WebSocket URL."""
        try:
            async with websockets.connect(f"{self.kernel_gateway_url}/api/kernels") as ws:
                # Create new kernel
                await ws.send(json.dumps({
                    "type": "create_kernel",
                    "kernel": {
                        "name": "python3"
                    }
                }))
                response = await ws.recv()
                kernel_info = json.loads(response)
                self.kernel_id = kernel_info["id"]
                self.ws_url = f"{self.kernel_gateway_url}/api/kernels/{self.kernel_id}/channels"
                logger.info(f"Created new kernel with ID: {self.kernel_id}")
                return self.kernel_id
        except Exception as e:
            logger.error(f"Error creating kernel: {str(e)}")
            raise

    async def execute_code(self, code: str) -> Dict:
        """Execute code in the kernel and return the result."""
        if not self.ws_url:
            raise RuntimeError("No active kernel. Call create_kernel() first.")

        try:
            async with websockets.connect(self.ws_url) as ws:
                # Send code execution request
                await ws.send(json.dumps({
                    "header": {
                        "msg_type": "execute_request",
                        "msg_id": "1"
                    },
                    "content": {
                        "code": code,
                        "silent": False,
                        "store_history": True,
                        "user_expressions": {},
                        "allow_stdin": False
                    }
                }))

                # Collect all messages until execution is complete
                output = []
                error = None
                while True:
                    msg = await ws.recv()
                    msg_data = json.loads(msg)
                    msg_type = msg_data["header"]["msg_type"]

                    if msg_type == "stream":
                        output.append(msg_data["content"]["text"])
                    elif msg_type == "error":
                        error = f"{msg_data['content']['ename']}: {msg_data['content']['evalue']}"
                    elif msg_type == "execute_reply":
                        break

                return {
                    "output": "\n".join(output) if output else "",
                    "error": error,
                    "exit_code": 1 if error else 0
                }
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            raise

    async def shutdown_kernel(self):
        """Shutdown the current kernel."""
        if not self.kernel_id:
            return

        try:
            async with websockets.connect(f"{self.kernel_gateway_url}/api/kernels/{self.kernel_id}") as ws:
                await ws.send(json.dumps({
                    "type": "shutdown_kernel"
                }))
                logger.info(f"Shutdown kernel with ID: {self.kernel_id}")
                self.kernel_id = None
                self.ws_url = None
        except Exception as e:
            logger.error(f"Error shutting down kernel: {str(e)}")
            raise

@asynccontextmanager
async def get_kernel():
    """Dependency for FastAPI to manage kernel lifecycle."""
    kernel_manager = JupyterKernelManager()
    try:
        await kernel_manager.create_kernel()
        yield kernel_manager
    finally:
        await kernel_manager.shutdown_kernel() 