from concurrent import futures
import io
import contextlib
from typing import Dict, Any
import logging

import grpc
from google.protobuf.empty_pb2 import Empty

from tool import tool_registry

import code_executor_pb2
import code_executor_pb2_grpc

# tool imports
from tool import search

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def final_answer(answer):
    print(f"<SYSTEM>Final answer is {answer}<SYSTEM>")

class CodeExecutorServicer(code_executor_pb2_grpc.CodeExecutorServicer):
    def GetToolList(self, request, context) -> code_executor_pb2.GetToolListResponse:
        logger.info(f"Received get code execution tools request")
        try:
            # Get tools from registry (returns Python dict)
            tools_dict = tool_registry.get_tools()
            
            # Convert to protobuf messages
            tool_messages = []
            for tool_name, tool_info in tools_dict.items():
                # Convert inputs dict to protobuf format
                inputs_proto = {}
                for input_name, input_info in tool_info.get('inputs', {}).items():
                    inputs_proto[input_name] = code_executor_pb2.ToolInput(
                        type=input_info.get('type', Any),
                        description=input_info.get('description', '')
                    )
                
                # Create Tool message
                tool_message = code_executor_pb2.Tool(
                    name=tool_info.get('name', tool_name),
                    description=tool_info.get('description', ''),
                    output_type=tool_info.get('output_type', Any),
                    inputs=inputs_proto
                )
                tool_messages.append(tool_message)
            
            # Return GetToolListResponse
            return code_executor_pb2.GetToolListResponse(tools=tool_messages)
            
        except Exception as e:
            logger.error(f"Error getting tool list: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting tool list: {str(e)}")
            raise
        

    def ExecuteCode(self, request: code_executor_pb2.CodeExecutionRequest, context) -> code_executor_pb2.CodeExecutionResponse:
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
                tool_namespace = {"search": search}
                namespace.update(tool_namespace)
                
                # Execute the code
                try:
                    exec(request.code, namespace)
                    output = stdout.getvalue()
                    error = stderr.getvalue()
                    return code_executor_pb2.CodeExecutionResponse(
                        output=output,
                        error=error,
                        exit_code=0
                    )
                except Exception as e:
                    error = f"{type(e).__name__}: {str(e)}"
                    return code_executor_pb2.CodeExecutionResponse(
                        output="",
                        error=error,
                        exit_code=1
                    )
            
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise

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
