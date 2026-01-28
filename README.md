# 🔧 AI Kustomize Agent

**An intelligent agent that uses AI to generate Kustomize patches for bulk Kubernetes resource modifications.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat-square&logo=kubernetes&logoColor=white)]()
[![Kustomize](https://img.shields.io/badge/Kustomize-326CE5?style=flat-square&logo=kubernetes&logoColor=white)]()
[![Azure OpenAI](https://img.shields.io/badge/Azure_OpenAI-0078D4?style=flat-square&logo=microsoft-azure&logoColor=white)]()
[![Gemini](https://img.shields.io/badge/Gemini_AI-4285F4?style=flat-square&logo=google&logoColor=white)]()

---

## 🎯 The Problem

DevOps engineers frequently need to make bulk changes to Kubernetes resources:
- *"Add resource limits to all deployments"*
- *"Update all images to use private registry"*
- *"Add security context to all pods"*

**Current approach:** Manually edit dozens of YAML files or write complex patches.

**This agent:** Describe what you want in plain English → Get Kustomize patches automatically.

---

## ✨ How It Works

```
┌─────────────────────────────────────────────────────────────┐
│              "Add memory limit 512Mi to all deployments"    │
│                              ↓                              │
│                    [AI Intent Parser]                       │
│                              ↓                              │
│              [Cluster/File Scanner] - Find targets          │
│                              ↓                              │
│              [Patch Generator] - Create Kustomize patches   │
│                              ↓                              │
│              [Preview] - Show diff before applying          │
│                              ↓                              │
│              [Apply/Export] - Apply or save to files        │
└─────────────────────────────────────────────────────────────┘
```

---

## 💬 Example Commands

```bash
# Add resource limits to all deployments
ai-kustomize "Add memory limit 512Mi and CPU limit 500m to all deployments in staging"

# Update images to private registry
ai-kustomize "Update all images from docker.io to ecr.aws/mycompany"

# Add security context
ai-kustomize "Add runAsNonRoot: true to all pods"

# Add labels to all services
ai-kustomize "Add label 'team=platform' to all services in namespace api"

# Add probes
ai-kustomize "Add readiness probe on port 8080 to all deployments without one"
```

---

## 🛠️ Features

| Feature | Description |
|---------|-------------|
| **Natural Language** | Describe changes in plain English |
| **Multi-Resource** | Deployments, Pods, Services, ConfigMaps, etc. |
| **Cluster Mode** | Scan live Kubernetes cluster |
| **File Mode** | Work with local YAML manifests |
| **Preview Mode** | See diff before applying |
| **Export Mode** | Generate Kustomize overlays for GitOps |
| **Dry Run** | Validate without changes |
| **Rollback** | Undo last batch of changes |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- kubectl configured (for cluster mode)
- **Azure OpenAI API key** (recommended) OR **Gemini API key**

### Installation

```bash
git clone https://github.com/PrashantMurtale/ai-kustomize-agent.git
cd ai-kustomize-agent

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT
# OR use GEMINI_API_KEY if using Google Gemini
```

### Usage

```bash
# File Mode (no cluster access needed)
ai-kustomize --mode file --path ./manifests "Add resource limits to deployments"

# Cluster Mode (uses kubeconfig)
ai-kustomize --mode cluster "Add memory limit 512Mi to all deployments in staging"

# Preview only (no changes)
ai-kustomize --preview "Update all images to use ecr.aws/company"

# Export Kustomize files
ai-kustomize --export ./output "Add security context to all pods"
```

---

## 🔐 Access Configuration

### Mode 1: File Mode (No Cluster Access)
```bash
ai-kustomize --mode file --path ./k8s-manifests "..."
```

### Mode 2: Kubeconfig (Local Development)
```bash
# Uses default kubeconfig
ai-kustomize --mode cluster "..."

# Specific context
ai-kustomize --context staging-cluster "..."
```

### Mode 3: Service Account (In-Cluster)
Deploy with appropriate RBAC:
```bash
kubectl apply -f deploy/rbac.yaml
kubectl apply -f deploy/deployment.yaml
```

### Mode 4: Token Auth (CI/CD)
```bash
export KUBE_API_SERVER="https://api.cluster.example.com"
export KUBE_TOKEN="eyJhbGciOiJSUzI..."
ai-kustomize --api-server $KUBE_API_SERVER --token $KUBE_TOKEN "..."
```

---

## 📁 Project Structure

```
ai-kustomize-agent/
├── src/
│   ├── main.py              # CLI entry point
│   ├── agents/
│   │   ├── intent_parser.py # AI intent understanding
│   │   └── patch_generator.py
│   ├── scanners/
│   │   ├── cluster_scanner.py
│   │   └── manifest_scanner.py
│   ├── transformers/
│   │   ├── deployment.py
│   │   ├── pod.py
│   │   ├── service.py
│   │   └── common.py
│   └── outputs/
│       ├── kustomize.py
│       └── diff.py
├── config/
│   ├── access.yaml          # Access configuration
│   └── templates.yaml       # Patch templates
├── deploy/
│   ├── rbac.yaml
│   └── deployment.yaml
├── examples/
│   ├── add-resource-limits/
│   ├── update-images/
│   └── add-security-context/
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 📋 Output Examples

### Generated Kustomization
```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

patches:
  - path: patches/deployment-api-limits.yaml
  - path: patches/deployment-web-limits.yaml
  - path: patches/deployment-worker-limits.yaml
```

### Generated Patch
```yaml
# patches/deployment-api-limits.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: staging
spec:
  template:
    spec:
      containers:
        - name: api
          resources:
            limits:
              memory: "512Mi"
              cpu: "500m"
```

---

## 🛡️ Safety Features

| Feature | Description |
|---------|-------------|
| **Dry Run Default** | Changes are previewed, not applied |
| **Namespace Filtering** | Restrict to specific namespaces |
| **Protected Namespaces** | Block kube-system, production by default |
| **Confirmation Prompt** | Manual approval before apply |
| **Audit Logging** | All actions logged |
| **Rollback** | Undo last changes |

---

## 🤝 Freelance Services

Need custom Kubernetes automation?

- **Custom Transformers:** Support for CRDs and custom resources
- **GitOps Integration:** Auto-commit to ArgoCD/Flux repos
- **Policy Engine:** Enforce organizational standards

[**Contact Me**](mailto:prashantmurtale@gmail.com)

---

## 📄 License

MIT License
