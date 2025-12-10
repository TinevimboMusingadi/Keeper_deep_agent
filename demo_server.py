"""
Enhanced Finance Agent Demo Server with:
- Demo Mode (pre-canned responses) vs Live Mode (real LLM)
- Document viewing & upload
- Reasoning/thinking display
- Benchmark testing
- File generation & download

Run with: uv run python demo_server.py
"""
import os
import json
import uuid
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Import the finance agent
from finance_agent.agent import create_finance_agent

# Store threads, documents, files in memory
threads: dict = {}
documents: dict = {}
generated_files: dict = {}
benchmark_results: list = []
agent = None

# Mode: "demo" or "live"
current_mode = "demo"

# Sample documents directory
SAMPLE_DOCS_DIR = Path("./sample_documents")
DEMO_WORKSPACE = Path("./demo_workspace")
GENERATED_FILES_DIR = DEMO_WORKSPACE / "generated"

# ============ DEMO RESPONSES ============
DEMO_RESPONSES = {
    "hello": {
        "content": """👋 Hello! I'm **Keeper**, your AI-powered finance agent!

I can help you with:
- 📄 **Document Processing** - Parse invoices, receipts, bank statements
- 📊 **Financial Analysis** - Generate reports, trial balances, income statements
- 🔢 **Transaction Management** - Record journal entries, classify accounts
- 📈 **Reporting** - Create financial summaries and insights

Try asking me to analyze a document from the sidebar, or click one of the quick actions below!""",
        "reasoning": ["Identified greeting message", "Prepared introduction response"],
        "tool_calls": [],
        "duration_ms": 245
    },
    "invoice": {
        "content": """📋 **Invoice Analysis - INV-2024-001**

Based on the invoice document, here are the key details:

| Field | Value |
|-------|-------|
| **Vendor** | TechSupplies Inc. |
| **Invoice #** | INV-2024-001 |
| **Date** | December 5, 2024 |
| **Due Date** | December 20, 2024 |
| **Payment Terms** | Net 15 |

**Line Items:**
| Item | Qty | Unit Price | Amount |
|------|-----|------------|--------|
| Office Laptops (Dell XPS 15) | 5 | $1,299.00 | $6,495.00 |
| Wireless Keyboards | 10 | $49.99 | $499.90 |
| USB-C Docking Stations | 5 | $189.00 | $945.00 |
| Office Software Licenses | 5 | $299.00 | $1,495.00 |

**Totals:**
- Subtotal: **$9,434.90**
- Tax (8.5%): **$801.97**
- **Total Due: $10,236.87**

📌 *This invoice should be recorded as an Accounts Payable entry.*""",
        "reasoning": ["Parsed invoice document structure", "Extracted vendor information", "Calculated line item totals", "Identified tax rate and computed tax amount", "Determined accounting treatment"],
        "tool_calls": [{"name": "parse_document", "args": {"file": "invoice_001.txt"}}],
        "duration_ms": 1847,
        "generates_file": {
            "name": "invoice_analysis.json",
            "content": {
                "invoice_number": "INV-2024-001",
                "vendor": "TechSupplies Inc.",
                "vendor_address": "123 Innovation Drive, San Francisco, CA 94105",
                "vendor_tax_id": "12-3456789",
                "customer": "Acme Corporation",
                "date": "2024-12-05",
                "due_date": "2024-12-20",
                "items": [
                    {"description": "Office Laptops (Dell XPS 15)", "qty": 5, "unit_price": 1299.00, "amount": 6495.00},
                    {"description": "Wireless Keyboards", "qty": 10, "unit_price": 49.99, "amount": 499.90},
                    {"description": "USB-C Docking Stations", "qty": 5, "unit_price": 189.00, "amount": 945.00},
                    {"description": "Office Software Licenses", "qty": 5, "unit_price": 299.00, "amount": 1495.00}
                ],
                "subtotal": 9434.90,
                "tax_rate": 0.085,
                "tax_amount": 801.97,
                "total": 10236.87,
                "payment_terms": "Net 15"
            }
        }
    },
    "trial_balance": {
        "content": """📊 **Trial Balance - December 2024**

Generated from transactions.csv:

| Account Code | Account Name | Debit | Credit |
|--------------|--------------|-------|--------|
| 1010 | Cash | $51,339.50 | |
| 1110 | Accounts Receivable | $7,500.00 | |
| 1510 | Equipment | $10,236.87 | |
| 2010 | Accounts Payable | | $10,236.87 |
| 2110 | Unearned Revenue | | $5,000.00 |
| 3010 | Owner Equity | | $50,000.00 |
| 4010 | Service Revenue | | $20,000.00 |
| 4020 | Interest Income | | $125.00 |
| 6010 | Office Supplies | $450.00 | |
| 6020 | Rent Expense | $3,500.00 | |
| 6030 | Utilities | $285.50 | |
| 6040 | Salaries Expense | $8,500.00 | |
| 6050 | Insurance | $1,200.00 | |
| 6060 | Marketing | $2,000.00 | |
| 6070 | Repairs & Maintenance | $350.00 | |
| | **TOTALS** | **$85,361.87** | **$85,361.87** |

✅ **Trial balance is in balance!** Debits = Credits""",
        "reasoning": ["Loaded transactions from CSV", "Grouped by account", "Calculated running balances", "Verified debits equal credits", "Formatted trial balance report"],
        "tool_calls": [
            {"name": "parse_tabular", "args": {"file": "transactions.csv"}},
            {"name": "generate_financial_reports", "args": {"report_type": "trial_balance"}}
        ],
        "duration_ms": 2341,
        "generates_file": {
            "name": "trial_balance_dec2024.csv",
            "content": "account_code,account_name,debit,credit\n1010,Cash,51339.50,\n1110,Accounts Receivable,7500.00,\n1510,Equipment,10236.87,\n2010,Accounts Payable,,10236.87\n2110,Unearned Revenue,,5000.00\n3010,Owner Equity,,50000.00\n4010,Service Revenue,,20000.00\n4020,Interest Income,,125.00\n6010,Office Supplies,450.00,\n6020,Rent Expense,3500.00,\n6030,Utilities,285.50,\n6040,Salaries Expense,8500.00,\n6050,Insurance,1200.00,\n6060,Marketing,2000.00,\n6070,Repairs & Maintenance,350.00,\nTOTALS,,85361.87,85361.87"
        }
    },
    "income_statement": {
        "content": """📈 **Income Statement - December 2024**

**REVENUE**
| Account | Amount |
|---------|--------|
| Service Revenue | $20,000.00 |
| Interest Income | $125.00 |
| **Total Revenue** | **$20,125.00** |

**EXPENSES**
| Account | Amount |
|---------|--------|
| Office Supplies | $450.00 |
| Rent Expense | $3,500.00 |
| Utilities | $285.50 |
| Salaries Expense | $8,500.00 |
| Insurance | $1,200.00 |
| Marketing | $2,000.00 |
| Repairs & Maintenance | $350.00 |
| **Total Expenses** | **$16,285.50** |

---
### 💰 **Net Income: $3,839.50**

The company is profitable this month with a profit margin of **19.1%**.""",
        "reasoning": ["Extracted revenue accounts (4xxx)", "Extracted expense accounts (6xxx)", "Summed revenue total", "Summed expense total", "Calculated net income", "Computed profit margin percentage"],
        "tool_calls": [
            {"name": "parse_tabular", "args": {"file": "transactions.csv"}},
            {"name": "generate_financial_reports", "args": {"report_type": "income_statement"}}
        ],
        "duration_ms": 1923,
        "generates_file": {
            "name": "income_statement_dec2024.json",
            "content": {
                "period": "December 2024",
                "revenue": {
                    "service_revenue": 20000.00,
                    "interest_income": 125.00,
                    "total": 20125.00
                },
                "expenses": {
                    "office_supplies": 450.00,
                    "rent": 3500.00,
                    "utilities": 285.50,
                    "salaries": 8500.00,
                    "insurance": 1200.00,
                    "marketing": 2000.00,
                    "repairs": 350.00,
                    "total": 16285.50
                },
                "net_income": 3839.50,
                "profit_margin": 0.191
            }
        }
    },
    "bank_reconciliation": {
        "content": """🏦 **Bank Reconciliation - December 2024**

**Bank Statement Balance:** $58,839.50
**Book Balance:** $51,339.50

**Reconciling Items:**

| Item | Amount | Note |
|------|--------|------|
| Equipment Purchase (A/P) | +$10,236.87 | Not yet paid from bank |
| Client Invoice #1001 | -$7,500.00 | Recorded but not deposited |
| Unearned Revenue | +$5,000.00 | Already in bank |
| **Adjusted Book Balance** | **$59,076.37** |

⚠️ **Discrepancy Found: $236.87**

This may be due to:
- Bank fees not yet recorded
- Timing differences in posting
- Potential data entry error

📋 *Recommendation: Review December transactions for missing entries.*""",
        "reasoning": ["Loaded bank statement", "Loaded book transactions", "Identified unreconciled items", "Calculated adjustments", "Found discrepancy", "Generated recommendations"],
        "tool_calls": [
            {"name": "parse_document", "args": {"file": "bank_statement_dec2024.txt"}},
            {"name": "parse_tabular", "args": {"file": "transactions.csv"}}
        ],
        "duration_ms": 2876
    },
    "classify": {
        "content": """🏷️ **Transaction Classification Results**

Analyzed 13 transactions from transactions.csv:

**By Account Type:**
| Type | Count | Total |
|------|-------|-------|
| 💰 Assets | 5 | $69,076.37 |
| 💳 Liabilities | 2 | $15,236.87 |
| 📊 Equity | 1 | $50,000.00 |
| 📈 Revenue | 3 | $20,125.00 |
| 📉 Expenses | 7 | $16,285.50 |

**Classification Breakdown:**
- ✅ All transactions properly follow double-entry accounting
- ✅ All debits have matching credits
- ✅ Account codes match chart of accounts

**Top Expense Categories:**
1. Salaries - $8,500.00 (52.2%)
2. Rent - $3,500.00 (21.5%)
3. Marketing - $2,000.00 (12.3%)""",
        "reasoning": ["Loaded chart of accounts", "Matched each transaction to account type", "Verified double-entry compliance", "Calculated category totals", "Ranked expense categories"],
        "tool_calls": [
            {"name": "parse_tabular", "args": {"file": "transactions.csv"}},
            {"name": "parse_tabular", "args": {"file": "chart_of_accounts.csv"}}
        ],
        "duration_ms": 1654
    },
    "default": {
        "content": """I understand you're asking about financial matters. In **Demo Mode**, I can show you these pre-built examples:

🎯 **Try these commands:**
- "Analyze the invoice" - Parse invoice_001.txt
- "Generate trial balance" - Create trial balance from transactions
- "Create income statement" - P&L report
- "Reconcile bank statement" - Bank reconciliation
- "Classify transactions" - Categorize by account type

💡 **Or switch to Live Mode** (toggle in header) to use the real AI!

*In Live Mode, I'll actually process your request using Claude and can handle any financial question.*""",
        "reasoning": ["Query not matched to demo response", "Provided available demo options"],
        "tool_calls": [],
        "duration_ms": 156
    }
}


