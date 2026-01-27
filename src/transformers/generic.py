from typing import Dict, Any
from .base import BaseTransformer

class GenericTransformer(BaseTransformer):
    """Transformer for generic resources."""

    def transform(self) -> Dict[str, Any]:
        target_field = self.intent.get("target_field", "")

        if target_field == "labels":
            return self._add_metadata("labels")
        elif target_field == "annotations":
            return self._add_metadata("annotations")
        else:
            return None

    def _add_metadata(self, field: str) -> Dict[str, Any]:
        """Add labels or annotations to resource metadata."""
        patch = self._build_patch_base()
        patch["metadata"][field] = self.intent.get("value")
        return patch
