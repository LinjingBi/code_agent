import grpc
from . import code_executor_pb2
from . import code_executor_pb2_grpc
import logging

logger = logging.getLogger(__name__)

class CodeExecutorClient:
    def __init__(self, host: str = 'localhost', port: int = 50051):
        """Initialize the code executor client.
        
        Args:
            host: The host where the code executor service is running
            port: The port where the code executor service is running
        """
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = code_executor_pb2_grpc.CodeExecutorStub(self.channel)
    
    def __call__(self, code: str) -> tuple[str, str, int]:
        """Execute Python code remotely.
        
        Args:
            code: The Python code to execute
            environment: Optional environment variables to set
            
        Returns:
            tuple: (output, error, exit_code)
        """
        try:
            request = code_executor_pb2.CodeExecutionRequest(
                code=code
            )
            response = self.stub.ExecuteCode(request)
            return response.output, response.error, response.exit_code
            
        except grpc.RpcError as e:
            logger.error(f"RPC failed: {str(e)}")
            return "", str(e), 1
    
    def close(self):
        """Close the gRPC channel."""
        self.channel.close()


