# Humanizer Agent

A FastAPI service that uses OpenAI, LangChain, and LangGraph to rewrite text in a more natural,
human style. The graph alternates between a writer and an evaluator, stopping when the quality
score reaches the configured threshold or the maximum number of passes is reached.

```text
request -> rewrite -> evaluate -> good enough / pass limit -> response
                ^         |
                +---------+ needs another pass
```

## Why LangGraph and LangChain are here

The original repository was only a deployment scaffold. It had health endpoints and configuration,
but no model invocation or agent workflow, so the `OPENAI_API_KEY` was only checked by `/ready` and
was never used.

The implementation now uses:

- `langgraph` to define and run the bounded rewrite/evaluate loop in
  `app/agent/workflow.py`.
- `langchain-openai` to connect that graph to OpenAI through `ChatOpenAI`.
- `langchain-core` for model messages and runnable interfaces.

The large `langchain` convenience package is not needed. Modern LangChain projects can install only
the provider package they use; `langchain-openai` supplies the OpenAI integration.

## Requirements

- Python 3.12 for local development, or Docker with Docker Compose
- An OpenAI API key with access to the model configured in `OPENAI_MODEL`

## Configure the environment

The `.env` file is excluded from both Git and Docker build context. If it does not already exist,
create it from the safe template:

```bash
cp .env.example .env
```

At minimum, set:

```dotenv
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4.1-mini
```

Do not commit `.env` or paste the key into source code.

## Run locally

From the repository root:

```bash
make setup
make run
```

The service starts at <http://localhost:8000>. Interactive API documentation is available at
<http://localhost:8000/docs>.

Equivalent commands without `make`:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m app.main
```

## Run with Docker

The simplest Docker command is:

```bash
docker compose up --build
```

Stop it with `Ctrl+C`, then remove the stopped container and network with:

```bash
docker compose down
```

To run without Compose:

```bash
docker build -t humanizer-agent .
docker run --rm --env-file .env -p 8000:8000 humanizer-agent
```

## Call the API

Check process health and configuration readiness:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Humanize text:

```bash
curl --request POST http://localhost:8000/humanize \
  --header 'Content-Type: application/json' \
  --data '{
    "text": "Furthermore, it is important to note that this solution facilitates improved outcomes.",
    "audience": "general readers",
    "tone": "clear and conversational"
  }'
```

Example response shape:

```json
{
  "text": "This approach can lead to better results.",
  "score": 91.0,
  "passes": 2,
  "model": "gpt-4.1-mini"
}
```

Each request can make up to `MAX_PASSES` rewrite calls plus the same number of evaluator calls, so
latency and OpenAI usage increase with the number of passes. The workflow does not call the model for
`/health`, `/ready`, or `/docs`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | required for `/humanize` | OpenAI credential |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Model used for rewriting and evaluation |
| `PORT` | `8000` | HTTP port |
| `ENVIRONMENT` | `local` | Runtime environment label |
| `LOG_LEVEL` | `INFO` | Application log level |
| `MAX_INPUT_CHARS` | `12000` | Maximum request text length |
| `MAX_PASSES` | `3` | Maximum rewrite/evaluate cycles |
| `SCORE_THRESHOLD` | `85` | Score that ends the graph early |
| `REQUEST_TIMEOUT_SECONDS` | `120` | Timeout for each model request |
| `MAX_TOKENS_PER_REQUEST` | `8000` | Maximum completion tokens per model request |

Other variables in `.env.example` are reserved for storage and MCP extensions; they are not active
in this stateless version.

## Test and lint

The unit tests use fake models and never spend OpenAI credits:

```bash
make test
make lint
```

## API behavior

- `GET /health` returns `200` when the process is alive and never calls external services.
- `GET /ready` returns `200` when `OPENAI_API_KEY` is configured, otherwise `503`.
- `POST /humanize` runs the LangGraph workflow and returns `503` without a key or `502` if the
  upstream model request fails.
- `GET /docs` provides Swagger UI for trying the API in a browser.
