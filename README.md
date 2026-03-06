# Overleaf MCP Server

An MCP server that lets AI coding agents (OpenCode, Claude, etc.) **read**, **list**, **summarize**, and **update** LaTeX sections in Overleaf projects via Git. Designed for theses, papers, and reports.

## Features

- **Read** any LaTeX file (preview or raw source)
- **List** all files in the project
- **Summarize** a section in plain language
- **Update** a specific section body without touching anything else
- **Cached clone** -- first call clones the repo, subsequent reads are instant

## Prerequisites

- Python 3.10+
- Git
- An Overleaf account with **Git integration** (requires a paid plan or institutional access)
- An Overleaf Git authentication token

## Setup

### 1. Clone this repository

```bash
git clone https://github.com/Aryan1718/OverLeaf-MCP.git
cd OverLeaf-MCP
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Get your Overleaf credentials

1. Open your Overleaf project
2. Go to **Menu > Git** and copy the Git clone URL (looks like `https://git.overleaf.com/<project-id>`)
3. Go to **Account Settings > Git Integration** and generate a Git authentication token

### 4. Create a `.env` file

Create a `.env` file in this directory (it is gitignored):

```
OVERLEAF_GIT_URL=https://git.overleaf.com/<your-project-id>
OVERLEAF_TOKEN=olp_<your-token>
```

### 5. Test the server

```bash
# Windows (PowerShell)
.\venv\Scripts\python server.py

# Linux / macOS
./venv/bin/python server.py
```

The server should start without errors (it communicates over stdio, so you won't see output unless there's an error).

## OpenCode Integration

To use this MCP server with [OpenCode](https://opencode.ai), create an `opencode.jsonc` file in your **project root** (the project you run OpenCode from, not this directory):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "overleaf": {
      "type": "local",
      "command": ["<path-to-this-repo>/venv/Scripts/python.exe", "<path-to-this-repo>/server.py"],
      "environment": {
        "OVERLEAF_GIT_URL": "https://git.overleaf.com/<your-project-id>",
        "OVERLEAF_TOKEN": "olp_<your-token>"
      }
    }
  }
}
```

Replace `<path-to-this-repo>` with the absolute path to this directory. On Linux/macOS, use `venv/bin/python` instead of `venv/Scripts/python.exe`.

**Important:** Add `opencode.jsonc` to your project's `.gitignore` since it contains credentials.

After creating the config, restart OpenCode. The MCP server tools will be available automatically.

### Usage in OpenCode

The read tools work instantly through MCP:

```
List my Overleaf files
Read the intro.tex file from Overleaf
```

The write tool (`update_overleaf_section`) may time out through MCP due to the git push latency to Overleaf's servers. If this happens, the agent can fall back to running the update directly via a Python script.

## Available Tools

| Tool | Description | Speed |
|---|---|---|
| `list_overleaf_files` | List all files in the project | Instant |
| `read_overleaf_file` | Read a file (preview or raw LaTeX) | Instant |
| `summarize_overleaf_section` | Summarize a section in plain text | Instant |
| `update_overleaf_section` | Replace a section body and push | ~2-3s (network) |

## How It Works

1. On startup, the server clones your Overleaf project via Git into a temp directory (background thread)
2. Read tools use the cached local clone -- no network access needed
3. The write tool pulls latest changes, edits the section, commits, and pushes back to Overleaf
4. A thread lock prevents race conditions between concurrent tool calls

## Troubleshooting

- **"Missing Overleaf configuration"** -- `OVERLEAF_GIT_URL` and `OVERLEAF_TOKEN` environment variables are not set. Check your `.env` file or `opencode.jsonc` environment block.
- **Git clone fails with 401** -- Your token is invalid or expired. Generate a new one in Overleaf Account Settings > Git Integration.
- **MCP tool times out** -- The default MCP tool timeout may be too short for the initial clone. The `timeout` setting in `opencode.jsonc` controls the handshake timeout (set to 60000 for 60s). Subsequent read calls are instant.
- **Section not found** -- The `section_title` must exactly match the text inside `\section{...}`. Check for encoding issues with non-ASCII characters.
