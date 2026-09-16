# n8n-Job-Hunter
n8n Job Hunter: runs daily at 7AM (you can set), scrapes Himalayas, Jobicy, Remotive, Arbeitnow, RemoteOK, TheMuse, Indeed and JobStreet, dedupes listings, scores each job against the resume via Gemini/local Llama AI, keeps 80+ matches, and emails an HTML digest of the best remote/hybrid job fits.


# 🤖 AI Job Hunting Bot

An n8n workflow that automatically scrapes job postings from multiple boards, scores each one against your resume using local or cloud AI, and emails you a daily digest of your strongest matches.

## ✨ Features

- **Multi-source scraping** — Pulls jobs from Jobicy, Himalayas, TheMuse, Remotive, RemoteOK, Arbeitnow, Indeed, and JobStreet
- **AI-powered scoring** — Uses Google Gemini (cloud) with automatic fallback to Ollama (local) for offline scoring
- **Smart deduplication** — Remembers seen jobs across runs so you never get repeats
- **Location-aware** — Filters for jobs open to your target country
- **HTML email digest** — Beautifully formatted email with match scores, AI reasoning, and direct apply links
- **Scheduled runs** — Automatically runs every morning at 7 AM
- **Free to run** — No paid APIs required (Gemini free tier + Ollama)

## 📋 Prerequisites

Before you begin, make sure you have:

| Requirement | Why |
|-------------|-----|
| **n8n** (v1.0+) | Workflow orchestration |
| **Python 3.10+** | Runs the Indeed scraper |
| **Ollama** | Local AI model (free fallback) |
| **Google Account** | For Gmail SMTP + Gemini API |
| **Node.js 18+** | Required by Playwright for the Indeed scraper |

## 🏗️ Architecture

```
┌─────────────────┐
│  Schedule       │  Runs daily at 7 AM
│  Trigger        │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Edit Fields    │  Your resume + job titles + preferences
└────────┬────────┘
         ↓
┌─────────────────┐
│  Split Out      │  Creates one branch per job title
└────────┬────────┘
         ↓
   ┌─────┴──────────────────────────────────────┐
   ↓     ↓     ↓     ↓     ↓     ↓     ↓     ↓   ↓
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬──────┐
│ API │ API │ API │ API │ API │ API │ API │ API │ Py   │
│Jobicy│Hima│Muse│Remot│RemOK│Arbeit│Indd│JobSt│ scraper│
└──┬──┴──┬──┴──┬──┴──┬──┴──┬──┴──┬──┴──┬──┴──┬──┴───┬──┘
   └─────┴─────┴─────┴─────┴─────┴─────┴─────┴──────┘
                      ↓
              ┌───────────────┐
              │  Merge        │  Combines all sources
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │ Remove Dups   │  Deduplicates by URL
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │ Loop Over     │  Batches of 5
              │ Items         │
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │ Gemini HTTP   │  Primary AI scorer
              │   (fallback)  │
              └───────┬───────┘
                      ↓ (on error)
              ┌───────────────┐
              │ Ollama Local  │  Backup AI scorer
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │ Parse + Filter│  Score >= 70
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │ Aggregate     │
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │ Send Email    │  HTML digest
              └───────────────┘
```

## 🚀 Setup Guide

### 1. Install n8n

**Option A — npx (quickest):**
```bash
npx n8n
```

**Option B — npm global install:**
```bash
npm install n8n -g
n8n start
```

Once n8n is running, open `http://localhost:5678` in your browser.

### 2. Install Ollama (Local AI Fallback)

