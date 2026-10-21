"""AWS Lambda entry point for the FastAPI application."""

from mangum import Mangum

from app.main import app

# The application does not define ASGI lifespan startup/shutdown handlers.
# Mangum translates Lambda Function URL HTTP events into ASGI requests.
handler = Mangum(app, lifespan="off")
