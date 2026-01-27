"""
Patch Generator - Creates Kustomize patches from intents.
"""

import logging
from typing import Dict, Any, List
import yaml

from src.transformers.factory import get_transformer

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

        # Validate intent
        required_fields = ["action", "resource_type", "target_field"]
        if any(intent.get(field) == "unknown" or field not in intent for field in required_fields):
            logger.error(f"Invalid intent: Missing one of {required_fields}. Intent: {intent}")
            return patches
        
        for resource in resources:
            try:
                transformer = get_transformer(resource, intent)
                patch = transformer.transform()
                
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
    
    def _generate_diff(self, original: Dict, patch: Dict) -> str:
        """Generate a human-readable diff."""
        lines = []
        lines.append(f"Resource: {original['kind']}/{original['metadata']['name']}")
        lines.append(f"Namespace: {original['metadata'].get('namespace', 'default')}")
        lines.append("")
        lines.append("Changes:")
        lines.append(yaml.dump(patch.get("spec", patch.get("metadata", {})), default_flow_style=False))
        
        return "\n".join(lines)
