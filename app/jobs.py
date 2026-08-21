import uuid
import time
import threading
import logging
from typing import Optional, Dict, Any
from .discord import send_discord_notification

logger = logging.getLogger(__name__)

# In-memory job storage (use a database for production)
jobs: Dict[str, Dict[str, Any]] = {}

def run_job_script(parameters: Dict[str, Any]) -> str:
    """
    Executes the exact Colab script logic wrapped for server execution.
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    logger.info("Starting job script execution...")
    from scripts.your_script import run
    return run(parameters)

def execute_job(job_id: str, parameters: Dict[str, Any]):
    """Background thread runner for a job."""
    jobs[job_id]["status"] = "running"
    jobs[job_id]["start_time"] = time.time()
    logger.info(f"Job {job_id} started")
    
    try:
        output_file = run_job_script(parameters)
        runtime = time.time() - jobs[job_id]["start_time"]
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completion_time"] = time.time()
        jobs[job_id]["runtime"] = runtime
        jobs[job_id]["output_file"] = output_file
        logger.info(f"Job {job_id} completed in {runtime:.2f}s")
        
        # Send Discord notification
        try:
            send_discord_notification(job_id, "completed", runtime, output_file=output_file)
        except Exception as e:
            logger.error(f"Discord notification failed for job {job_id}: {e}")
            jobs[job_id]["discord_error"] = str(e)
            
    except Exception as e:
        runtime = time.time() - jobs[job_id].get("start_time", time.time())
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["completion_time"] = time.time()
        jobs[job_id]["runtime"] = runtime
        jobs[job_id]["error"] = str(e)
        logger.error(f"Job {job_id} failed: {e}")
        
        try:
            send_discord_notification(job_id, "failed", runtime, error=str(e))
        except Exception as de:
            logger.error(f"Discord failure notification also failed for job {job_id}: {de}")

def start_job(parameters: Dict[str, Any]) -> str:
    """Create a new job and start it in the background."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "start_time": None,
        "completion_time": None,
        "runtime": None,
        "output_file": None,
        "error": None,
        "discord_error": None,
    }
    logger.info(f"Job {job_id} created")
    
    thread = threading.Thread(target=execute_job, args=(job_id, parameters), daemon=True)
    thread.start()
    
    return job_id

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the current status of a job."""
    return jobs.get(job_id)