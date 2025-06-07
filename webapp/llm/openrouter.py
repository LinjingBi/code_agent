from typing import Dict, List, Optional, Union
import httpx
from pydantic import BaseModel

class CompletionRequest(BaseModel):
    """Request model for chat completion."""
    model: str
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False

class OpenRouterError(Exception):
    """Base exception for OpenRouter API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class OpenRouter:
    """OpenRouter API client for chat completions."""
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """Initialize the OpenRouter client.
        
        Args:
            api_key: Your OpenRouter API key
            base_url: Optional custom base URL for the API
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
            }
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-3.5-turbo",
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = 1.0,
        stream: bool = False
    ) -> str:
        """Create a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Model to use for completion
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            stream: Whether to stream the response
            
        Returns:
            The LLM's response text
            
        Raises:
            OpenRouterError: If the API request fails
        """
        try:
            request = CompletionRequest(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream
            )
            
            response = await self.client.post(
                "/chat/completions",
                json=request.model_dump(exclude_none=True)
            )
            response.raise_for_status()
            
            if stream:
                return response.aiter_lines()
            
            return response.json()["choices"][0]["message"]["content"]
            
        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred: {str(e)}"
            if hasattr(e, 'response'):
                try:
                    error_data = e.response.json()
                    error_msg = f"API error: {error_data.get('error', {}).get('message', str(e))}"
                except:
                    pass
            raise OpenRouterError(
                message=error_msg,
                status_code=getattr(e, 'response', None) and e.response.status_code,
                response=getattr(e, 'response', None) and e.response.json()
            )
        except Exception as e:
            raise OpenRouterError(f"Unexpected error: {str(e)}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close() 