"""
Diff Preview - Shows changes before applying.
"""

import logging
import subprocess
from typing import List, Dict

logger = logging.getLogger(__name__)


class DiffPreview:
    """Generate and display diffs for pending changes."""
    
    def show(self, patches: List[Dict]):
        """Display all patches as diffs."""
        for patch in patches:
            print(f"\n{'='*60}")
            print(f"📝 {patch['kind']}/{patch['name']} ({patch['namespace']})")
            print('='*60)
            print(patch['yaml'])
    
    def kubectl_diff(self, patches: List[Dict]) -> str:
        """
        Use kubectl diff to show actual changes.
        Requires kubectl and cluster access.
        """
        results = []
        
        for patch in patches:
            try:
                # Write patch to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                    f.write(patch['yaml'])
                    temp_path = f.name
                
                # Run kubectl diff
                result = subprocess.run(
                    ['kubectl', 'diff', '-f', temp_path],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    results.append(f"--- {patch['name']} ---\n{result.stdout}")
                
                # Cleanup
                import os
                os.unlink(temp_path)
                
            except Exception as e:
                logger.warning(f"kubectl diff failed: {e}")
        
        return "\n".join(results) if results else "No differences found"
