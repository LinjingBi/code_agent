import grpc
from . import code_executor_pb2
from . import code_executor_pb2_grpc
from utils.logging import setup_logger

logger = setup_logger(__name__)

class CodeExecutorClient:
    def __init__(self, host: str = 'localhost', port: int = 50051):
        """Initialize the code executor client.
        
        Args:
            host: The host where the code executor service is running
            port: The port where the code executor service is running
        """
        self.address = f'{host}:{port}'
        self._get_channel()
    
    def _get_channel(self):
        if not hasattr(self, 'channel') or self.channel._channel.check_connectivity_state(try_to_connect=True) != grpc.ChannelConnectivity.READY:
            self.channel = grpc.insecure_channel(self.address)
            self.stub = code_executor_pb2_grpc.CodeExecutorStub(self.channel)
            logger.info(f"Initialized gRPC client for {self.address}")
    
    def __call__(self, code: str) -> tuple[str, str, int]:
        """Execute Python code remotely.
        
        Args:
            code: The Python code to execute
            
        Returns:
            tuple: (output, error, exit_code)
        """
        self._get_channel() # make sure the connection is active
        try:
            request = code_executor_pb2.CodeExecutionRequest(
                code=code
            )
            response = self.stub.ExecuteCode(request)
            return response.output, response.error, response.exit_code
            
        except grpc.RpcError as e:
            error_msg = f"RPC failed: {str(e)}"
            logger.error(error_msg)
            return "", error_msg, 1
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return "", error_msg, 1
    
    def close(self):
        """Close the gRPC channel."""
        try:
            self.channel.close()
            logger.info("Closed gRPC channel")
        except Exception as e:
            logger.error(f"Error closing gRPC channel: {str(e)}")


