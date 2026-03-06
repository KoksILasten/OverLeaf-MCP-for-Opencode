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
- [OpenCode](https://opencode.ai) installed

## Setup

### 1. Clone this repository

```bash
git clone https://github.com/KoksILasten/OverLeaf-MCP-for-Opencode.git
cd OverLeaf-MCP-for-Opencode
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

### 4. Configure OpenCode

Copy the example config into the root of the project you run OpenCode from (not this directory):

```bash
cp opencode.jsonc.example /path/to/your/project/opencode.jsonc
```

Then edit `opencode.jsonc` and fill in:

- **`command`** — absolute paths to the Python executable and `server.py` inside this repo. On Linux/macOS, use `venv/bin/python` instead of `venv/Scripts/python.exe`.
- **`OVERLEAF_GIT_URL`** — your Overleaf Git clone URL from step 3.
- **`OVERLEAF_TOKEN`** — your Git authentication token from step 3.

The file should look like this (with your real values):

```jsonc
// Windows
"command": ["C:/path/to/OverLeaf-MCP-for-Opencode/venv/Scripts/python.exe", "C:/path/to/OverLeaf-MCP-for-Opencode/server.py"]

// Linux / macOS
"command": ["/home/user/OverLeaf-MCP-for-Opencode/venv/bin/python", "/home/user/OverLeaf-MCP-for-Opencode/server.py"]
```

Full example:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "overleaf": {
      "type": "local",
      "command": ["<absolute-path-to-repo>/venv/Scripts/python.exe", "<absolute-path-to-repo>/server.py"],
      "timeout": 60000,
      "environment": {
        "OVERLEAF_GIT_URL": "https://git.overleaf.com/<your-project-id>",
        "OVERLEAF_TOKEN": "olp_<your-token>"
      }
    }
  }
}
```

**Important:** Add `opencode.jsonc` to your project's `.gitignore` since it contains credentials. Do **not** commit it.
#### **  Do **not** commit opencode.jsonc. **

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

- **"Missing Overleaf configuration"** -- `OVERLEAF_GIT_URL` and `OVERLEAF_TOKEN` environment variables are not set. Check your `opencode.jsonc` environment block.
- **Git clone fails with 401** -- Your token is invalid or expired. Generate a new one in Overleaf Account Settings > Git Integration.
- **MCP tool times out** -- The default MCP tool timeout may be too short for the initial clone. The `timeout` setting in `opencode.jsonc` controls the handshake timeout (set to 60000 for 60s). Subsequent read calls are instant.
- **Section not found** -- The `section_title` must exactly match the text inside `\section{...}`. Check for encoding issues with non-ASCII characters.
