# UmaBot Skills

Official skill collection for [UmaBot](https://github.com/yourusername/umabot) — a self-hosted personal AI assistant.

Each skill is a self-contained module with its own scripts, dependencies, and configuration. Skills run as isolated subprocesses with their own virtual environment.

## Available Skills

| Skill | Description | Risk Level |
|-------|-------------|------------|
| [todo_assistant](todo_assistant/) | Create, list, and update todos persisted in a JSONL file | yellow |
| [news](news/) | Fetch latest news from Google News via SerpAPI | green |
| [finance](finance/) | Fetch finance quotes from Google Finance via SerpAPI | green |

## Installation

### Prerequisites

- UmaBot installed and configured (`make install && make init` in the umabot repo)
- UmaBot CLI available as `umabot` (via the `.venv`)

### Install a skill

From the umabot project directory:

```bash
# Install from local path
umabot skills install /path/to/umabot-skills/news

# Install from this repo (all skills are subdirectories)
umabot skills install ./umabot-skills/todo_assistant
```

Or using the Makefile in the umabot repo:

```bash
make skills-install SKILL=/path/to/umabot-skills/news
```

### Configure a skill

After installation, configure skill-specific settings:

```bash
umabot skills configure news
```

Or edit `~/.umabot/config.yaml` directly:

```yaml
skill_configs:
  news:
    args:
      interests: "technology,science,AI,climate"
      country: "us"
      language: "en"
    env:
      SERPAPI_API_KEY: "your-api-key-here"
```

For secrets like API keys, prefer setting them as environment variables rather than storing them in the config file:

```bash
export SERPAPI_API_KEY="your-api-key-here"
```

### Verify installation

```bash
# List all installed skills
umabot skills list

# Validate skill manifests
umabot skills lint
```

### Reload after install

If UmaBot is already running, reload to pick up the new skill:

```bash
umabot reload
# or
make reload
```

## Skill Structure

Each skill follows this directory layout:

```
my-skill/
├── SKILL.md           # Manifest (required) — YAML frontmatter + docs
├── requirements.txt   # Python dependencies (installed in isolated .venv)
└── scripts/
    ├── my_script.py   # Script entry points
    └── common.py      # Shared helpers (optional)
```

### SKILL.md Manifest

The `SKILL.md` file contains YAML frontmatter that defines:

- **name** — unique skill identifier
- **version** — semver version string
- **description** — brief description
- **risk_level** — `green` (auto-approve), `yellow` (auto with allowlist), `red` (requires owner confirmation)
- **triggers** — keywords that activate the skill
- **scripts** — entry points with input schemas and argument mappings
- **install_config** — configuration args and environment variables
- **runtime** — timeout and validation settings

### Script I/O Protocol

Scripts receive JSON on stdin and emit JSON on stdout:

**Input:**
```json
{
  "input": { "query": "AI news", "limit": 5 },
  "config": { "country": "us", "interests": "technology" }
}
```

**Output:**
```json
{
  "ok": true,
  "message": "Human-readable result",
  "articles": [...]
}
```

## Developing a New Skill

1. Create a new directory under this repo with the skill name
2. Add a `SKILL.md` with the required YAML frontmatter
3. Add a `requirements.txt` (can be empty if no external deps)
4. Write scripts under `scripts/` following the stdin JSON / stdout JSON protocol
5. Test locally, then install with `umabot skills install ./your-skill`

Use the existing skills as reference:
- **todo_assistant** — file-based persistence, no external APIs
- **news** — external API integration with SerpAPI, environment variable secrets
- **finance** — external finance quote lookups via SerpAPI, environment variable secrets
