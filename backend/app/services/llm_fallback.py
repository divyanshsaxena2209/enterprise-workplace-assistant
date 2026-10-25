import logging
from google import genai
from google.genai import errors

logger = logging.getLogger(__name__)

# Use currently documented stable Gemini API model IDs. Lite models are tried
# first for lower-cost throughput-oriented tasks; larger stable Flash models follow.
DEFAULT_FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]


def execute_with_fallback(client: genai.Client, contents: str, models: list[str] = None, **kwargs):
    """
    Executes a generate_content request with bounded model fallback.

    The Gemini SDK retries transient network, 429 and 5xx failures internally.
    This function tries the next supported model when the selected model is
    unavailable or rate-limited. Configuration/permission failures are surfaced
    immediately rather than repeated against other models.
    """
    if models is None:
        models = DEFAULT_FALLBACK_MODELS

    last_exception = None

    for i, model in enumerate(models):
        try:
            logger.debug(
                "Attempting generate_content with model: %s (Tier %s/%s)",
                model,
                i + 1,
                len(models),
            )
            response = client.models.generate_content(
                model=model,
                contents=contents,
                **kwargs
            )
            if i > 0:
                logger.info("Successfully generated content using fallback model: %s", model)
            return response
        except errors.APIError as exc:
            # 404 can mean this model is unavailable to the project; 429/5xx
            # may be transient. Do not mask invalid credentials/permissions (401/403).
            if exc.code in (404, 408, 429, 500, 502, 503, 504):
                logger.warning(
                    "Model %s failed with API error %s; trying next fallback model.",
                    model,
                    exc.code,
                )
                last_exception = exc
                continue
            logger.error("Model %s failed with non-recoverable API error %s.", model, exc.code)
            raise
        except Exception as exc:
            logger.warning(
                "Model %s encountered an unexpected error (%s); trying next fallback model.",
                model,
                type(exc).__name__,
            )
            last_exception = exc
            continue

    logger.error("All fallback models exhausted.")
    if last_exception:
        raise last_exception
    raise RuntimeError("Fallback execution failed without raising an exception.")
