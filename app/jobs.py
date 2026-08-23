import uuid
import time
import threading
import logging
from typing import Optional, Dict, Any
from .discord import send_discord_notification, send_discord_progress, discord_enabled
from .config import PROGRESS_INTERVAL

logger = logging.getLogger(__name__)

# In-memory job storage (use a database for production)
jobs: Dict[str, Dict[str, Any]] = {}

def run_job_script(parameters: Dict[str, Any], job_id: str = None, progress_callback=None) -> str:
    """
    Executes the exact Colab script logic wrapped for server execution.
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    logger.info("Starting job script execution...")
    from scripts.your_script import run
    return run(parameters, job_id=job_id, progress_callback=progress_callback)

def get_all_jobs_status() -> Dict[str, Any]:
    """Retrieve the status of all jobs."""
    return {
        "total_jobs": len(jobs),
        "jobs": [
            {
                "job_id": j["job_id"],
                "status": j["status"],
                "start_time": j["start_time"],
                "completion_time": j["completion_time"],
                "runtime": j["runtime"],
                "progress": j.get("progress"),
                "error": j["error"],
            }
            for j in jobs.values()
        ],
    }

def _send_batch_file(job_id: str, total: int, state: dict):
    """Writes the buffered accounts to a txt file and sends it to Discord."""
    from scripts.your_script import format_result

    completed = state["completed"]
    batch_file = f"output_{job_id[:8]}_{completed}.txt"
    with open(batch_file, "w") as f:
        for r in state["batch"]:
            f.write(format_result(r))
    state["batch"] = []

    send_discord_progress(job_id, completed, total, state["failed"], output_file=batch_file)
    logger.info(f"Batch file sent for job {job_id} at {completed}/{total}")

def make_progress_callback(job_id: str, total: int, interval: int):
    """
    Builds a callback that buffers each finished account. Every `interval`
    completions it sends a Discord progress message with a txt file of just
    those accounts attached.
    Returns (callback, flush) - call flush() at the end to send any leftover
    accounts that didn't fill a full interval.
    """
    state = {"completed": 0, "failed": 0, "batch": []}

    def progress_callback(result: dict):
        success = result.get("error") is None
        state["completed"] += 1
        if not success:
            state["failed"] += 1
        state["batch"].append(result)
        jobs[job_id]["progress"]["completed"] = state["completed"]
        jobs[job_id]["progress"]["failed"] = state["failed"]

        if interval > 0 and state["completed"] % interval == 0:
            try:
                _send_batch_file(job_id, total, state)
            except Exception as e:
                logger.error(f"Failed sending progress batch for job {job_id}: {e}")

    def flush():
        if state["batch"] and discord_enabled():
            try:
                _send_batch_file(job_id, total, state)
            except Exception as e:
                logger.error(f"Failed sending final progress batch for job {job_id}: {e}")

    return progress_callback, flush

def execute_job(job_id: str, parameters: Dict[str, Any]):
    """Background thread runner for a job."""
    jobs[job_id]["status"] = "running"
    jobs[job_id]["start_time"] = time.time()
    logger.info(f"Job {job_id} started")

    total = parameters.get("number_of_accounts", 2)
    interval = parameters.get("progress_interval", PROGRESS_INTERVAL)
    jobs[job_id]["progress"] = {"total": total, "completed": 0, "failed": 0}
    progress_callback, flush_batches = make_progress_callback(job_id, total, interval)

    try:
        output_file = run_job_script(parameters, job_id=job_id, progress_callback=progress_callback)
        flush_batches()
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
            send_discord_notification(
                job_id, "failed", runtime,
                error=f"Whole job failed. Reason: {e}",
                output_file=None
            )
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
        "progress": {"total": parameters.get("number_of_accounts", 2), "completed": 0, "failed": 0},
    }
    logger.info(f"Job {job_id} created")
    
    thread = threading.Thread(target=execute_job, args=(job_id, parameters), daemon=True)
    thread.start()
    
    return job_id

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the current status of a job."""
    return jobs.get(job_id)