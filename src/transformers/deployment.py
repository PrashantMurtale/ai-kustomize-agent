from typing import Dict, Any, List
from .base import BaseTransformer

class DeploymentTransformer(BaseTransformer):
    """Transformer for Deployment resources."""

    def transform(self) -> Dict[str, Any]:
        target_field = self.intent.get("target_field", "")

        if "resources.limits" in target_field or "resources" in target_field:
            return self._add_resource_limits()
        elif target_field == "image":
            return self._update_image()
        elif "probe" in target_field.lower():
            return self._add_probe()
        elif target_field == "labels":
            return self._add_labels("spec.template.metadata")
        elif target_field == "annotations":
            return self._add_annotations("spec.template.metadata")
        elif "securityContext" in target_field:
            return self._add_security_context()
        elif "replicas" in target_field:
            return self._set_replicas()
        else:
            return None

    def _add_resource_limits(self) -> Dict[str, Any]:
        """Add memory or CPU limits to containers."""
        patch = self._build_patch_base()
        value = self.intent.get("value", {})
        if not isinstance(value, dict):
            value = {"memory": "512Mi", "cpu": "500m"} # Fallback

        containers = self.resource.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])

        patch["spec"] = {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": c["name"],
                            "resources": { "limits": value }
                        } for c in containers
                    ]
                }
            }
        }
        return patch

    def _update_image(self) -> Dict[str, Any]:
        """Update container images."""
        patch = self._build_patch_base()
        value = self.intent.get("value")

        from_prefix = value.get("from", "") if isinstance(value, dict) else ""
        to_image = value.get("to", value) if isinstance(value, dict) else value

        containers = self.resource.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])

        patched_containers = []
        for c in containers:
            current_image = c.get("image", "")
            
            if from_prefix and from_prefix in current_image:
                new_image = current_image.replace(from_prefix, to_image)
            elif "/" not in to_image and ":" in to_image and ":" in current_image:
                # If target is like "nginx:1.16.0" and current is "nginx:1.15.0"
                # Just replace the whole thing if it seems like a tag update
                new_image = to_image
            elif "/" not in current_image and "/" not in to_image:
                # Simple case: both are just image[:tag]
                new_image = to_image
            else:
                # Fallback to original logic but with better naming
                image_parts = current_image.split('/')
                image_name = image_parts[-1]
                
                if "/" in to_image:
                    new_image = to_image
                else:
                    new_image = f"{to_image}/{image_name}"

            patched_containers.append({
                "name": c["name"],
                "image": new_image
            })

        patch["spec"] = { "template": { "spec": { "containers": patched_containers } } }
        return patch

    def _add_probe(self) -> Dict[str, Any]:
        """Add readiness or liveness probe."""
        patch = self._build_patch_base()
        probe_type = "readinessProbe"
        if "liveness" in self.intent.get("target_field", "").lower():
            probe_type = "livenessProbe"

        value = self.intent.get("value")
        port = value.get("port", 8080) if isinstance(value, dict) else 8080

        probe = {
            "httpGet": {"path": "/health", "port": port},
            "initialDelaySeconds": 10,
            "periodSeconds": 10
        }

        containers = self.resource.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])

        patch["spec"] = {
            "template": {
                "spec": {
                    "containers": [
                        {"name": c["name"], probe_type: probe} for c in containers
                    ]
                }
            }
        }
        return patch

    def _add_labels(self, target_path: str = None) -> Dict[str, Any]:
        patch = self._build_patch_base()
        patch["spec"] = {"template": {"metadata": {"labels": self.intent.get("value")}}}
        return patch

    def _add_annotations(self, target_path: str = None) -> Dict[str, Any]:
        patch = self._build_patch_base()
        patch["spec"] = {"template": {"metadata": {"annotations": self.intent.get("value")}}}
        return patch

    def _add_security_context(self) -> Dict[str, Any]:
        patch = self._build_patch_base()
        value = self.intent.get("value")
        if not isinstance(value, dict):
            value = {"runAsNonRoot": True}

        patch["spec"] = {"template": {"spec": {"securityContext": value}}}
        return patch

    def _set_replicas(self) -> Dict[str, Any]:
        patch = self._build_patch_base()
        value = self.intent.get("value")
        if isinstance(value, str):
            value = int(value)
        patch["spec"] = {"replicas": value}
        return patch
