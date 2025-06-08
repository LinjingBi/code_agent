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
        self.address = f'{host}:{port}'
        self.channel = grpc.insecure_channel(
            self.address,
            options=[
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_send_message_length', 100 * 1024 * 1024),     # 100MB
                ('grpc.keepalive_time_ms', 30000),                       # 30 seconds
                ('grpc.keepalive_timeout_ms', 10000),                    # 10 seconds
                ('grpc.keepalive_permit_without_calls', True),
                ('grpc.http2.max_pings_without_data', 0),
                ('grpc.http2.min_time_between_pings_ms', 10000),         # 10 seconds
            ]
        )
        self.stub = code_executor_pb2_grpc.CodeExecutorStub(self.channel)
        logger.info(f"Initialized gRPC client for {self.address}")
    
    def __call__(self, code: str) -> tuple[str, str, int]:
        """Execute Python code remotely.
        
        Args:
            code: The Python code to execute
            
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


