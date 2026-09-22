# Global Personality Chatbot

A privacy-first chatbot starter built around **Qwen2.5-1.5B-Instruct Q4_K_M** with a shared, global personality adapter.

## What this repo does

- Serves a small browser chat UI.
- Talks to a local/remote OpenAI-compatible llama.cpp server.
- Stores conversation events, ratings, and message edits in a database.
- Treats those events as training/feedback data for one **global** adapter.
- Rebuilds the global adapter weekly with GitHub Actions.
- Keeps the raw message store separate from the checked-in source code.
- Shows a clear warning before chat so people know messages may contribute to future tuning.
- Includes a manual, one-time model bootstrap workflow.

### Important model/runtime note

The default model is **Qwen2.5-1.5B-Instruct Q4_K_M**, a roughly 1.12 GB GGUF published by Qwen. A normal GitHub-hosted runner is not a suitable permanent inference machine. The one-time bootstrap workflow downloads that GGUF and publishes it as a GitHub Release asset rather than putting the binary in Git history.

The application is intentionally split into:

```text
Browser
  -> FastAPI app
      -> PostgreSQL / SQLite
      -> llama.cpp OpenAI-compatible endpoint
      -> global personality adapter

Feedback/edit events
  -> DB immediately
  -> weekly GitHub Actions job
      -> build preference dataset
      -> optional GPU LoRA training
      -> publish adapter artifact
```

GitHub Actions handles builds and scheduled jobs; the FastAPI server itself needs persistent compute outside an ordinary short-lived GitHub-hosted Actions job.

## Local development

1. Copy `.env.example` to `.env`.
2. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Start a compatible llama.cpp server and point `LLAMA_BASE_URL` at it.
4. Start the app:

```bash
uvicorn app.main:app --reload
```

5. Open http://localhost:8000.

## Database

Set `DATABASE_URL` to PostgreSQL in production, for example:

```
postgresql+psycopg://user:password@host:5432/chatbot
```

SQLite is supported for local development.

The write path is deliberately append-oriented: every rating and edit becomes an event immediately. This lets a separate training job consume a consistent time window without blocking chat requests.

## Privacy model

Do **not** use chat messages for passwords, authentication codes, financial information, medical records, precise addresses, or anything else you would not want included in a machine-learning dataset.

The app does not collect IP addresses or account emails by default. It uses a random browser conversation ID. Production deployments should add a real deletion flow, retention policy, access controls, encryption at rest, and a published privacy policy before collecting real users.

## Adapter strategy

There are two layers:

1. **Global personality adapter** — a small JSON artifact containing behavior guidance derived from aggregate feedback. This is always supported and can be loaded into the system prompt immediately.
2. **Optional LoRA adapter** — the weekly workflow can call `scripts/train_lora.py` on a GPU runner when `TRAIN_LORA=1` and a compatible training base model is configured.

GGUF inference weights are treated as deployment artifacts. LoRA training normally needs a compatible transformer-format training checkpoint; the GGUF file itself is not treated as a directly fine-tunable Transformers checkpoint.

## GitHub Actions and Backend environment

The repository uses a GitHub Environment named **Backend** for deployment-time configuration.

Put these in **Settings → Environments → Backend**:

**Variables**
- `BACKEND_URL` — the public HTTPS URL of the FastAPI server, used when building the GitHub Pages frontend.

**Secrets**
- `DATABASE_URL` — production PostgreSQL connection string.
- `LLAMA_BASE_URL` — URL for the llama.cpp OpenAI-compatible server when it contains sensitive connection details.
- `HF_TOKEN` — only when the optional training checkpoint is gated/private.

The weekly adapter workflow references the **Backend** environment, so `DATABASE_URL` is read from that environment's secrets.

The Pages build also references the **Backend** environment so `BACKEND_URL` can be stored there. The Pages deployment itself continues to use the separate `github-pages` environment.

The remaining tuning options can be supplied as workflow/repository variables as appropriate:
- `TRAIN_LORA` — `1` to enable optional GPU LoRA training.
- `TRAIN_BASE_MODEL` — compatible transformer checkpoint for the optional LoRA stage.

### Important limitation

A GitHub Environment is a configuration/deployment boundary, not a server. It provides variables, secrets, and optional protection rules to jobs that reference it; it does not keep a FastAPI process running 24/7. The container workflow currently publishes the backend image to GHCR, and that image still needs to be deployed to persistent compute.

## License

See the upstream model's Apache-2.0 license and the licenses of every dependency/model used by your deployment.
