"""
FastAPI Server for AI Kustomize Agent
Exposes the agent's capabilities as a REST API for the Web UI.
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from agents.intent_parser import IntentParser
from agents.patch_generator import PatchGenerator
from scanners.cluster_scanner import ClusterScanner
from outputs.kustomize import KustomizeGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AI Kustomize Agent API",
    description="Natural language to Kubernetes patches",
    version="1.0.0"
)

# CORS - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
intent_parser = IntentParser()
patch_generator = PatchGenerator()
kustomize_gen = KustomizeGenerator()

try:
    scanner = ClusterScanner()
    cluster_connected = True
except Exception as e:
    logger.warning(f"Could not connect to cluster: {e}")
    scanner = None
    cluster_connected = False


# === Request/Response Models ===

class CommandRequest(BaseModel):
    command: str
    namespace: Optional[str] = None
    dry_run: bool = True


class PatchPreview(BaseModel):
    name: str
    kind: str
    namespace: str
    yaml: str
    diff: str


class CommandResponse(BaseModel):
    status: str
    message: Optional[str] = None
    intents: Optional[List[Dict[str, Any]]] = None
    patches: Optional[List[PatchPreview]] = None
    patches_count: int = 0


class HealthResponse(BaseModel):
    status: str
    cluster_connected: bool
    ai_provider: str


class NamespaceResponse(BaseModel):
    namespaces: List[str]


class ResourceResponse(BaseModel):
    resources: List[Dict[str, Any]]


# === Landing Page HTML ===
LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Kustomize Agent</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0d0d1a 0%, #1a1a35 100%);
            color: #f8fafc;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem;
        }
        .container { max-width: 900px; width: 100%; }
        .header { text-align: center; margin-bottom: 3rem; }
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #6366f1, #22d3ee);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .header p { color: #94a3b8; font-size: 1.1rem; }
        .status-bar { display: flex; justify-content: center; gap: 2rem; margin-bottom: 2rem; }
        .status-item {
            display: flex; align-items: center; gap: 0.5rem;
            background: rgba(30, 30, 60, 0.6);
            padding: 0.75rem 1.25rem; border-radius: 12px;
            border: 1px solid rgba(100, 100, 150, 0.2);
        }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; background: #22c55e; }
        .card {
            background: rgba(30, 30, 60, 0.6);
            border: 1px solid rgba(100, 100, 150, 0.2);
            border-radius: 16px; padding: 2rem; margin-bottom: 1.5rem;
            backdrop-filter: blur(20px);
        }
        .card h2 { font-size: 1.25rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; color: #94a3b8; }
        input, select, textarea {
            width: 100%; background: #151528;
            border: 1px solid rgba(100, 100, 150, 0.3);
            border-radius: 10px; padding: 0.875rem 1rem;
            color: #f8fafc; font-size: 1rem; font-family: inherit;
        }
        input:focus, select:focus, textarea:focus {
            outline: none; border-color: #6366f1;
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
        }
        .btn {
            background: linear-gradient(135deg, #6366f1, #22d3ee);
            color: white; border: none; padding: 1rem 2rem;
            border-radius: 12px; font-weight: 600; cursor: pointer;
            font-size: 1rem; transition: all 0.2s;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4); }
        .btn-secondary { background: transparent; border: 1px solid #6366f1; color: #6366f1; }
        .btn-row { display: flex; gap: 1rem; margin-top: 1rem; }
        .result {
            background: #0d0d1a; border-radius: 10px; padding: 1rem;
            margin-top: 1rem; font-family: monospace; font-size: 0.85rem;
            white-space: pre-wrap; max-height: 400px; overflow-y: auto; display: none;
        }
        .links { display: flex; gap: 1rem; justify-content: center; margin-top: 2rem; }
        .links a {
            color: #6366f1; text-decoration: none; padding: 0.5rem 1rem;
            border: 1px solid #6366f1; border-radius: 8px; transition: all 0.2s;
        }
        .links a:hover { background: #6366f1; color: white; }
        .examples { margin-top: 1rem; color: #64748b; font-size: 0.9rem; }
        .examples code { background: #1a1a35; padding: 0.25rem 0.5rem; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 AI Kustomize Agent</h1>
            <p>Natural language to Kubernetes patches</p>
        </div>
        <div class="status-bar">
            <div class="status-item">
                <div class="status-dot" id="clusterDot"></div>
                <span id="clusterStatus">Checking...</span>
            </div>
            <div class="status-item">
                <span>🤖 AI:</span>
                <span id="aiProvider">-</span>
            </div>
        </div>
        <div class="card">
            <h2>💬 Send a Command</h2>
            <div class="form-group">
                <label>Namespace (optional)</label>
                <input type="text" id="namespace" placeholder="e.g., agent-test">
            </div>
            <div class="form-group">
                <label>Command</label>
                <textarea id="command" rows="3" placeholder="Describe what you want to change..."></textarea>
            </div>
            <div class="examples">
                Examples: <code>Add label env=prod to all deployments</code> | 
                <code>Set memory limit 512Mi for my-nginx</code>
            </div>
            <div class="btn-row">
                <button class="btn" onclick="sendCommand(true)">👀 Preview</button>
                <button class="btn btn-secondary" onclick="sendCommand(false)">🚀 Apply</button>
            </div>
            <pre class="result" id="result"></pre>
        </div>
        <div class="links">
            <a href="/docs">📖 API Docs</a>
            <a href="/health">❤️ Health</a>
            <a href="/namespaces">📁 Namespaces</a>
        </div>
    </div>
    <script>
        fetch('/health').then(r => r.json()).then(data => {
            document.getElementById('clusterStatus').textContent = data.cluster_connected ? 'Connected' : 'Disconnected';
            document.getElementById('clusterDot').style.background = data.cluster_connected ? '#22c55e' : '#ef4444';
            document.getElementById('aiProvider').textContent = data.ai_provider;
        });
        function sendCommand(dryRun) {
            const command = document.getElementById('command').value;
            const namespace = document.getElementById('namespace').value;
            const resultEl = document.getElementById('result');
            if (!command) { alert('Please enter a command'); return; }
            resultEl.style.display = 'block';
            resultEl.textContent = 'Processing...';
            fetch('/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command, namespace: namespace || null, dry_run: dryRun })
            }).then(r => r.json()).then(data => {
                let output = 'Status: ' + data.status + '\\nMessage: ' + data.message + '\\n\\n';
                if (data.patches && data.patches.length > 0) {
                    output += 'Patches:\\n';
                    data.patches.forEach(p => { output += '\\n--- ' + p.kind + '/' + p.name + ' ---\\n' + p.yaml + '\\n'; });
                }
                resultEl.textContent = output;
            }).catch(err => { resultEl.textContent = 'Error: ' + err.message; });
        }
    </script>
</body>
</html>
"""

