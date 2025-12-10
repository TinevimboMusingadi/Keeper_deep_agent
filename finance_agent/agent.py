"""Root finance agent orchestrator."""

from pathlib import Path

from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from .config import DEFAULT_MODEL, ensure_workspace
from .subagents import build_keeper_subagent, build_clerk_subagent


def _create_model(model_name: str):
    """Create a model instance using init_chat_model."""
    # Use the langchain init_chat_model for proper initialization
    return init_chat_model(model=f"anthropic:{model_name}", temperature=0.0)

ROOT_PROMPT = """
You are the Finance Orchestrator (root agent).
- Plan with write_todos, then delegate to subagents via task().
- Do not parse files yourself; delegate ingestion to Keeper.
- Delegate report generation to Clerk after Keeper prepares data.
- File conventions:
  - Ingested text/logs under /ingest and /logs.
  - Reports under /reports (e.g., balance_sheet.md).
- After delegation, read the produced files and synthesize a concise user-facing answer.
- Summaries should cite which files were produced and where they are saved.
"""


def create_finance_agent(
    model_name: str = DEFAULT_MODEL,
    workspace_root: str | None = None,
) -> any:
    if workspace_root:
        root_dir = Path(workspace_root).resolve()
        root_dir.mkdir(parents=True, exist_ok=True)
        for subdir in ("ingest", "reports", "logs"):
            (root_dir / subdir).mkdir(parents=True, exist_ok=True)
    else:
        root_dir = ensure_workspace()
    backend = FilesystemBackend(root_dir=str(root_dir))

    # Create actual model instance
    model = _create_model(model_name)

    keeper = build_keeper_subagent(model=model, backend=backend)
    clerk = build_clerk_subagent(model=model, backend=backend)

    return create_deep_agent(
        model=model,
        backend=backend,
        subagents=[keeper, clerk],
        system_prompt=ROOT_PROMPT,
    )


