import logging
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic
from .config import API_USERNAME, API_PASSWORD, SWAGGER_USERNAME, SWAGGER_PASSWORD, PORT
from .auth import verify_api_credentials, verify_swagger_credentials
from .jobs import start_job, get_job_status

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

@app.on_event("startup")
def startup_event():
    logger.info("Server starting up")

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

@app.post("/jobs/start", dependencies=[Depends(verify_api_credentials)])
async def create_job(payload: JobRequest):
    """
    Start a new background job.
    
    Returns a job ID immediately while the job runs in the background.
    """
    job_id = start_job(payload.model_dump())
    logger.info(f"Job {job_id} created for {payload.number_of_accounts} accounts")
    
    return {"job_id": job_id, "status": "started"}

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
        "output_file": job["output_file"],
        "error": job["error"],
        "discord_error": job["discord_error"],
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on 0.0.0.0:{PORT}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=False)