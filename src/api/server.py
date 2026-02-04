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


# === API Endpoints ===

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
