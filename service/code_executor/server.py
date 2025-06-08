import grpc
from concurrent import futures
import io
import contextlib
from typing import Dict, Any
import logging

# Import generated gRPC code
import code_executor_pb2
import code_executor_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def final_answer(answer):
    print(f"<SYSTEM>Final answer is {answer}<SYSTEM>")

class CodeExecutorServicer(code_executor_pb2_grpc.CodeExecutorServicer):
    def ExecuteCode(self, request: code_executor_pb2.CodeExecutionRequest, context):
        """Execute Python code in a safe environment."""
        logger.info(f"Received code execution request. Code: {request.code[:50]}")
        try:
            # Capture stdout and stderr
            stdout = io.StringIO()
            stderr = io.StringIO()
            
            # Execute code with captured output
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                # Create a new namespace for execution
                namespace: Dict[str, Any] = {
                    "__builtins__": __builtins__,
                    "final_answer": final_answer,
                }
                
                # Execute the code
                exec(request.code, namespace)
            
            # Get captured output
            output = stdout.getvalue()
            error = stderr.getvalue()
            
            return code_executor_pb2.CodeExecutionResponse(
                output=output,
                error=error,
                exit_code=0
            )
            
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            return code_executor_pb2.CodeExecutionResponse(
                output="",
                error=str(e),
                exit_code= e.code if isinstance(e.code, int) else 1
            )

def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    code_executor_pb2_grpc.add_CodeExecutorServicer_to_server(
        CodeExecutorServicer(), server
    )
    port = 50051
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"Code executor server started on port {port}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
