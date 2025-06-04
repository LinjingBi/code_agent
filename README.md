# AI Chatbot

A Python-based AI chatbot using FastAPI and OpenAI's API.

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following variables:
```env
# Required: Your API key for the language model
API_KEY=your_api_key_here

# Optional: The model to use (defaults to "gpt-3.5-turbo")
MODEL_NAME=gpt-3.5-turbo
```

4. Run the application:
```bash
uvicorn main:app --reload
```

## Features

- FastAPI backend
- OpenAI API integration
- Dynamic tool loading
- Jinja2 templating for prompts

## Project Structure

- `main.py`: FastAPI application entry point
- `agent.py`: Core chatbot logic
- `utils/config.py`: Configuration management
- `tool/tool.py`: Tool decorator and registry
- `prompt.yaml`: System prompt template

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## API Endpoints

### POST /chat
Send a message to the code agent.

Request body:
```json
{
    "message": "Your message here",
    "context": ["optional", "context", "strings"]
}
```

Response:
```json
{
    "response": "Agent's response",
    "tool_calls": null
}
```