def get_demo_response(message: str) -> dict:
    """Match message to demo response."""
    msg = message.lower()
    
    if any(w in msg for w in ["hello", "hi", "hey", "help", "what can you"]):
        return DEMO_RESPONSES["hello"]
    elif any(w in msg for w in ["invoice", "vendor", "total amount", "due"]):
        return DEMO_RESPONSES["invoice"]
    elif any(w in msg for w in ["trial balance", "balance sheet"]):
        return DEMO_RESPONSES["trial_balance"]
    elif any(w in msg for w in ["income statement", "profit", "loss", "p&l", "revenue"]):
        return DEMO_RESPONSES["income_statement"]
    elif any(w in msg for w in ["bank", "reconcil"]):
        return DEMO_RESPONSES["bank_reconciliation"]
    elif any(w in msg for w in ["classif", "categoriz", "account type"]):
        return DEMO_RESPONSES["classify"]
    else:
        return DEMO_RESPONSES["default"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup."""
    global agent, documents
    print("🚀 Starting Finance Agent Demo Server...")
    print(f"   API Key: {os.environ.get('ANTHROPIC_API_KEY', '')[:20]}...")
    
    # Create directories
    DEMO_WORKSPACE.mkdir(exist_ok=True)
    GENERATED_FILES_DIR.mkdir(exist_ok=True)
    for subdir in ("ingest", "reports", "logs"):
        (DEMO_WORKSPACE / subdir).mkdir(exist_ok=True)
    
    # Load sample documents
    if SAMPLE_DOCS_DIR.exists():
        for doc_path in SAMPLE_DOCS_DIR.iterdir():
            if doc_path.is_file():
                try:
                    content = doc_path.read_text(encoding='utf-8')
                    documents[doc_path.name] = {
                        "name": doc_path.name,
                        "path": str(doc_path),
                        "content": content,
                        "size": len(content),
                        "type": doc_path.suffix[1:] if doc_path.suffix else "txt"
                    }
                    print(f"   📄 Loaded: {doc_path.name}")
                except Exception as e:
                    print(f"   ⚠️ Failed to load {doc_path.name}: {e}")
    
    # Initialize agent for live mode
    try:
        agent = create_finance_agent(workspace_root=str(DEMO_WORKSPACE))
        print("✅ Agent initialized!")
    except Exception as e:
        print(f"⚠️ Agent init failed (demo mode still works): {e}")
        agent = None
    
    print(f"   📁 {len(documents)} sample documents loaded")
    print(f"   🎭 Starting in DEMO MODE (no LLM costs)")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="Finance Agent Demo",
    description="Demo server with Demo/Live modes, document viewing, and file generation",
    lifespan=lifespan
)

# Allow CORS for the UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    type: str = "human"
    content: str


class ThreadInput(BaseModel):
    messages: list[Message]


class RunInput(BaseModel):
    assistant_id: str = "finance"
    input: ThreadInput


class ModeRequest(BaseModel):
    mode: str  # "demo" or "live"


# ============ Mode Endpoints ============

@app.get("/mode")
async def get_mode():
    """Get current mode."""
    return {"mode": current_mode}


@app.post("/mode")
async def set_mode(request: ModeRequest):
    """Set demo or live mode."""
    global current_mode
    if request.mode not in ["demo", "live"]:
        raise HTTPException(status_code=400, detail="Mode must be 'demo' or 'live'")
    current_mode = request.mode
    return {"mode": current_mode, "message": f"Switched to {current_mode.upper()} mode"}


# ============ Thread/Agent Endpoints ============

@app.get("/ok")
async def health_check():
    """Health check endpoint."""
    return {"ok": True, "mode": current_mode, "documents_loaded": len(documents)}


@app.post("/threads")
async def create_thread():
    """Create a new conversation thread."""
    thread_id = str(uuid.uuid4())
    threads[thread_id] = {
        "thread_id": thread_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "messages": [],
        "reasoning_steps": [],
        "documents_used": [],
        "generated_files": [],
        "status": "idle"
    }
    return threads[thread_id]


@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    """Get thread details."""
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail="Thread not found")
    return threads[thread_id]


@app.post("/threads/{thread_id}/runs/wait")
async def run_agent(thread_id: str, run_input: RunInput):
    """Run the agent and wait for completion."""
    global current_mode
    
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    thread = threads[thread_id]
    thread["status"] = "running"
    thread["updated_at"] = datetime.utcnow().isoformat()
    
    # Add user message
    user_msg = run_input.input.messages[-1]
    user_content = user_msg.content
    
    thread["messages"].append({
        "type": "human",
        "content": user_content,
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    start_time = time.time()
    
    if current_mode == "demo":
        # DEMO MODE - Use pre-canned responses
        demo_resp = get_demo_response(user_content)
        
        # Simulate thinking time
        time.sleep(0.5 + (demo_resp["duration_ms"] / 5000))
        
        reasoning_step = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "input": user_content,
            "thinking": demo_resp["reasoning"],
            "tool_calls": demo_resp["tool_calls"],
            "duration_ms": demo_resp["duration_ms"],
            "mode": "demo"
        }
        
        ai_response = {
            "type": "ai",
            "content": demo_resp["content"],
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "tool_calls": demo_resp["tool_calls"]
        }
        
        # Generate file if applicable
        if "generates_file" in demo_resp:
            file_info = demo_resp["generates_file"]
            file_id = str(uuid.uuid4())[:8]
            file_name = file_info["name"]
            file_content = file_info["content"]
            
            # Save to disk
            if isinstance(file_content, dict):
                file_path = GENERATED_FILES_DIR / file_name
                file_path.write_text(json.dumps(file_content, indent=2))
            else:
                file_path = GENERATED_FILES_DIR / file_name
                file_path.write_text(str(file_content))
            
            generated_files[file_id] = {
                "id": file_id,
                "name": file_name,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "created_at": datetime.utcnow().isoformat(),
                "thread_id": thread_id
            }
            
            thread["generated_files"].append(file_id)
            ai_response["generated_file"] = generated_files[file_id]
        
        thread["messages"].append(ai_response)
        thread["reasoning_steps"].append(reasoning_step)
        thread["status"] = "idle"
        
        return {"thread_id": thread_id, "status": "completed", "mode": "demo", "duration_ms": demo_resp["duration_ms"]}
    
    else:
        # LIVE MODE - Use real LLM
        if agent is None:
            raise HTTPException(status_code=500, detail="Agent not initialized. Check API key.")
        
        reasoning_step = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "input": user_content,
            "thinking": [],
            "tool_calls": [],
            "duration_ms": 0,
            "mode": "live"
        }
        
        try:
            # Build messages for the agent
            agent_messages = [
                {"type": msg["type"], "content": msg["content"]}
                for msg in thread["messages"]
            ]
            
            # Invoke the agent
            result = agent.invoke({"messages": agent_messages})
            
            # Capture duration
            reasoning_step["duration_ms"] = int((time.time() - start_time) * 1000)
            
            # Extract response and tool calls
            if "messages" in result:
                for msg in result["messages"]:
                    if hasattr(msg, "type"):
                        if msg.type == "ai":
                            # Check for tool calls
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    reasoning_step["tool_calls"].append({
                                        "name": tc.get("name", "unknown"),
                                        "args": tc.get("args", {})
                                    })
                            
                            ai_response = {
                                "type": "ai",
                                "content": msg.content,
                                "id": str(uuid.uuid4()),
                                "timestamp": datetime.utcnow().isoformat(),
                                "tool_calls": reasoning_step["tool_calls"]
                            }
                            thread["messages"].append(ai_response)
            
            thread["reasoning_steps"].append(reasoning_step)
            thread["status"] = "idle"
            thread["updated_at"] = datetime.utcnow().isoformat()
            return {"thread_id": thread_id, "status": "completed", "mode": "live", "duration_ms": reasoning_step["duration_ms"]}
            
        except Exception as e:
            reasoning_step["duration_ms"] = int((time.time() - start_time) * 1000)
            reasoning_step["error"] = str(e)
            thread["reasoning_steps"].append(reasoning_step)
            thread["status"] = "error"
            thread["error"] = str(e)
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """Get the current state of a thread including reasoning."""
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    thread = threads[thread_id]
    return {
        "values": {
            "messages": thread["messages"],
            "reasoning": thread.get("reasoning_steps", []),
            "documents": thread.get("documents_used", []),
            "generated_files": [generated_files.get(fid) for fid in thread.get("generated_files", []) if fid in generated_files]
        },
        "status": thread["status"],
        "mode": current_mode
    }


@app.post("/threads/search")
async def search_threads(limit: int = 10):
    """Search/list threads."""
    sorted_threads = sorted(
        threads.values(), 
        key=lambda x: x.get("updated_at", x.get("created_at", "")),
        reverse=True
    )
    return sorted_threads[:limit]


# ============ Document Endpoints ============

@app.get("/documents")
async def list_documents():
    """List all available documents."""
    return list(documents.values())


@app.get("/documents/{doc_name}")
async def get_document(doc_name: str):
    """Get a specific document."""
    if doc_name not in documents:
        raise HTTPException(status_code=404, detail="Document not found")
    return documents[doc_name]


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a new document."""
    content = await file.read()
    try:
        text_content = content.decode('utf-8')
    except:
        text_content = content.decode('latin-1')
    
    doc_name = file.filename or f"upload_{uuid.uuid4().hex[:8]}.txt"
    documents[doc_name] = {
        "name": doc_name,
        "path": f"uploads/{doc_name}",
        "content": text_content,
        "size": len(text_content),
        "type": Path(doc_name).suffix[1:] if Path(doc_name).suffix else "txt",
        "uploaded_at": datetime.utcnow().isoformat()
    }
    
    # Save to workspace
    upload_path = DEMO_WORKSPACE / "ingest" / doc_name
    upload_path.write_text(text_content, encoding='utf-8')
    
    return {"success": True, "document": documents[doc_name]}


# ============ Generated Files Endpoints ============

@app.get("/files")
async def list_generated_files():
    """List all generated files."""
    return list(generated_files.values())


@app.get("/files/{file_id}")
async def get_file_info(file_id: str):
    """Get info about a generated file."""
    if file_id not in generated_files:
        raise HTTPException(status_code=404, detail="File not found")
    return generated_files[file_id]


@app.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """Download a generated file."""
    if file_id not in generated_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = generated_files[file_id]
    file_path = Path(file_info["path"])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File no longer exists")
    
    return FileResponse(
        path=str(file_path),
        filename=file_info["name"],
        media_type="application/octet-stream"
    )


@app.get("/files/{file_id}/content")
async def get_file_content(file_id: str):
    """Get content of a generated file."""
    if file_id not in generated_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = generated_files[file_id]
    file_path = Path(file_info["path"])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File no longer exists")
    
    content = file_path.read_text()
    return {"id": file_id, "name": file_info["name"], "content": content}


# ============ Benchmark Endpoints ============

@app.get("/benchmark/tests")
async def get_benchmark_tests():
    """Get available benchmark tests."""
    benchmark_file = SAMPLE_DOCS_DIR / "benchmark_tests.json"
    if benchmark_file.exists():
        return json.loads(benchmark_file.read_text())
    return {"test_cases": []}


@app.post("/benchmark/run/{test_id}")
async def run_benchmark_test(test_id: str, document_context: list[str] = []):
    """Run a specific benchmark test."""
    benchmark_file = SAMPLE_DOCS_DIR / "benchmark_tests.json"
    if not benchmark_file.exists():
        raise HTTPException(status_code=404, detail="Benchmark file not found")
    
    benchmarks = json.loads(benchmark_file.read_text())
    test = next((t for t in benchmarks["test_cases"] if t["id"] == test_id), None)
    
    if not test:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")
    
    # Simulate benchmark in demo mode
    if current_mode == "demo":
        time.sleep(0.5)
        result = {
            "test_id": test_id,
            "test_name": test["name"],
            "category": test["category"],
            "difficulty": test["difficulty"],
            "duration_ms": 1500 + (500 if test["difficulty"] == "hard" else 0),
            "expected": test["expected_outputs"],
            "status": "completed",
            "mode": "demo",
            "timestamp": datetime.utcnow().isoformat()
        }
        benchmark_results.append(result)
        return result
    
    # Live mode - actually run the test
    thread_id = str(uuid.uuid4())
    threads[thread_id] = {
        "thread_id": thread_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "messages": [],
        "reasoning_steps": [],
        "documents_used": document_context,
        "generated_files": [],
        "status": "idle",
        "benchmark_test": test_id
    }
    
    # Build context with documents
    context_parts = [f"Benchmark Test: {test['name']}\n"]
    for doc_name in document_context:
        if doc_name in documents:
            context_parts.append(f"\n--- Document: {doc_name} ---\n{documents[doc_name]['content']}\n")
    
    prompt = "\n".join(context_parts) + f"\n\nTask: {test['input']}"
    
    run_input = RunInput(
        assistant_id="finance",
        input=ThreadInput(messages=[Message(type="human", content=prompt)])
    )
    
    start_time = time.time()
    try:
        await run_agent(thread_id, run_input)
        duration = int((time.time() - start_time) * 1000)
        
        result = {
            "test_id": test_id,
            "test_name": test["name"],
            "category": test["category"],
            "difficulty": test["difficulty"],
            "thread_id": thread_id,
            "duration_ms": duration,
            "expected": test["expected_outputs"],
            "status": "completed",
            "mode": "live",
            "timestamp": datetime.utcnow().isoformat()
        }
        benchmark_results.append(result)
        return result
        
    except Exception as e:
        result = {
            "test_id": test_id,
            "test_name": test["name"],
            "status": "error",
            "error": str(e),
            "mode": current_mode,
            "timestamp": datetime.utcnow().isoformat()
        }
        benchmark_results.append(result)
        return result


@app.get("/benchmark/results")
async def get_benchmark_results():
    """Get all benchmark results."""
    return benchmark_results


@app.post("/benchmark/run-all")
async def run_all_benchmarks():
    """Run all benchmark tests."""
    benchmark_file = SAMPLE_DOCS_DIR / "benchmark_tests.json"
    if not benchmark_file.exists():
        raise HTTPException(status_code=404, detail="Benchmark file not found")
    
    benchmarks = json.loads(benchmark_file.read_text())
    results = []
    
    for test in benchmarks["test_cases"]:
        doc_context = []
        if "invoice" in test["input"].lower():
            doc_context.append("invoice_001.txt")
        if "transactions" in test["input"].lower() or "csv" in test["input"].lower():
            doc_context.append("transactions.csv")
        if "chart" in test["input"].lower() or "accounts" in test["input"].lower():
            doc_context.append("chart_of_accounts.csv")
        if "bank" in test["input"].lower():
            doc_context.append("bank_statement_dec2024.txt")
        
        result = await run_benchmark_test(test["id"], doc_context)
        results.append(result)
    
    return {
        "total_tests": len(results),
        "completed": len([r for r in results if r["status"] == "completed"]),
        "errors": len([r for r in results if r["status"] == "error"]),
        "mode": current_mode,
        "results": results
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  🏦 KEEPER FINANCE AGENT - DEMO SERVER")
    print("="*60)
    print("\n  Features:")
    print("    🎭 Demo Mode - Pre-canned responses (no LLM cost)")
    print("    🤖 Live Mode - Real AI (uses API key)")
    print("    📄 Document viewing & upload")
    print("    🧠 Reasoning/thinking display")
    print("    📊 Benchmark testing")
    print("    💾 File generation & download")
    print("\n  Endpoints:")
    print("    Backend: http://localhost:8000")
    print("    UI:      http://localhost:8080")
    print("    Docs:    http://localhost:8000/docs")
    print("\n  Press Ctrl+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
