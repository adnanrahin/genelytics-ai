# Genelytics

Chat-driven analytics and ETL over any SQLAlchemy database. Ask questions in natural language, get dialect-correct SQL executed safely, and load/transform CSVs through the same engine — as a Python library or via the Flask demo UI.

## Features

- **NL → SQL → answer** — schema-aware SQL generation, safe execution, plain-English responses
- **Env-based LLM config** — YAML profiles for Ollama, OpenAI, OpenAI-compatible gateways, and AWS Bedrock (nothing hard-coded in code)
- **Multi-database** — MySQL, PostgreSQL, SQLite (and other SQLAlchemy dialects via URI)
- **Chat-driven ETL** — load CSV, rename/cast/filter, write tables with pandas + SQLAlchemy
- **Read-only analytics guard** — blocks INSERT/UPDATE/DELETE/DROP in analytics mode
- **Session memory** — follow-up questions keep history by `session_id`

## Requirements

- Python **3.10+**
- An LLM endpoint (**Ollama** recommended for local use)
- A database (optional NASA MySQL demo included under `project_config/nasa-docker-db`)

## Install via pip (library users)

```bash
# when published to PyPI:
pip install genelytics

# from GitHub before PyPI:
pip install git+https://github.com/adnanrahin/generative-data-analytics-engine.git

# include the Flask demo UI:
pip install "genelytics[demo]"
```

## Install from source (developers)

```bash
git clone https://github.com/adnanrahin/generative-data-analytics-engine.git
cd generative-data-analytics-engine

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Unix/macOS:
# source .venv/bin/activate

pip install -e ".[demo,dev]"
```

## Configuration

Nothing LLM-related is hard-coded in Python. Pick an environment YAML, then optionally override with env vars.

**1. Choose an environment** (`GENELYTICS_ENV` → `config/environments/{name}.yaml`):

| Profile | Typical use |
|---------|-------------|
| `local` | Ollama on localhost |
| `development` | Dev Ollama / swap provider in YAML |
| `production` | OpenAI |
| `openai_compatible` | Groq, Azure OpenAI, vLLM, etc. |
| `bedrock` | AWS Bedrock (`pip install 'genelytics[bedrock]'`) |

Add your own file (e.g. `config/environments/staging.yaml`) and set `GENELYTICS_ENV=staging`.

| Variable | Purpose |
|----------|---------|
| `GENELYTICS_ENV` | **Required** — which YAML profile to load |
| `GENELYTICS_CONFIG_DIR` | Override path to the `config/` directory |
| `GENELYTICS_LLM__PROVIDER` | `ollama` \| `openai` \| `openai_compatible` \| `bedrock` |
| `GENELYTICS_LLM__BASE_URL` | Ollama / OpenAI-compatible base URL |
| `GENELYTICS_LLM__MODEL` | Model name or Bedrock model id |
| `GENELYTICS_LLM__API_KEY` | API key (OpenAI / compatible) |
| `GENELYTICS_LLM__REGION` | AWS region (Bedrock) |
| `GENELYTICS_DATABASE__URI` | Optional default SQLAlchemy URI |

Copy `.env.example` for a full checklist.

**Local (Ollama)** — edit `config/environments/local.yaml`:

```yaml
llm:
  provider: ollama
  base_url: http://127.0.0.1:11434
  model: mistral
  temperature: 0
```

**OpenAI:**

```bash
set GENELYTICS_ENV=production
set GENELYTICS_LLM__API_KEY=sk-...
```

**AWS Bedrock:**

```bash
pip install "genelytics[bedrock]"
set GENELYTICS_ENV=bedrock
set GENELYTICS_LLM__REGION=us-east-1
# use AWS profile / IAM role, or set GENELYTICS_LLM__AWS_ACCESS_KEY_ID=...
```

**OpenAI-compatible gateway:**

```bash
set GENELYTICS_ENV=openai_compatible
set GENELYTICS_LLM__BASE_URL=https://api.groq.com/openai/v1
set GENELYTICS_LLM__API_KEY=gsk-...
```

## Use as a library

```python
from genelytics import AnalyticsEngine

engine = AnalyticsEngine.from_env()  # reads GENELYTICS_ENV → config/environments/{env}.yaml
# engine = AnalyticsEngine.from_env("bedrock")
# engine = AnalyticsEngine.from_yaml("config/environments/production.yaml")
engine.connect(uri="mysql+pymysql://root:root@localhost:3305/nasa_space_exploration_database")
# or structured kwargs (UI sends "postgres"; both "postgres" and "postgresql" work):
# engine.connect(db_type="mysql", host="localhost", port=3305,
#                username="root", password="root",
#                database_schema="nasa_space_exploration_database")

result = engine.ask("What were total sales last month?")
print(result.answer, result.sql, result.data)

engine.etl("Load ./sales.csv into table monthly_sales and normalize dates")
```

## Run the demo app

1. Start Ollama and ensure the configured model exists (default in `local.yaml` is `mistral`):

```bash
ollama serve
ollama pull mistral
# or override: set GENELYTICS_LLM__MODEL=<name from `ollama list`>
```

2. (Optional) Start the NASA MySQL demo DB:

```bash
cd project_config/nasa-docker-db
docker compose up -d
```

3. Install and launch:

```bash
pip install -e ".[demo]"
genelytics-demo
# or:
python -m genelytics.demo
```

Open http://127.0.0.1:5000 — or use curl:

Windows (PowerShell):

```powershell
curl -X POST -H "Content-Type: application/json" `
  -d '{"db_config": {"db_type": "mysql", "host": "localhost", "port": "3305", "username": "root", "password": "root", "database_schema": "nasa_space_exploration_database"}}' `
  http://127.0.0.1:5000/set_db_config
```

Unix:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"db_config": {"db_type": "mysql", "host": "localhost", "port": "3305", "username": "root", "password": "root", "database_schema": "nasa_space_exploration_database"}}' \
  http://127.0.0.1:5000/set_db_config
```

Ask a question:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"user_prompt": "Get all the Astronauts"}' \
  http://127.0.0.1:5000/user_prompt
```

Response shape: `{ "answer", "sql", "rows", "error", "result" }` (`result` is kept for template compatibility).

## Project layout

```
genelytics-ai/
├── pyproject.toml
├── config/environments/     # local | development | production YAML
├── src/genelytics/          # installable library
│   ├── engine.py            # AnalyticsEngine facade
│   ├── config/              # Settings + YAML loader
│   ├── llm/                 # provider factory
│   ├── db/                  # URI builder + QueryExecutor
│   ├── agents/              # SQL + ETL + intent router + sessions
│   ├── etl/                 # pandas pipeline helpers
│   ├── prompts/             # dialect-aware SQL prompts
│   └── demo/                # Flask UI entrypoint
├── examples/demo_app/       # thin re-export of the demo
├── project_config/          # NASA docker DB + few-shot prompts
├── templates/               # demo HTML
└── tests/
```

## Contributing

```bash
pip install -e ".[demo,dev]"
pytest
```

- Unit tests for config and SQL safety run without Ollama.
- `tests/test_engine_smoke.py` skips automatically if Ollama is down.
- Prefer small, focused PRs; keep dependencies lean (no torch/tensorflow/spark in core).

## License

MIT — see [LICENSE](LICENSE).
