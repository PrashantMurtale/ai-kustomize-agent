from typing import Dict, Any, List
from .base import BaseTransformer

class PodTransformer(BaseTransformer):
    """Transformer for Pod resources."""

    def transform(self) -> Dict[str, Any]:
        target_field = self.intent.get("target_field", "")

        if "resources.limits" in target_field or "resources" in target_field:
            return self._add_resource_limits()
        elif target_field == "labels":
            return self._add_labels()
        elif target_field == "annotations":
            return self._add_annotations()
        elif "securityContext" in target_field:
            return self._add_security_context()
        else:
            return None

    def _add_resource_limits(self) -> Dict[str, Any]:
        """Add memory or CPU limits to containers."""
        patch = self._build_patch_base()
        value = self.intent.get("value", {})
        target_field = self.intent.get("target_field", "").lower()
        
        # Normalize value if it's a string
        if isinstance(value, str):
            if "memory" in target_field:
                value = {"memory": value}
            elif "cpu" in target_field:
                value = {"cpu": value}
            else:
                value = {"memory": value}
        
        if not isinstance(value, dict):
            value = {"memory": "512Mi", "cpu": "500m"}

        containers = self.resource.get("spec", {}).get("containers", [])

        patched_containers = []
        for c in containers:
            container_patch = {"name": c["name"]}
            
            target_container = self.intent.get("conditions", {}).get("container_name")
            if target_container and c["name"] != target_container:
                continue
                
            container_patch["resources"] = { "limits": value }
            patched_containers.append(container_patch)

        patch["spec"] = {
            "containers": patched_containers
        }
        return patch

    def _add_labels(self) -> Dict[str, Any]:
        patch = self._build_patch_base()
        patch["metadata"]["labels"] = self.intent.get("value")
        return patch

    def _add_annotations(self) -> Dict[str, Any]:
        patch = self._build_patch_base()
        patch["metadata"]["annotations"] = self.intent.get("value")
        return patch

    def _add_security_context(self) -> Dict[str, Any]:
        patch = self._build_patch_base()
        value = self.intent.get("value")
        if not isinstance(value, dict):
            value = {"runAsNonRoot": True}

        patch["spec"] = {"securityContext": value}
        return patch
