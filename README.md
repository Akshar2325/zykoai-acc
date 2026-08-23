# 🚀 Zylo AI Job Runner API

> A production-ready FastAPI server for running background account-creation jobs at scale — deployed on **Render** as a Docker web service.

---

## ✨ Features

| Feature                           | Description                                                                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| ⚡**Async Job Execution**   | Jobs run in the background; API returns a`job_id` instantly                                                                   |
| 🔐**Secure by Default**     | HTTP Basic Auth (separate creds for API & Swagger UI)                                                                           |
| 💬**Discord Notifications** | Job completion (with output file attached), whole-job failures with reason,**and** live progress updates every N accounts |
| 📊**Job Monitoring**        | Status of a single job or all jobs in one call                                                                                  |
| 🐳**Docker Ready**          | Production-ready Dockerfile, deploys directly on Render                                                                         |

---

## 📡 API Endpoints

| Method   | Endpoint           | Auth       | Description                                |
| -------- | ------------------ | ---------- | ------------------------------------------ |
| `GET`  | `/health`        | ❌ Public  | Health / uptime check                      |
| `POST` | `/jobs/start`    | ✅ API     | Start a new background job                 |
| `GET`  | `/jobs`          | ✅ API     | Status of**all** jobs (no ID needed) |
| `GET`  | `/jobs/{job_id}` | ✅ API     | Status of a single job                     |
| `GET`  | `/docs`          | ✅ Swagger | Swagger UI                                 |

---

## 🔧 Request Parameters (`POST /jobs/start`)

```json
{
  "number_of_accounts": 1000,
  "max_workers": 5,
  "chat_model": "nemotron-3-ultra",
  "chat_message": "Hello! What can you do?",
  "progress_interval": 100
}
```

| Parameter              | Default                       | Description                                               |
| ---------------------- | ----------------------------- | --------------------------------------------------------- |
| `number_of_accounts` | `2`                         | Total accounts to create in this job                      |
| `max_workers`        | `1`                         | Parallel workers (threads)                                |
| `chat_model`         | `nemotron-3-ultra`          | Model used to verify each account                         |
| `chat_message`       | `"Hello! What can you do?"` | Test message sent per account                             |
| `progress_interval`  | `100`                       | Send a Discord progress update every N completed accounts |

---

## 🧪 Usage Examples

### Start a job

```bash
curl -X POST "https://<YOUR-SERVICE>.onrender.com/jobs/start" \
  -u "$API_USERNAME:$API_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{"number_of_accounts": 1000, "max_workers": 5, "progress_interval": 100}'
```

```json
{ "job_id": "uuid-here", "status": "started" }
```

### Check all jobs

```bash
curl "https://<YOUR-SERVICE>.onrender.com/jobs" \
  -u "$API_USERNAME:$API_PASSWORD"
```

```json
{
  "total_jobs": 2,
  "jobs": [
    {
      "job_id": "uuid-here",
      "status": "running",
      "start_time": 1755930000.123,
      "completion_time": null,
      "runtime": null,
      "progress": { "total": 1000, "completed": 400, "failed": 3 },
      "error": null
    }
  ]
}
```

### Check one job

```bash
curl "https://<YOUR-SERVICE>.onrender.com/jobs/<job_id>" \
  -u "$API_USERNAME:$API_PASSWORD"
```

---

## 🔔 Notifications

All notifications are sent to your **Discord webhook** (`DISCORD_WEBHOOK_URL`):

- **Job completed** — notification with the full output file attached.
- **Whole job failed** — notification including the exact error/reason why it failed.
- **Progress updates with batch files** — every `progress_interval` accounts, a message is sent **with a `.txt` file of just those accounts attached** (e.g. 100 total + interval 50 → file of first 50 at 50, file of remaining 50 at 100). Any leftover accounts are sent in a final batch when the job ends:

```
**Job Progress Update**
Job ID: <job_id>
Completed: 50/100
Failed: 2
Remaining: 50
📎 output_ab12cd34_50.txt
```

---

## ⚙️ Environment Variables

Set these in your terminal for local dev, or under **Environment → Environment Variables** in your Render service settings:

| Variable                | Required | Description                                      |
| ----------------------- | -------- | ------------------------------------------------ |
| `API_USERNAME`        | ✅       | Username for API authentication                  |
| `API_PASSWORD`        | ✅       | Password for API authentication                  |
| `SWAGGER_USERNAME`    | ✅       | Username for Swagger UI access                   |
| `SWAGGER_PASSWORD`    | ✅       | Password for Swagger UI access                   |
| `DISCORD_WEBHOOK_URL` | Optional | Discord webhook for job & progress notifications |
| `PROGRESS_INTERVAL`   | Optional | Default progress interval (default`100`)       |
| `PORT`                | Optional | Server port (Render sets this automatically)     |

⚠️ **Never commit these values to Git. Always use environment variables or Render's environment settings.**

---

## ☁️ Deploying on Render

1. Push this repository to GitHub (already done)
2. In [Render Dashboard](https://dashboard.render.com), click **New → Web Service**
3. Connect your GitHub repo and select it
4. Configure:
   - **Environment**: `Docker` (Render auto-detects the Dockerfile)
   - **Instance type**: pick based on expected workload (more workers = more RAM/CPU)
5. Add all environment variables from the table above
6. Deploy — Render builds the Docker image and starts the server automatically
7. Your API is live at `https://<YOUR-SERVICE>.onrender.com`
8. Access Swagger UI at `https://<YOUR-SERVICE>.onrender.com/docs`

> ℹ️ Free tier services spin down after ~15 min of inactivity; the first request afterwards takes longer to respond.

---

## 💻 Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables (see table above)
export API_USERNAME=your_api_user
export API_PASSWORD=your_api_password
export SWAGGER_USERNAME=your_swagger_user
export SWAGGER_PASSWORD=your_swagger_password
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# 3. Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Open Swagger UI
open http://localhost:8000/docs
```

Or run with Docker:

```bash
docker build -t zylo-job-runner .
docker run -p 8000:8000 --env-file .env zylo-job-runner
```

---

## 📁 Project Structure

```
├── app.py                  # Entry point
├── app/
│   ├── main.py             # FastAPI routes
│   ├── jobs.py             # Job execution engine + progress tracking
│   ├── discord.py          # Discord webhook notifications (status + progress)
│   ├── auth.py             # HTTP Basic Auth
│   └── config.py           # Env config
├── scripts/
│   └── your_script.py      # Account creation logic
├── Dockerfile
└── requirements.txt
```

---

## 🔒 Security

- All sensitive endpoints protected by HTTP Basic Auth
- Constant-time credential comparison
- Credentials only from environment variables
- No sensitive data in logs

---

## 📝 Notes

- Job storage is **in-memory** — restarting/redeploying the service clears job history. Use a database if persistence is required.
- For large jobs (e.g. 1000 accounts), tune `max_workers` carefully — each account takes roughly 1–1.5 minutes.
- Render may restart the service during deploys, which cancels running background jobs.
