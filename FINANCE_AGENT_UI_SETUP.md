# Keeper Finance Agent - UI Setup Complete

## ✅ What's Been Done

### 1. **UI Customization for Finance Agent** ✓
- **Branding Updated**: Changed "Deep Agent UI" → "Keeper Finance Agent"
- **Welcome Message**: Updated to "Welcome to Keeper Finance Agent" with finance-specific description
- **Default Configuration**: Pre-filled with:
  - Deployment URL: `your_venv_name\Scripts\activate.bat
If using PowerShell.
Code

    your_venv_name\Scripts\Activate.ps1
(You might need to adjust your PowerShell execution policy if you encounter errors. This can be done by running Set-ExecutionPolicy RemoteSigned -Scope CurrentUser in an administrator PowerShell session.)
2. On macOS and Linux (Bash or Zsh):
Code

source your_venv_name/bin/activate
Explanation:
your_venv_name: Replace this with the actual name of your virtual environment directory (e.g., venv, env, myproject_env).
Scripts vs. bin: Windows virtual environments store activation scripts in a Scripts directory, while macOS and Linux use bin.
activate.bat / Activate.ps1 / activate: These are the specific activation scripts for each platform and shell.
source: On Unix-like systems, source is used to execute a script within the current shell, allowing it to modify the shell's environment variables (like PATH), which is necessary for the virtual environment to function correctly.
After activation:
Your terminal prompt will typically change to include the name of the activated virtual environment in parentheses (e.g., (your_venv_name) $), indicating that you are now working within that isolated environment. Any Python commands or package installations (e.g., pip install package_name) will now apply only to this specific virtual environment.
To deactivate the virtual environment:
Simply type deactivate in your terminal and press Enter.
your_venv_name\Scripts\activate.bat
If using PowerShell.
Code

    your_venv_name\Scripts\Activate.ps1
(You might need to adjust your PowerShell execution policy if you encounter errors. This can be done by running Set-ExecutionPolicy RemoteSigned -Scope CurrentUser in an administrator PowerShell session.)
2. On macOS and Linux (Bash or Zsh):
Code

source your_venv_name/bin/activate
Explanation:
your_venv_name: Replace this with the actual name of your virtual environment directory (e.g., venv, env, myproject_env).
Scripts vs. bin: Windows virtual environments store activation scripts in a Scripts directory, while macOS and Linux use bin.
activate.bat / Activate.ps1 / activate: These are the specific activation scripts for each platform and shell.
source: On Unix-like systems, source is used to execute a script within the current shell, allowing it to modify the shell's environment variables (like PATH), which is necessary for the virtual environment to function correctly.
After activation:
Your terminal prompt will typically change to include the name of the activated virtual environment in parentheses (e.g., (your_venv_name) $), indicating that you are now working within that isolated environment. Any Python commands or package installations (e.g., pip install package_name) will now apply only to this specific virtual environment.
To deactivate the virtual environment:
Simply type deactivate in your terminal and press Enter.
http://127.0.0.1:2024`
  - Assistant ID: `finance`
- **Config Dialog**: Updated descriptions to mention "Keeper Finance Agent" and local development defaults

### 2. **Backend Server Status** ✓
- **LangGraph Server**: Running at `http://127.0.0.1:2024`
- **Assistant Registered**: `finance` assistant is active
- **API Endpoints**: Available at `/docs` for API documentation

### 3. **Files Modified**
- `deep-agents-ui/src/app/page.tsx` - Updated branding and welcome messages
- `deep-agents-ui/src/app/components/ConfigDialog.tsx` - Added default values and finance-specific descriptions

## 🚀 How to Use

### Starting the UI (if not already running):

```powershell
cd C:\Users\PC\Keeper_deep_agent\deep-agents-ui
yarn dev
```

The UI will start on:
- **Local**: `http://localhost:3000` (or 3001 if 3000 is busy)
- **Network**: `http://192.168.56.1:3001`

### First Time Setup:

1. **Open the UI** in your browser
2. **Configuration Dialog** will appear (or click Settings)
3. **Default values are pre-filled**:
   - Deployment URL: `http://127.0.0.1:2024`
   - Assistant ID: `finance`
4. **Click Save** - settings are stored in browser localStorage

### Using the Finance Agent:

1. **Start a new thread** (click "New Thread" button)
2. **Ask finance questions**, for example:
   - "Process the transactions CSV in /ingest/transactions.csv and generate reports"
   - "Create a balance sheet for the last quarter"
   - "Audit the transactions in /ingest folder"
3. **Watch the agent work**:
   - Root agent plans with `write_todos`
   - Keeper subagent ingests documents
   - Clerk subagent generates financial reports
   - Files appear in the sidebar under `/reports`

## 📁 File Structure

The agent workspace is at: `C:\Users\PC\Keeper_deep_agent\finance_agent_workspace\`

```
finance_agent_workspace/
├── ingest/          # Documents to process (PDFs, CSVs)
├── reports/         # Generated reports (balance sheets, income statements)
└── logs/           # Agent activity logs
```

## 🔧 Troubleshooting

### If UI doesn't start:
1. **Check dependencies**: `yarn install` (may need network retry)
2. **Check port**: UI uses port 3000 or 3001
3. **Check LangGraph server**: Ensure `langgraph dev` is running

### If agent doesn't respond:
1. **Check API key**: Ensure `ANTHROPIC_API_KEY` is set in environment
2. **Check server logs**: Look at LangGraph server terminal for errors
3. **Check configuration**: Verify Deployment URL and Assistant ID in Settings

### Network Issues:
- If yarn install fails, try: `yarn cache clean` then retry
- Use `npm` instead of `yarn` if yarn continues to have issues

## 🎯 Next Steps

1. **Test the full workflow**:
   - Upload a CSV file to `/ingest/`
   - Ask agent to process it
   - Check generated reports in `/reports/`

2. **Customize further** (optional):
   - Add finance-specific icons/colors
   - Customize tool call displays for Keeper/Clerk
   - Add finance-specific file type handling

3. **Production deployment**:
   - Deploy LangGraph server to cloud
   - Update Deployment URL in UI config
   - Set up persistent storage for workspace

## 📝 Notes

- **UI runs on**: Next.js 15 with Turbopack
- **Backend runs on**: LangGraph in-memory server (for development)
- **Storage**: Agent workspace uses local filesystem (FilesystemBackend)
- **Subagents**: Keeper (ingestion) and Clerk (accounting/reporting) are configured

