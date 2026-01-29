#!/usr/bin/env python3
"""
AI Kustomize Agent - CLI Entry Point
Natural language to Kustomize patches for bulk K8s modifications.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from agents.intent_parser import IntentParser
from agents.patch_generator import PatchGenerator
from scanners.cluster_scanner import ClusterScanner
from scanners.manifest_scanner import ManifestScanner
from outputs.kustomize import KustomizeGenerator
from outputs.diff import DiffPreview
import yaml

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIKustomizeAgent:
    """Main agent class orchestrating the workflow."""
    
    def __init__(
        self,
        namespace: Optional[str] = None,
        dry_run: bool = True,
        yes: bool = False
    ):
        self.mode = mode
        self.manifest_path = manifest_path
        self.namespace = namespace
        self.dry_run = dry_run
        self.yes = yes
        
        # Initialize components
        self.intent_parser = IntentParser()
        self.patch_generator = PatchGenerator()
        self.kustomize_gen = KustomizeGenerator()
        self.diff_preview = DiffPreview()
        
        # Initialize scanner based on mode
        if mode == "cluster":
            self.scanner = ClusterScanner(
                kubeconfig=kubeconfig,
                context=context
            )
        else:
            self.scanner = ManifestScanner(path=manifest_path)
    
    def run(self, user_request: str, export_path: Optional[str] = None) -> dict:
        """Execute the full workflow."""
        logger.info(f"📝 Processing request: {user_request}")
        
        # Step 1: Parse intent
        logger.info("🤖 Parsing intent with AI...")
        intent_data = self.intent_parser.parse(user_request)
        
        if intent_data.get("error"):
            return {"status": "error", "message": f"Failed to parse intent: {intent_data['error']}"}
        
        intents = intent_data.get("intents", [])
        if not intents:
            return {"status": "warning", "message": "No intents found in request"}

        # Collect all patches across all intents
        all_resource_patches = {} # key: (kind, name, namespace), value: merged_patch_dict

        for intent in intents:
            logger.info(f"   Action: {intent.get('action')} on {intent.get('target_field')}")
            
            # Step 2: Scan resources for this intent
            resources = self.scanner.scan(
                resource_type=intent.get("resource_type", "deployments"),
                namespace=self.namespace or intent.get("namespace"),
                labels=intent.get("label_selector")
            )
            
            if not resources:
                logger.warning(f"      No matching resources found for {intent.get('target_field')}")
                continue
            
            # Step 3: Generate patches for this intent
            intent_patches = self.patch_generator.generate(intent, resources)
            
            # Step 4: Merge patches for the same resource
            for p in intent_patches:
                key = (p['kind'], p['name'], p['namespace'])
                if key not in all_resource_patches:
                    logger.debug(f"      Initial patch for {key}")
                    all_resource_patches[key] = p
                else:
                    logger.debug(f"      Merging patch for {key}")
                    # Deep merge patch data
                    self._deep_merge(all_resource_patches[key]['patch'], p['patch'])
                    # Update yaml
                    all_resource_patches[key]['yaml'] = yaml.dump(all_resource_patches[key]['patch'], default_flow_style=False)
                    logger.debug(f"      Merged patch: {all_resource_patches[key]['yaml']}")

        if not all_resource_patches:
            return {"status": "warning", "message": "No patches generated"}

        final_patches = list(all_resource_patches.values())
        logger.info(f"   Total unique resources to patch: {len(final_patches)}")
        
        # Step 5: Preview changes
        if self.dry_run or export_path:
            logger.info("👀 Preview of changes:")
            for patch in final_patches:
                print(f"\n--- {patch['name']} ---")
                print(f"Resource: {patch['kind']}/{patch['name']}")
                print(f"Namespace: {patch['namespace']}")
                print("Changes:")
                print(patch['yaml'])
        
        # Step 6: Export or Apply
        if export_path:
            logger.info(f"📦 Exporting to {export_path}...")
            self.kustomize_gen.export(final_patches, export_path)
            return {
                "status": "exported",
                "path": export_path,
                "patches_count": len(final_patches)
            }
        
        if not self.dry_run:
            # Confirm before applying
            if not self.yes and not self._confirm_apply(len(final_patches)):
                return {"status": "cancelled", "message": "User cancelled"}
            
            logger.info("🚀 Applying patches...")
            results = self._apply_patches(final_patches)
            return {
                "status": "applied",
                "applied": results["success"],
                "failed": results["failed"]
            }
        
        return {
            "status": "preview",
            "patches_count": len(final_patches),
            "message": "Use --apply to apply changes or --export to save Kustomize files"
        }

    def _deep_merge(self, base: dict, extra: dict):
        """Deep merge two dictionaries."""
        import collections.abc
        for k, v in extra.items():
            if isinstance(v, collections.abc.Mapping) and k in base and isinstance(base[k], dict):
                self._deep_merge(base[k], v)
            elif isinstance(v, list) and k in base and isinstance(base[k], list):
                # For lists (like containers), merge by name if possible
                if k == "containers" or k == "initContainers":
                    self._merge_containers(base[k], v)
                else:
                    # Fallback: extend if not already present
                    for item in v:
                        if item not in base[k]:
                            base[k].append(item)
            else:
                base[k] = v

    def _merge_containers(self, base_list: list, extra_list: list):
        """Merge container lists by name."""
        base_map = {c["name"]: c for c in base_list}
        for extra_c in extra_list:
            name = extra_c.get("name")
            if name in base_map:
                self._deep_merge(base_map[name], extra_c)
            else:
                base_list.append(extra_c)

    
    def _confirm_apply(self, patch_count: int) -> bool:
        """Ask user to confirm before applying."""
        response = input(f"\n⚠️  Apply {patch_count} patches? [y/N]: ")
        return response.lower() == 'y'
    
    def _apply_patches(self, patches: list) -> dict:
        """Apply patches to the cluster."""
        success = 0
        failed = 0
        
        for patch in patches:
            try:
                self.scanner.apply_patch(patch)
                success += 1
                logger.info(f"   ✅ Applied: {patch['name']}")
            except Exception as e:
                failed += 1
                logger.error(f"   ❌ Failed: {patch['name']} - {e}")
        
        return {"success": success, "failed": failed}


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Kustomize Agent - Natural language to Kustomize patches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-kustomize "Add memory limit 512Mi to all deployments in staging"
  ai-kustomize --mode file --path ./manifests "Update all images to ecr.aws/company"
  ai-kustomize --export ./output "Add security context to all pods"
  ai-kustomize --preview "Add label team=platform to all services"
        """
    )
    
    # Positional argument
    parser.add_argument(
        "request",
        nargs="?",
        help="Natural language request describing the changes"
    )
    
    # Mode options
    parser.add_argument(
        "--mode",
        choices=["cluster", "file"],
        default="cluster",
        help="Scan mode: cluster (live) or file (local manifests)"
    )
    
    parser.add_argument(
        "--path",
        help="Path to manifest files (required for file mode)"
    )
    
    # Cluster options
    parser.add_argument(
        "--kubeconfig",
        help="Path to kubeconfig file"
    )
    
    parser.add_argument(
        "--context",
        help="Kubernetes context to use"
    )
    
    parser.add_argument(
        "--namespace", "-n",
        help="Limit to specific namespace"
    )
    
    # Action options
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview changes only (default behavior)"
    )
    
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to cluster"
    )
    
    parser.add_argument(
        "--export",
        metavar="PATH",
        help="Export Kustomize files to path"
    )
    
    # Other options
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt when applying"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.request:
        parser.print_help()
        sys.exit(1)
    
    if args.mode == "file" and not args.path:
        print("Error: --path is required for file mode")
        sys.exit(1)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run agent
    try:
        agent = AIKustomizeAgent(
            mode=args.mode,
            manifest_path=args.path,
            kubeconfig=args.kubeconfig,
            context=args.context,
            namespace=args.namespace,
            dry_run=not args.apply,
            yes=args.yes
        )
        
        result = agent.run(
            user_request=args.request,
            export_path=args.export
        )
        
        # Print result
        print(f"\n{'='*50}")
        print(f"Status: {result['status']}")
        
        if result.get("message"):
            print(f"Message: {result['message']}")
        
        if result.get("patches_count"):
            print(f"Patches: {result['patches_count']}")
        
        if result.get("path"):
            print(f"Exported to: {result['path']}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