# === API Endpoints ===

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """Serve the landing page."""
    return LANDING_PAGE_HTML


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        cluster_connected=cluster_connected,
        ai_provider=os.getenv("AI_PROVIDER", "azure")
    )


@app.get("/namespaces", response_model=NamespaceResponse)
async def list_namespaces():
    """List all namespaces in the cluster."""
    if not scanner:
        raise HTTPException(status_code=503, detail="Cluster not connected")
    
    try:
        namespaces = scanner.list_namespaces()
        return NamespaceResponse(namespaces=namespaces)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/resources/{namespace}", response_model=ResourceResponse)
async def list_resources(namespace: str, resource_type: str = "deployments"):
    """List resources in a namespace."""
    if not scanner:
        raise HTTPException(status_code=503, detail="Cluster not connected")
    
    try:
        resources = scanner.scan(
            resource_type=resource_type,
            namespace=namespace
        )
        # Simplify for API response
        simplified = []
        for r in resources:
            simplified.append({
                "name": r.get("metadata", {}).get("name"),
                "kind": r.get("kind"),
                "namespace": r.get("metadata", {}).get("namespace"),
                "labels": r.get("metadata", {}).get("labels", {}),
            })
        return ResourceResponse(resources=simplified)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """
    Execute a natural language command.
    Returns patch previews (dry_run=True) or applies them (dry_run=False).
    """
    logger.info(f"📝 Processing command: {request.command}")
    
    # Step 1: Parse intent with AI
    try:
        intent_data = intent_parser.parse(request.command)
        
        if intent_data.get("error"):
            return CommandResponse(
                status="error",
                message=f"Failed to parse intent: {intent_data['error']}"
            )
        
        intents = intent_data.get("intents", [])
        if not intents:
            return CommandResponse(
                status="warning",
                message="No intents found in request"
            )
    except Exception as e:
        logger.error(f"Intent parsing failed: {e}")
        return CommandResponse(status="error", message=str(e))
    
    # Step 2: Scan and generate patches
    if not scanner:
        return CommandResponse(
            status="error",
            message="Cluster not connected"
        )
    
    all_patches = []
    for intent in intents:
        try:
            resources = scanner.scan(
                resource_type=intent.get("resource_type", "deployments"),
                namespace=request.namespace or intent.get("namespace"),
                labels=intent.get("label_selector")
            )
            
            if resources:
                patches = patch_generator.generate(intent, resources)
                all_patches.extend(patches)
        except Exception as e:
            logger.error(f"Patch generation failed for intent: {e}")
    
    if not all_patches:
        return CommandResponse(
            status="warning",
            message="No patches generated",
            intents=[dict(i) for i in intents]
        )
    
    # Step 3: Apply if not dry run
    if not request.dry_run:
        for patch in all_patches:
            try:
                scanner.apply_patch(patch)
                logger.info(f"✅ Applied: {patch['name']}")
            except Exception as e:
                logger.error(f"❌ Failed to apply {patch['name']}: {e}")
    
    # Build response
    patch_previews = [
        PatchPreview(
            name=p["name"],
            kind=p["kind"],
            namespace=p["namespace"],
            yaml=p["yaml"],
            diff=p.get("diff", "")
        )
        for p in all_patches
    ]
    
    return CommandResponse(
        status="applied" if not request.dry_run else "preview",
        message=f"{'Applied' if not request.dry_run else 'Generated'} {len(all_patches)} patches",
        intents=[dict(i) for i in intents],
        patches=patch_previews,
        patches_count=len(all_patches)
    )


@app.post("/apply")
async def apply_patches(request: CommandRequest):
    """Shortcut to apply patches directly."""
    request.dry_run = False
    return await execute_command(request)


# === Run Server ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
