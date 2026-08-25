import os
import logging
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Robust .env loading for both local and Render/Docker
# - Local: loads from .env file if present
# - Render: secrets are injected as real environment variables,
#           so we MUST NOT override them with an empty/missing .env
# ------------------------------------------------------------
dotenv_path = find_dotenv(filename=".env", usecwd=True)

if dotenv_path:
    logger.info(f"[config] Found .env at: {dotenv_path} — loading (override=False)")
    load_dotenv(dotenv_path, override=False, verbose=True)
else:
    # find_dotenv returned empty -> try default search; verbose will log if not found
    # override=False ensures Render-injected env vars are never overwritten
    result = load_dotenv(override=False, verbose=True)
    if result:
        logger.info("[config] .env loaded via default search")
    else:
        logger.info("[config] No .env file found — using system environment variables (expected on Render)")

def _mask(value: str | None) -> str:
    """Mask secrets for safe logging: show first 3 + last 2 chars + length."""
    if not value:
        return "NOT SET (None/empty) ❌"
    if len(value) <= 4:
        return f"*** (len={len(value)})"
    return f"{value[:3]}***{value[-2:]} (len={len(value)})"

def _mask_url(value: str | None) -> str:
    if not value:
        return "NOT SET (None/empty) ❌"
    # Show domain + masked tail
    return f"{value[:30]}*** (len={len(value)})"

# Hugging Face Spaces / Render inject secrets directly as environment variables.
# For local development, ensure you have exported these variables or have a .env file.
API_USERNAME = os.getenv("API_USERNAME")
API_PASSWORD = os.getenv("API_PASSWORD")
SWAGGER_USERNAME = os.getenv("SWAGGER_USERNAME")
SWAGGER_PASSWORD = os.getenv("SWAGGER_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
PROGRESS_INTERVAL = int(os.getenv("PROGRESS_INTERVAL", 100))
PORT = int(os.getenv("PORT", 7860))

# --- Startup diagnostics (visible in Render logs) ---
# Use print() as well as logger so it shows even if logging not yet configured
print("=" * 60, flush=True)
print("[config] ENV VARIABLES DIAGNOSTICS", flush=True)
print(f"[config] .env path searched: {dotenv_path or 'not found (using os.environ)'}", flush=True)
print(f"[config] API_USERNAME: {_mask(API_USERNAME)}", flush=True)
print(f"[config] API_PASSWORD: {_mask(API_PASSWORD)}", flush=True)
print(f"[config] SWAGGER_USERNAME: {_mask(SWAGGER_USERNAME)}", flush=True)
print(f"[config] SWAGGER_PASSWORD: {_mask(SWAGGER_PASSWORD)}", flush=True)
print(f"[config] DISCORD_WEBHOOK_URL: {_mask_url(DISCORD_WEBHOOK_URL)}", flush=True)
print(f"[config] PROGRESS_INTERVAL: {PROGRESS_INTERVAL}", flush=True)
print(f"[config] PORT: {PORT}", flush=True)
# Also log via logger for structured logs
logger.info("=" * 60)
logger.info("[config] ENV VARIABLES DIAGNOSTICS")
logger.info(f"[config] .env path: {dotenv_path or 'not found (using os.environ)'}")
logger.info(f"[config] API_USERNAME: {_mask(API_USERNAME)}")
logger.info(f"[config] API_PASSWORD: {_mask(API_PASSWORD)}")
logger.info(f"[config] SWAGGER_USERNAME: {_mask(SWAGGER_USERNAME)}")
logger.info(f"[config] SWAGGER_PASSWORD: {_mask(SWAGGER_PASSWORD)}")
logger.info(f"[config] DISCORD_WEBHOOK_URL: {_mask_url(DISCORD_WEBHOOK_URL)}")
logger.info(f"[config] PROGRESS_INTERVAL: {PROGRESS_INTERVAL}")
logger.info(f"[config] PORT: {PORT}")

if not API_USERNAME or not API_PASSWORD:
    msg = "⚠️  API_USERNAME or API_PASSWORD is NOT SET — /jobs/* auth will ALWAYS fail! Check Render Environment tab."
    print(f"[config] {msg}", flush=True)
    logger.warning(msg)
if not SWAGGER_USERNAME or not SWAGGER_PASSWORD:
    msg = "⚠️  SWAGGER_USERNAME or SWAGGER_PASSWORD is NOT SET — /docs auth will fail!"
    print(f"[config] {msg}", flush=True)
    logger.warning(msg)
if not DISCORD_WEBHOOK_URL:
    msg = "⚠️  DISCORD_WEBHOOK_URL is NOT SET — Discord notifications disabled."
    print(f"[config] {msg}", flush=True)
    logger.warning(msg)

print("=" * 60, flush=True)
logger.info("=" * 60)