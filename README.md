# Global Personality Chatbot

A privacy-first chatbot starter built around **prism-ml/Ternary-Bonsai-2-27B-gguf** with a shared, global personality adapter.

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

The default model is **Qwen2.5-1.5B-Instruct Q4_K_M**, a roughly 1.12 GB GGUF published by Qwen. A normal GitHub-hosted runner is not a suitable permanent inference machine, and GitHub's regular repository file limit is 100 MiB. The one-time bootstrap workflow downloads that GGUF and publishes it as a GitHub Release asset. GitHub allows individual release assets below 2 GiB, so this model fits without entering Git history.

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

The bundled model card currently recommends temperature 0.7, top-p 0.95, and top-k 20 for this model family.

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

## GitHub Actions

- `bootstrap-model.yml`: manual, one-time model download to a persistent model directory on a self-hosted/larger runner.
- `weekly-adapter.yml`: every Sunday, exports recent feedback and rebuilds the global personality adapter.
- `ci.yml`: tests the API and frontend basics.
- `container.yml`: builds a container image on pushes to `main`.

Set these repository variables/secrets as needed:

- `DATABASE_URL` — production PostgreSQL connection string.
- `LLAMA_BASE_URL` — URL for the llama.cpp OpenAI-compatible server.
- `TRAIN_LORA` — `1` to enable optional GPU LoRA training.
- `TRAIN_BASE_MODEL` — compatible transformer checkpoint for the optional LoRA stage.
- `HF_TOKEN` — only when the optional training checkpoint is gated/private.

The default Qwen2.5-1.5B-Instruct model is Apache-2.0 licensed. urlQwen model cardhttps://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF

## License

See the upstream model's Apache-2.0 license and the licenses of every dependency/model used by your deployment.
