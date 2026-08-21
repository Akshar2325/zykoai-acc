import os

# Hugging Face Spaces inject secrets directly as environment variables.
# For local development, ensure you have exported these variables in your terminal.
API_USERNAME = os.getenv("API_USERNAME")
API_PASSWORD = os.getenv("API_PASSWORD")
SWAGGER_USERNAME = os.getenv("SWAGGER_USERNAME")
SWAGGER_PASSWORD = os.getenv("SWAGGER_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
PORT = int(os.getenv("PORT", 7860))