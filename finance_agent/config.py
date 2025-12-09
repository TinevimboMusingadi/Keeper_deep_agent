import os
from pathlib import Path

# Default model; override with FINANCE_AGENT_MODEL
DEFAULT_MODEL = os.getenv("FINANCE_AGENT_MODEL", "claude-sonnet-4-5-20250929")

# Workspace root for all agents; override with FINANCE_AGENT_ROOT
WORKSPACE_ROOT = Path(os.getenv("FINANCE_AGENT_ROOT", "./finance_agent_workspace")).resolve()


def ensure_workspace() -> Path:
    """Create workspace dirs for shared agent state."""
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    for subdir in ("ingest", "reports", "logs"):
        (WORKSPACE_ROOT / subdir).mkdir(parents=True, exist_ok=True)
    return WORKSPACE_ROOT


