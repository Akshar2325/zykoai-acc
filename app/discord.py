import os
import requests
import logging
from .config import DISCORD_WEBHOOK_URL

logger = logging.getLogger(__name__)

def send_discord_notification(job_id: str, status: str, runtime: float, error: str = None, output_file: str = None):
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord webhook URL not configured. Skipping notification.")
        return

    content = f"**Job {status.upper()}**\nJob ID: `{job_id}`\nRuntime: `{runtime}s`"
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