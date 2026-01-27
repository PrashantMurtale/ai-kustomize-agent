from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTransformer(ABC):
    """Abstract base class for resource transformers."""

    def __init__(self, resource: Dict[str, Any], intent: Dict[str, Any]):
        self.resource = resource
        self.intent = intent

    @abstractmethod
    def transform(self) -> Dict[str, Any]:
        """
        Apply the transformation to the resource.
        Returns the patch.
        """
        raise NotImplementedError

    def _build_patch_base(self) -> Dict[str, Any]:
        """Build the base structure of a patch."""
        patch = {
            "apiVersion": self.resource.get("apiVersion"),
            "kind": self.resource.get("kind"),
            "metadata": {
                "name": self.resource.get("metadata", {}).get("name"),
            }
        }
        namespace = self.resource.get("metadata", {}).get("namespace")
        if namespace:
            patch["metadata"]["namespace"] = namespace
        return patch
