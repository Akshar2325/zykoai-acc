import logging
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic
from .config import API_USERNAME, API_PASSWORD, SWAGGER_USERNAME, SWAGGER_PASSWORD, PORT
from .auth import verify_api_credentials, verify_swagger_credentials
from .jobs import start_job, get_job_status, get_all_jobs_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Generic Job Runner API",
    description="Production-ready FastAPI server for running background jobs",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

class JobRequest(BaseModel):
    number_of_accounts: int = 2
    max_workers: int = 1
    chat_model: str = "nemotron-3-ultra"
    chat_message: str = "Hello! What can you do?"
    progress_interval: int = 100

@app.on_event("startup")
def startup_event():
    # Re-log env diagnostics at startup (visible in Render logs)
    # Import here to ensure config's print has already run, and re-check live values
    from . import config as _cfg
    import os
    def _mask(v):
        if not v: return "NOT SET ❌"
        return f"{v[:3]}***{v[-2:]} (len={len(v)})" if len(v) > 4 else f"*** (len={len(v)})"
    print("=" * 60, flush=True)
    print("[startup] Server starting up — ENV CHECK", flush=True)
    print(f"[startup] API_USERNAME={_mask(os.getenv('API_USERNAME') or _cfg.API_USERNAME)}", flush=True)
    print(f"[startup] API_PASSWORD={_mask(os.getenv('API_PASSWORD') or _cfg.API_PASSWORD)}", flush=True)
    print(f"[startup] SWAGGER_USERNAME={_mask(os.getenv('SWAGGER_USERNAME') or _cfg.SWAGGER_USERNAME)}", flush=True)
    print(f"[startup] SWAGGER_PASSWORD={_mask(os.getenv('SWAGGER_PASSWORD') or _cfg.SWAGGER_PASSWORD)}", flush=True)
    print(f"[startup] DISCORD_WEBHOOK_URL={'SET ✅' if (os.getenv('DISCORD_WEBHOOK_URL') or _cfg.DISCORD_WEBHOOK_URL) else 'NOT SET ❌'}", flush=True)
    print(f"[startup] PORT={os.getenv('PORT') or _cfg.PORT}", flush=True)
    print("=" * 60, flush=True)
    logger.info("Server starting up — env check logged above")
    if not _cfg.API_USERNAME or not _cfg.API_PASSWORD:
        logger.warning("API credentials NOT SET — all /jobs/* requests will return 401! Set them in Render > Environment")

@app.get("/docs", dependencies=[Depends(verify_swagger_credentials)])
async def get_docs():
    """Swagger UI protected by HTTP Basic Auth."""
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="API Docs"
    )

@app.get("/openapi.json", dependencies=[Depends(verify_swagger_credentials)])
async def get_openapi():
    """OpenAPI schema protected by HTTP Basic Auth."""
    return app.openapi()

@app.get("/health")
async def health_check():
    """Public health/uptime endpoint. No authentication required."""
    return {"status": "ok", "service": "Zylo AI Job Runner"}

@app.head("/health")
async def health_check_head():
    """Public HEAD health check for uptime monitors. No authentication required."""
    return {"status": "ok", "service": "Zylo AI Job Runner"}

@app.post("/jobs/start", dependencies=[Depends(verify_api_credentials)])
async def create_job(payload: JobRequest):
    """
    Start a new background job.
    
    Returns a job ID immediately while the job runs in the background.
    """
    job_id = start_job(payload.model_dump())
    logger.info(f"Job {job_id} created for {payload.number_of_accounts} accounts")
    
    return {"job_id": job_id, "status": "started"}

@app.get("/jobs", dependencies=[Depends(verify_api_credentials)])
async def list_jobs():
    """
    Get the status of ALL jobs at once. No job ID required.
    """
    return get_all_jobs_status()

@app.get("/jobs/{job_id}", dependencies=[Depends(verify_api_credentials)])
async def get_job(job_id: str):
    """
    Check the status of a job by ID.
    
    Returns current status, timing info, and error details if applicable.
    """
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "start_time": job["start_time"],
        "completion_time": job["completion_time"],
        "runtime": job["runtime"],
        "progress": job.get("progress"),
        "output_file": job["output_file"],
        "error": job["error"],
        "discord_error": job["discord_error"],
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on 0.0.0.0:{PORT}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=False)