# Code Agent with Code Execution Service

This project consists of a main application that uses an LLM to generate code and a separate microservice for executing that code safely.

## Architecture

```
Main Application (Code Agent)
        │
        │ gRPC (port 50051)
        ▼
┌─────────────────┐
│  Code Executor  │
│  (Docker)       │
└─────────────────┘
```

### Components

1. **Code Agent (Main Application)**
   - FastAPI web application
   - Uses OpenRouter LLM for code generation
   - Manages conversation history
   - Communicates with code executor service
   - Validates and processes LLM responses

2. **Code Executor Service (Microservice)**
   - Runs in isolated Docker container
   - Executes Python code safely
   - Captures stdout/stderr
   - Returns execution results

## Setup

### Code Executor Service

1. Build the Docker image:
```bash
cd service/code_executor
docker build -t code-executor .
```

2. Run the service:
```bash
docker run -p 50051:50051 code-executor
```

### Main Application

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export API_KEY="your-openrouter-api-key"
export CODE_EXECUTOR_HOST="localhost"  # or your service host
export CODE_EXECUTOR_PORT="50051"
```

3. Run the FastAPI application:
```bash
uvicorn main:app --reload
```

The API will be available at:
- API Documentation: http://localhost:8000/docs
- Alternative Documentation: http://localhost:8000/redoc

## API Endpoints

### POST /chat
Send a message to the code agent.

Request body:
```json
{
    "message": "Your message here"
}
```

Response:
```json
{
    "thought": "Agent's reasoning",
    "code": "Generated code",
    "observation": "Code execution result"
}
```

## Code Execution Flow

1. User sends a message to the Code Agent via API
2. LLM generates a response with thought and code
3. Code is validated and cleaned
4. Code is sent to Code Executor service
5. Code Executor runs the code in an isolated environment
6. Results are returned to the main application
7. Results are added to the conversation history
8. Full response is returned to the user

## Security

- Code execution happens in an isolated Docker container
- Each execution uses a fresh namespace
- Environment variables can be controlled
- Output is captured and sanitized
- API endpoints are protected (add your authentication)

## Development

### Project Structure
```
<project_root>/
├── service/
│   ├── code_executor/
│   │   ├── client.py
│   │   ├── server.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── proto/
│   │       └── code_executor.proto
├── agent/
│   └── agent.py
├── main.py
└── requirements.txt
```

### Adding New Features

1. Update the Protocol Buffer definition in `service/code_executor/proto/code_executor.proto`
2. Regenerate gRPC code
3. Update server and client implementations
4. Rebuild and redeploy the service

## Error Handling

- Invalid code is caught and reported
- Execution errors are captured and returned
- Network issues are handled gracefully
- All errors are logged for debugging
- API errors return appropriate HTTP status codes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[MIT]

## Future Improvements

### Security Enhancements
1. **Secure gRPC Communication**
   - Implement TLS/SSL for gRPC communication
   - Add certificate-based authentication
   - Configure secure ports for production
   - Environment variables for SSL configuration:
     ```
     GRPC_USE_SECURE=true
     GRPC_CERT_FILE=/path/to/cert.pem
     GRPC_KEY_FILE=/path/to/key.pem
     ```

2. **Code Execution Safety**
   - Add resource limits (CPU, memory)
   - Implement timeouts for code execution
   - Add sandboxing for code execution
   - Restrict available Python modules

3. **Authentication & Authorization**
   - Add API key authentication
   - Implement rate limiting
   - Add user-based access control
   - Log all code execution attempts

### Performance Optimizations
1. **Scaling**
   - Add load balancing for code executor
   - Implement connection pooling
   - Add caching for frequently executed code
   - Optimize Docker container size

2. **Monitoring**
   - Add metrics collection
   - Implement health checks
   - Add performance monitoring
   - Set up alerting

### Development Experience
1. **Testing**
   - Add unit tests
   - Add integration tests
   - Add load tests
   - Set up CI/CD pipeline

2. **Documentation**
   - Add API documentation
   - Add deployment guides
   - Add troubleshooting guides
   - Add development guides
