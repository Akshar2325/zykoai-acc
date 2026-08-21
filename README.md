---
title: Messiai
colorFrom: purple
colorTo: red
sdk: gradio
sdk_version: "4.44.0"
python_version: "3.12"
app_file: app.py
pinned: false
---

# Generic Job Runner API

A production-ready FastAPI server for running background Python scripts, deployable as a Docker container on Hugging Face Spaces.

## Features

- FastAPI server with modular structure
- Background job execution (non-blocking)
- HTTP Basic Authentication (separate credentials for API and Swagger)
- Discord webhook notifications with file attachments
- Production-ready Dockerfile
- Comprehensive logging

## Quick Start

### Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variables:

```bash
export API_USERNAME=your_api_user
export API_PASSWORD=your_api_password
export SWAGGER_USERNAME=your_swagger_user
export SWAGGER_PASSWORD=your_swagger_password
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

3. Run the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Access Swagger UI: `http://localhost:8000/docs`

## Hugging Face Space Deployment

### A. Create a Hugging Face Account

Sign up at https://huggingface.co/signup

### B. Create a New Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Select **Docker** as the Space SDK
4. Choose a name (e.g., `zylo-job-runner`)
5. Set visibility (Public or Private)
6. Click "Create Space"

### C. Clone the Space Repository

```bash
git clone https://huggingface.co/spaces/<YOUR_USERNAME>/<SPACE_NAME>
cd <SPACE_NAME>
```

### D. Copy Project Files

Copy all files from this project into the cloned repository:

```
app/
scripts/
Dockerfile
requirements.txt
.gitignore
```

### E. Configure Space Secrets

In your Hugging Face Space settings, go to "Repository secrets" and add:

| Secret Name           | Description                           |
| --------------------- | ------------------------------------- |
| `API_USERNAME`        | Username for API authentication       |
| `API_PASSWORD`        | Password for API authentication       |
| `SWAGGER_USERNAME`    | Username for Swagger UI access        |
| `SWAGGER_PASSWORD`    | Password for Swagger UI access        |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications |

⚠️ **Never commit these values to Git. Always use Hugging Face Secrets.**

### F. Commit and Push

```bash
git add .
git commit -m "Initial FastAPI job runner"
git push
```

### G. Monitor Build Logs

1. Go to your Space page on Hugging Face
2. Click the "App" tab to view logs
3. Wait for Docker build to complete and the server to start
4. You should see: `Server starting up`

### H. Access Swagger UI

1. Open `https://<YOUR_USERNAME>-<SPACE_NAME>.hf.space/docs`
2. Enter Swagger credentials when prompted
3. View and test API endpoints

### I. Call the API

Use HTTP Basic Auth with `API_USERNAME` / `API_PASSWORD`:

```bash
curl -X POST "https://<YOUR_USERNAME>-<SPACE_NAME>.hf.space/jobs/start" \
  -u "$API_USERNAME:$API_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{"param1": "value1", "param2": "value2"}'
```

Response:

```json
{ "job_id": "uuid-here", "status": "started" }
```

Check job status:

```bash
curl "https://<YOUR_USERNAME>-<SPACE_NAME>.hf.space/jobs/<job_id>" \
  -u "$API_USERNAME:$API_PASSWORD"
```

## API Endpoints

### POST /jobs/start

Starts a new background job.

- **Auth**: API Basic Auth
- **Body**: JSON parameters for the script
- **Response**: `{"job_id": "...", "status": "started"}`

### GET /jobs/{job_id}

Get job status.

- **Auth**: API Basic Auth
- **Response**:

```json
{
  "job_id": "...",
  "status": "queued|running|completed|failed",
  "start_time": 1234567890.123,
  "completion_time": 1234567895.456,
  "runtime": 5.333,
  "output_file": "output_abc123.txt",
  "error": null,
  "discord_error": null
}
```

## Local Development (Without Docker)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables:
   Edit the `.env` file with your credentials. It is already set up with your Discord webhook.

3. Start the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. Open `http://localhost:8000/docs` in your browser and authenticate with your Swagger credentials.

## Integrating Your Script

Replace the placeholder in `scripts/your_script.py` with your actual script logic. Update `app/jobs.py` `run_job_script()` function to call your script.

## Security

- All endpoints protected by HTTP Basic Auth
- Credentials from environment variables only
- Constant-time credential comparison
- No sensitive data in logs
- Input validation on all endpoints