1. Download and install Ollama from [ollama.com](https://ollama.com)
2. Open a terminal and pull the model used in this workflow:
   ```bash
   ollama pull llama3.1:8b
   ```
3. Verify it's running:
   ```bash
   ollama list
   ```
   You should see `llama3.1:8b` in the list.

4. **Important:** Ollama listens on `127.0.0.1:11434` (IPv4 only). If you get "connection refused" errors in n8n, use `http://127.0.0.1:11434` (not `http://localhost:11434`) in your HTTP Request node.

### 3. Get a Gemini API Key (Free)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API key"**
4. Copy the key — you'll need it in n8n

### 4. Set Up Gmail SMTP

Sending email requires an **App Password** (not your regular password).

1. Go to your [Google Account Security page](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (required for App Passwords)
3. Search for **"App Passwords"** in the search bar
4. Create a new app password:
   - App name: `n8n Job Bot`
   - Click **Create**
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

You'll use this in the **Send Email** node with these settings:
- **Host:** `smtp.gmail.com`
- **Port:** `465`
- **SSL/TLS:** ON
- **User:** your-email@gmail.com
- **Password:** the 16-char app password

### 5. Set Up the Indeed Scraper

The Indeed scraper is based on **[JIM-jobs-scraper](https://github.com/blurridge/JIM-jobs-scraper)** (modified version included in this repo).

#### Install Python dependencies:
```bash
pip install playwright
playwright install chromium
```

#### Copy the scraper:
Place `scraper.py` (included in this repo) into a folder, e.g.:
```
C:\Users\YourName\Documents\py\jim-jobs-scraper\scraper.py
```

#### Test it:
```bash
python scraper.py "Web Developer" "Manila" indeed
```

You should see JSON output with Indeed job listings.

### 6. ⚠️ Enable the Execute Command Node (CRITICAL)

The Execute Command node is **disabled by default** in n8n v2.0+ for security reasons. Without enabling it, your workflow will fail to run the Python scraper.

#### Windows (PowerShell):
```powershell
[System.Environment]::SetEnvironmentVariable('NODES_EXCLUDE','[]','User')
```
Then **close and reopen** your terminal, and start n8n normally.

#### Windows (Command Prompt):
```cmd
set NODES_EXCLUDE=[]
n8n start
```

#### macOS / Linux:
```bash
export NODES_EXCLUDE=[]
n8n start
```

To make it permanent on macOS/Linux, add the line to `~/.bashrc` or `~/.zshrc`.

#### Docker:
Add the environment variable to your `docker-compose.yml`:
```yaml
environment:
  - NODES_EXCLUDE=[]
```

Then recreate the container:
```bash
docker compose down
docker compose up -d
```

**Verify it worked:**
- Refresh your n8n editor (`Ctrl+Shift+R`)
- Click `+` to add a node
- Search for **"Execute Command"** — it should now appear

### 7. Import the Workflow

1. Download `workflow.json` from this repo
2. In n8n, click **Workflows → Import from File**
3. Select the JSON file
4. The workflow will appear on your canvas

### 8. Configure the Workflow

#### A. Edit Fields Node

Open the **Edit Fields** node and customize:

| Field | Type | Example |
|-------|------|---------|
| `job_title` | Array | `["Web Developer", "Software Engineer", "Quality Assurance"]` |
| `tech_stack` | String | `"PHP, Python, JavaScript, SQL, HTML, CSS"` |
| `resume_text` | String | Paste your full resume text here |
| `match_threshold` | Number | `70` |
| `work_mode` | Array | `["Remote", "Hybrid"]` |

#### B. Execute Command Node

Update the Python path in the command field:
```
python "C:\Users\YourName\Documents\py\jim-jobs-scraper\scraper.py" "{{ $json.job_title }}" "Manila" indeed 2>nul
```

- On macOS/Linux, use `python3` instead of `python`
- Change `"Manila"` to your preferred city

#### C. Gemini HTTP Request Node

1. Open the **HTTP Request Gemini** node
2. Under **Authentication**, select **Generic Credential Type → Header Auth**
3. Create a new credential:
   - **Name:** `Authorization`
   - **Value:** `Bearer YOUR_GEMINI_API_KEY`

#### D. Send Email Node

1. Open the **Send an Email** node
2. Create a new SMTP credential with the details from Step 4
3. Set **From** and **To** to your email

### 9. Run the Workflow

1. Click **Execute Workflow** at the bottom of the canvas
2. The first run takes ~5-10 minutes (Indeed scraping is slow)
3. Check your inbox for the job digest email!

### 10. Schedule It

The workflow is pre-configured to run **daily at 7 AM**. To change this:

1. Open the **Schedule Trigger** node
2. Adjust the trigger time
3. Make sure your laptop is on and Ollama is running at that time
4. Click **Publish** (top-right) to activate the workflow

## 🔧 Troubleshooting

### "Execute Command" doesn't appear in the node list
- Verify you set `NODES_EXCLUDE=[]` **before** starting n8n
- Restart n8n completely (not just refresh the browser)
- Check that the environment variable is set: `echo $env:NODES_EXCLUDE` (PowerShell)

### "Connection refused" when calling Ollama
- Use `http://127.0.0.1:11434` instead of `http://localhost:11434`
- Make sure Ollama is running: `ollama list` should return a list
- Check that the model is downloaded: `ollama pull llama3.1:8b`

### Gemini returns "429 Too Many Requests"
- You've hit the free-tier rate limit
- The workflow automatically retries via Ollama fallback
- Wait 60 seconds and try again

### Indeed scraper returns 0 jobs
- Indeed's HTML structure changes periodically
- Open `scraper.py` and verify the CSS selectors still match
- You can inspect the page in your browser: right-click a job card → **Inspect**
- Look for `<div class="job_seen_beacon">` — if that's changed, update the selector

### Email never arrives
- Check spam folder
- Verify the SMTP credentials work by clicking **Execute step** on the Send Email node
- Confirm your Google account has "Less secure app access" enabled OR you're using an App Password

### The loop never finishes
- **Split In Batches** node terminates early if any downstream node returns fewer items than it received
- If you use a Filter inside the loop, use `.map()` instead of `.filter()` — move filtering to **after** the Aggregate node

## 📝 Customization

### Changing Target Roles

Edit the `job_title` field in the **Edit Fields** node:
```json
["Business Analyst", "Quality Assurance", "Software Tester", "QA Engineer"]
```

### Adjusting Match Threshold

Edit the **Filter code** node's last line:
```javascript
const filtered = matches.filter(job => job.match_score >= 70);
```

- `50` = more results (looser)
- `70` = balanced
- `85` = only the best matches

### Adding More Job Sources

1. Add a new **HTTP Request** node connected to **Split Out**
2. Add a **Code** node after it to normalize the response to this schema:
   ```javascript
   { title, company, description, url, source, location, work_mode, posted_at }
   ```
3. Connect the Code node to the **Merge** node's next available input
4. Increase the Merge node's input count

## 📄 License

MIT — free to use, modify, and distribute.

## 🙏 Credits

- **JIM-jobs-scraper** by [@blurridge](https://github.com/blurridge) — foundation for the Indeed scraper
- **n8n** — the workflow automation platform
- **Ollama** — local LLM runtime
- **Google Gemini** — free cloud AI

**Happy job hunting!** 🎯

<img width="1867" height="835" alt="Screenshot 2026-09-11 165317" src="https://github.com/user-attachments/assets/70d10ad0-5647-403d-9c13-1415dfe6e9cc" />

---
