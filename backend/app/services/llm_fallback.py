import logging
from google import genai
from google.genai import errors

logger = logging.getLogger(__name__)

DEFAULT_FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-1.5-flash",
    "gemini-2.5-flash",
    "gemini-3.7-flash"
]

def execute_with_fallback(client: genai.Client, contents: str, models: list[str] = None, **kwargs):
    """
    Executes a generate_content request with automatic fallback on rate limit / resource exhausted errors.
    
    Args:
        client: The initialized genai.Client instance.
        contents: The prompt/contents to pass to the model.
        models: An optional list of model strings ordered by priority.
        **kwargs: Additional arguments to pass to generate_content (e.g., config).
        
    Returns:
        The successful response object from the Gemini API.
        
    Raises:
        The last exception if all models in the fallback chain fail.
    """
    if models is None:
        models = DEFAULT_FALLBACK_MODELS

    last_exception = None
    
    for i, model in enumerate(models):
        try:
            # We add a debug log to trace which model is being attempted
            logger.debug(f"Attempting generate_content with model: {model} (Tier {i+1}/{len(models)})")
            
            response = client.models.generate_content(
                model=model,
                contents=contents,
                **kwargs
            )
            
            if i > 0:
                logger.info(f"Successfully generated content using fallback model: {model}")
                
            return response
            
        except errors.APIError as e:
            # Check for 429 Resource Exhausted, 403 Quota Exceeded, 503 Service Unavailable, or 404 Not Found
            if e.code in (429, 403, 503, 404):
                logger.warning(
                    f"Model {model} failed with API error {e.code} (Rate Limit/Quota/Unavailable). "
                    f"Message: {e.message}. Attempting next fallback..."
                )
                last_exception = e
                continue
            else:
                # If it's a different API error (e.g., 400 Bad Request), re-raise immediately
                logger.error(f"Model {model} failed with non-recoverable APIError {e.code}: {e.message}")
                raise
        except Exception as e:
            # Catching generic exceptions (e.g., network timeouts) to potentially fallback or log
            logger.warning(
                f"Model {model} encountered an unexpected error: {str(e)}. Attempting next fallback..."
            )
            last_exception = e
            continue
            
    logger.error("All fallback models exhausted. Raising the last exception.")
    if last_exception:
        raise last_exception
    else:
        raise RuntimeError("Fallback execution failed without raising an exception.")
