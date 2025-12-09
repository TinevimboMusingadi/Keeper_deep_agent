# Finance Agent Setup Guide

## ✅ Current Status

**Core Accounting Tools**: Working correctly (tested with Python 3.10.4)
- Symbolic accounting engine (ledger, journals, reports)
- Document parser (PDF/CSV)
- All finance tools functional

**Deep Agents Integration**: Requires Python 3.11+
- The `deepagents` package requires Python >=3.11,<4.0
- Current system Python: 3.10.4
- **Solution**: Install Python 3.11+ or use a Python version manager

## Installation Steps

### Option 1: Install Python 3.11+ via uv (Recommended)

```powershell
# Install Python 3.11.13
uv python install 3.11.13

# Create venv with Python 3.11
uv venv --python 3.11.13
.venv\Scripts\Activate.ps1

# Install deepagents from local source
uv pip install -e libs/deepagents

# Install other dependencies
uv pip install pdfplumber PyPDF2 pandas openpyxl
```

### Option 2: Install Python 3.11+ Manually

1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Install it
3. Create venv pointing to that Python:
   ```powershell
   C:\Python311\python.exe -m venv .venv
   .venv\Scripts\Activate.ps1
   uv pip install -e libs/deepagents
   ```

### Option 3: Use System Python 3.11+ if Available

If you have Python 3.11+ installed elsewhere:
```powershell
uv venv --python C:\Path\To\Python311\python.exe
.venv\Scripts\Activate.ps1
uv pip install -e libs/deepagents
```

## Testing

### Test Core Tools (Works with Python 3.10+)
```powershell
uv run python test_tools_only.py
```

### Test Full Agent (Requires Python 3.11+)
```powershell
# After setting up Python 3.11+ environment
uv run python test_finance_agent.py
```

### Run LangGraph Server (Requires Python 3.11+)
```powershell
langgraph dev
```

## Current Test Results

✅ **Core Accounting Engine**: All tests passing
- Chart of Accounts creation
- Journal entry recording
- Balance computation
- Trial balance generation
- Financial report generation

## Next Steps

1. Install Python 3.11+ (see options above)
2. Set up virtual environment with Python 3.11+
3. Install deepagents package
4. Run full agent tests
5. Start LangGraph server for UI integration

