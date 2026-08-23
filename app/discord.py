import os
import requests
import logging
from .config import DISCORD_WEBHOOK_URL

logger = logging.getLogger(__name__)

def discord_enabled() -> bool:
    return bool(DISCORD_WEBHOOK_URL)

def send_discord_notification(job_id: str, status: str, runtime: float = None, error: str = None, output_file: str = None):
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord webhook URL not configured. Skipping notification.")
        return

    content = f"**Job {status.upper()}**\nJob ID: `{job_id}`"
    if runtime is not None:
        content += f"\nRuntime: `{runtime}s`"
    if error:
        content += f"\nError: `{error[:500]}`"
    
    payload = {"content": content}
    
    try:
        if output_file and os.path.exists(output_file):
            with open(output_file, "rb") as f:
                requests.post(DISCORD_WEBHOOK_URL, data=payload, files={"file": f})
            logger.info(f"Discord notification with attachment sent for job {job_id}")
        else:
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            logger.info(f"Discord notification sent for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to send Discord notification for job {job_id}: {e}")
        raise

def send_discord_progress(job_id: str, completed: int, total: int, failed: int, output_file: str = None):
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord webhook URL not configured. Skipping progress notification.")
        return

    remaining = total - completed
    content = (
        f"**Job Progress Update**\n"
        f"Job ID: `{job_id}`\n"
        f"Completed: `{completed}/{total}`\n"
        f"Failed: `{failed}`\n"
        f"Remaining: `{remaining}`"
    )

    try:
        if output_file and os.path.exists(output_file):
            with open(output_file, "rb") as f:
                requests.post(DISCORD_WEBHOOK_URL, data={"content": content}, files={"file": f})
        else:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
        logger.info(f"Discord progress notification sent for job {job_id} ({completed}/{total})")
    except Exception as e:
        logger.error(f"Failed to send Discord progress notification for job {job_id}: {e}")