from typing import Dict, Any, Type
from .base import BaseTransformer
from .deployment import DeploymentTransformer
from .pod import PodTransformer
from .generic import GenericTransformer

def get_transformer(resource: Dict[str, Any], intent: Dict[str, Any]) -> BaseTransformer:
    """Factory function to get the appropriate transformer."""
    kind = resource.get("kind", "").lower()

    if kind == "deployment":
        return DeploymentTransformer(resource, intent)
    elif kind == "pod":
        return PodTransformer(resource, intent)
    # Add other specific transformers here
    # e.g., elif kind == "service":
    #          return ServiceTransformer(resource, intent)
    else:
        return GenericTransformer(resource, intent)
