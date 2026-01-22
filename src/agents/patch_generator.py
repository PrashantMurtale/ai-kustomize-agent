"""
Patch Generator - Creates Kustomize patches from intents.
"""

import logging
from typing import Dict, Any, List
import yaml

logger = logging.getLogger(__name__)


class PatchGenerator:
    """Generates Kustomize strategic merge patches."""
    
    def generate(self, intent: Dict[str, Any], resources: List[Dict]) -> List[Dict]:
        """
        Generate patches for all matching resources.
        
        Args:
            intent: Parsed intent from IntentParser
            resources: List of Kubernetes resources to patch
        
        Returns:
            List of patch dictionaries
        """
        patches = []
        
        target_field = intent.get("target_field", "")
        action = intent.get("action", "add")
        value = intent.get("value")
        
        for resource in resources:
            try:
                patch = self._generate_patch(resource, intent)
                
                if patch:
                    patches.append({
                        "name": f"{resource['kind'].lower()}-{resource['metadata']['name']}",
                        "namespace": resource['metadata'].get('namespace', 'default'),
                        "kind": resource['kind'],
                        "patch": patch,
                        "diff": self._generate_diff(resource, patch),
                        "yaml": yaml.dump(patch, default_flow_style=False)
                    })
                    
            except Exception as e:
                logger.error(f"Failed to generate patch for {resource.get('metadata', {}).get('name')}: {e}")
        
        return patches
    
    def _generate_patch(self, resource: Dict, intent: Dict) -> Dict:
        """Generate a single patch for a resource."""
        target_field = intent.get("target_field", "")
        action = intent.get("action", "add")
        value = intent.get("value")
        conditions = intent.get("conditions", {})
        
        # Build base patch structure
        patch = {
            "apiVersion": resource.get("apiVersion", "apps/v1"),
            "kind": resource["kind"],
            "metadata": {
                "name": resource["metadata"]["name"],
            }
        }
        
        if resource["metadata"].get("namespace"):
            patch["metadata"]["namespace"] = resource["metadata"]["namespace"]
        
        # Generate patch based on target field
        if "resources.limits.memory" in target_field:
            patch = self._add_resource_limit(patch, resource, "memory", value)
        
        elif "resources.limits.cpu" in target_field:
            patch = self._add_resource_limit(patch, resource, "cpu", value)
        
        elif "resources.limits" in target_field or "resources" in target_field:
            # Handle combined resource limits
            patch = self._add_resource_limits(patch, resource, value)
        
        elif target_field == "image":
            patch = self._update_image(patch, resource, value)
        
        elif target_field == "labels":
            patch = self._add_labels(patch, resource, value, "metadata")
        
        elif target_field == "annotations":
            patch = self._add_annotations(patch, resource, value)
        
        elif "securityContext" in target_field:
            patch = self._add_security_context(patch, resource, value)
        
        elif "replicas" in target_field:
            patch = self._set_replicas(patch, value)
        
        elif "probe" in target_field.lower():
            patch = self._add_probe(patch, resource, value, intent)
        
        else:
            logger.warning(f"Unknown target field: {target_field}")
            return None
        
        return patch
    
    def _add_resource_limit(self, patch: Dict, resource: Dict, limit_type: str, value: str) -> Dict:
        """Add memory or CPU limit to containers."""
        kind = resource["kind"]
        
        if kind == "Deployment":
            patch["spec"] = {
                "template": {
                    "spec": {
                        "containers": []
                    }
                }
            }
            
            # Get existing containers
            containers = resource.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            
            for container in containers:
                container_patch = {
                    "name": container["name"],
                    "resources": {
                        "limits": {
                            limit_type: value
                        }
                    }
                }
                patch["spec"]["template"]["spec"]["containers"].append(container_patch)
        
        elif kind == "Pod":
            patch["spec"] = {"containers": []}
            
            containers = resource.get("spec", {}).get("containers", [])
            
            for container in containers:
                container_patch = {
                    "name": container["name"],
                    "resources": {
                        "limits": {
                            limit_type: value
                        }
                    }
                }
                patch["spec"]["containers"].append(container_patch)
        
        return patch
    
    def _add_resource_limits(self, patch: Dict, resource: Dict, value: Dict) -> Dict:
        """Add combined resource limits."""
        if not isinstance(value, dict):
            value = {"memory": "512Mi", "cpu": "500m"}
        
        kind = resource["kind"]
        
        if kind == "Deployment":
            patch["spec"] = {
                "template": {
                    "spec": {
                        "containers": []
                    }
                }
            }
            
            containers = resource.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            
            for container in containers:
                container_patch = {
                    "name": container["name"],
                    "resources": {
                        "limits": value,
                        "requests": {
                            "memory": value.get("memory", "256Mi"),
                            "cpu": value.get("cpu", "250m")
                        }
                    }
                }
                patch["spec"]["template"]["spec"]["containers"].append(container_patch)
        
        return patch
    
    def _update_image(self, patch: Dict, resource: Dict, value: Dict) -> Dict:
        """Update container images."""
        kind = resource["kind"]
        
        from_prefix = value.get("from", "") if isinstance(value, dict) else ""
        to_prefix = value.get("to", value) if isinstance(value, dict) else value
        
        if kind == "Deployment":
            patch["spec"] = {
                "template": {
                    "spec": {
                        "containers": []
                    }
                }
            }
            
            containers = resource.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            
            for container in containers:
                current_image = container.get("image", "")
                
                if from_prefix and from_prefix in current_image:
                    new_image = current_image.replace(from_prefix, to_prefix)
                else:
                    new_image = f"{to_prefix}/{current_image.split('/')[-1]}"
                
                patch["spec"]["template"]["spec"]["containers"].append({
                    "name": container["name"],
                    "image": new_image
                })
        
        return patch
    
    def _add_labels(self, patch: Dict, resource: Dict, value: Dict, target: str = "metadata") -> Dict:
        """Add labels to resource."""
        if target == "metadata":
            patch["metadata"]["labels"] = value
        else:
            # Add to pod template for Deployments
            kind = resource["kind"]
            if kind == "Deployment":
                patch["spec"] = {
                    "template": {
                        "metadata": {
                            "labels": value
                        }
                    }
                }
        
        return patch
    
    def _add_annotations(self, patch: Dict, resource: Dict, value: Dict) -> Dict:
        """Add annotations to resource."""
        patch["metadata"]["annotations"] = value
        return patch
    
    def _add_security_context(self, patch: Dict, resource: Dict, value: Any) -> Dict:
        """Add security context."""
        kind = resource["kind"]
        
        if not isinstance(value, dict):
            value = {"runAsNonRoot": True}
        
        if kind == "Deployment":
            patch["spec"] = {
                "template": {
                    "spec": {
                        "securityContext": value
                    }
                }
            }
        elif kind == "Pod":
            patch["spec"] = {
                "securityContext": value
            }
        
        return patch
    
    def _set_replicas(self, patch: Dict, value: int) -> Dict:
        """Set replica count."""
        if isinstance(value, str):
            value = int(value)
        
        patch["spec"] = {"replicas": value}
        return patch
    
    def _add_probe(self, patch: Dict, resource: Dict, value: Any, intent: Dict) -> Dict:
        """Add readiness or liveness probe."""
        probe_type = "readinessProbe"
        if "liveness" in intent.get("target_field", "").lower():
            probe_type = "livenessProbe"
        
        port = 8080
        if isinstance(value, dict):
            port = value.get("port", 8080)
        elif isinstance(value, int):
            port = value
        
        probe = {
            "httpGet": {
                "path": "/health",
                "port": port
            },
            "initialDelaySeconds": 10,
            "periodSeconds": 10
        }
        
        kind = resource["kind"]
        
        if kind == "Deployment":
            containers = resource.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            
            patch["spec"] = {
                "template": {
                    "spec": {
                        "containers": []
                    }
                }
            }
            
            for container in containers:
                patch["spec"]["template"]["spec"]["containers"].append({
                    "name": container["name"],
                    probe_type: probe
                })
        
        return patch
    
    def _generate_diff(self, original: Dict, patch: Dict) -> str:
        """Generate a human-readable diff."""
        lines = []
        lines.append(f"Resource: {original['kind']}/{original['metadata']['name']}")
        lines.append(f"Namespace: {original['metadata'].get('namespace', 'default')}")
        lines.append("")
        lines.append("Changes:")
        lines.append(yaml.dump(patch.get("spec", patch.get("metadata", {})), default_flow_style=False))
        
        return "\n".join(lines)
