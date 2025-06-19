from typing import Dict, Optional
import websocket
import json
import httpx
from utils.logging import setup_logger
import time

logger = setup_logger(__name__)

class JupyterKernelManager:
    def __init__(self, kernel_gateway_host: str = "localhost:8888"):
        self.kernel_gateway_host = kernel_gateway_host
        self.kernel_id: Optional[str] = None
        self.ws_url: Optional[str] = None

    def create_kernel(self):
        """Create a new kernel and get its WebSocket URL."""
        url = f"http://{self.kernel_gateway_host}/api/kernels"
        with httpx.Client() as client:
            response = client.post(url)
            response.raise_for_status()
            kernel_info = response.json()
            self.kernel_id = kernel_info["id"]
            self.ws_url = f"ws://{self.kernel_gateway_host}/api/kernels/{self.kernel_id}/channels"
            logger.info(f"Created new kernel with ID: {self.kernel_id}")
            
            # Wait for kernel to be ready (idle state)
            status_url = f"http://{self.kernel_gateway_host}/api/kernels/{self.kernel_id}"
            max_wait = 30  # Maximum wait time in seconds
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    status_response = client.get(status_url)
                    status_response.raise_for_status()
                    kernel_status = status_response.json()
                    logger.info(kernel_status)
                    execution_state = kernel_status.get('execution_state', 'unknown')
                    logger.info(f"Kernel status: {execution_state}")
                    
                    if execution_state == 'idle':
                        logger.info("Kernel is ready!")
                        break
                    elif execution_state == 'dead':
                        raise Exception("Kernel failed to start")
                    
                    time.sleep(3)
                    wait_time += 1
                except Exception as e:
                    logger.warning(f"Could not check kernel status: {e}")
                    time.sleep(1)
                    wait_time += 1
            
            if wait_time >= max_wait:
                raise Exception("Kernel did not become ready within timeout")
            
            return self.kernel_id

    def execute_code(self, code: str) -> Dict:
        """Execute code in the kernel and return the result."""
        if not self.ws_url:
            raise RuntimeError("No active kernel. Call create_kernel() first.")
        
        logger.info(f'Jupyter kernel executing code: {code}')
        logger.info(f'Connecting to WebSocket: {self.ws_url}')
        
        try:
            # Create WebSocket connection
            ws = websocket.create_connection(self.ws_url, timeout=30)
            logger.info('WebSocket connection established')
            
            # Send code execution request
            message = {
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
            }
            logger.info(f'Sending message: {json.dumps(message)}')
            ws.send(json.dumps(message))
            logger.info('Message sent successfully')

            # Collect all messages until execution is complete
            output = []
            error = None
            message_count = 0
            while True:
                logger.info(f'Waiting for message {message_count + 1}...')
                msg = ws.recv()
                message_count += 1
                logger.info(f'Received message {message_count}: {msg[:100]}...')
                
                msg_data = json.loads(msg)
                msg_type = msg_data["header"]["msg_type"]
                logger.info(f'Message type: {msg_type}')

                if msg_type == "stream":
                    output.append(msg_data["content"]["text"])
                elif msg_type == "error":
                    error = f"{msg_data['content']['ename']}: {msg_data['content']['evalue']}"
                elif msg_type == "execute_reply":
                    logger.info('Received execute_reply, breaking')
                    break

            logger.info(f'Code execution completed. Output: {len(output)} lines, Error: {error}')
            return {
                "output": "\n".join(output) if output else "",
                "error": error,
                "exit_code": 1 if error else 0
            }
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            raise
        finally:
            try:
                ws.close()
                logger.info('WebSocket connection closed')
            except:
                pass

    def shutdown_kernel(self):
        """Shutdown the current kernel."""
        if not self.kernel_id:
            return

        try:
            url = f"http://{self.kernel_gateway_host}/api/kernels/{self.kernel_id}"
            with httpx.Client() as client:
                client.delete(url)
            logger.info(f"Shutdown kernel with ID: {self.kernel_id}")
            self.kernel_id = None
            self.ws_url = None
        except Exception as e:
            logger.error(f"Error shutting down kernel: {str(e)}")
            raise

def get_kernel():
    """Synchronous dependency for FastAPI to manage kernel lifecycle."""
    kernel_manager = JupyterKernelManager()
    kernel_manager.create_kernel()
    try:
        yield kernel_manager
    finally:
        kernel_manager.shutdown_kernel()