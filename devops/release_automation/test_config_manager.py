#!/usr/bin/env python3
"""
Modular Test Configuration Manager

A CLI tool for managing the modular test framework configuration.
Provides easy ways to add tests, modify weights, and validate configuration.

Usage:
    python devops/release_automation/test_config_manager.py --list
    python devops/release_automation/test_config_manager.py --update .github/pr-test-config.yml --add-test "security_scan:90"
    python devops/release_automation/test_config_manager.py --validate
"""

import argparse
import json
import sys
import yaml
from pathlib import Path
from typing import Dict, Any


class TestConfigManager:
    """Manager for modular test configuration."""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            repo_root = self._find_repo_root()
            config_path = str(repo_root / ".github" / "pr-test-config.yml")
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _find_repo_root(self) -> Path:
        """Find the Git repository root"""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        raise Exception("Not in a Git repository")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            print(f"❌ Configuration file not found: {self.config_path}")
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML in configuration file: {e}")
            sys.exit(1)
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        return {
            "global_config": {
                "auto_merge_threshold": 85,
                "manual_review_threshold": 65,
                "block_threshold": 64
            },
            "test_suite": []
        }
    
    def _save_config(self):
        """Save configuration to YAML file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Configuration saved to {self.config_path}")
    
    def list_tests(self):
        """List all configured tests."""
        tests = self.config.get("test_suite", [])
        
        if not tests:
            print("📋 No tests configured")
            return
        
        print("📋 Configured Tests:")
        print("=" * 60)
        
        total_weight = 0
        hard_checks = []
        soft_checks = []
        
        for test in tests:
            test_id = test.get("id", "unknown")
            name = test.get("name", "Unnamed Test")
            weight = test.get("weight", 0)
            enforcement = test.get("enforcement", "soft")
            action_path = test.get("action_path", "")
            
            if enforcement == "hard":
                hard_checks.append((test_id, name, action_path))
            else:
                soft_checks.append((test_id, name, weight, action_path))
                total_weight += weight
        
        if hard_checks:
            print("\n🔒 Hard Checks (Must Pass):")
            for test_id, name, action_path in hard_checks:
                print(f"  • {name} ({test_id})")
                print(f"    Action: {action_path}")
        
        if soft_checks:
            print("\n📊 Soft Checks (Scoring):")
            for test_id, name, weight, action_path in soft_checks:
                print(f"  • {name} ({test_id}) - Weight: {weight}%")
                print(f"    Action: {action_path}")
            
            print(f"\n📈 Total Weight: {total_weight}% {'✅' if total_weight == 100 else '⚠️  (Should be 100%)'}")
        
        # Show thresholds
        gc = self.config.get("global_config", {})
        print(f"\n🎯 Thresholds:")
        print(f"  Auto-merge: ≥{gc.get('auto_merge_threshold', 85)}%")
        print(f"  Manual review: ≥{gc.get('manual_review_threshold', 65)}%")
        print(f"  Block: ≤{gc.get('block_threshold', 64)}%")
    
    def add_test(self, test_id: str, name: str, weight: int, enforcement: str, 
                 action_path: str, timeout: int = 10):
        """Add a new test to the configuration."""
        # Validate inputs
        if enforcement not in ["hard", "soft"]:
            print("❌ Enforcement must be 'hard' or 'soft'")
            return False
        
        if enforcement == "soft" and (weight < 0 or weight > 100):
            print("❌ Weight must be between 0 and 100 for soft checks")
            return False
        
        if enforcement == "hard":
            weight = 0  # Hard checks don't contribute to scoring
        
        # Check if test ID already exists
        existing_ids = [t.get("id") for t in self.config.get("test_suite", [])]
        if test_id in existing_ids:
            print(f"❌ Test ID '{test_id}' already exists")
            return False
        
        # Add the test
        new_test = {
            "id": test_id,
            "name": name,
            "description": f"Auto-generated test: {name}",
            "weight": weight,
            "enforcement": enforcement,
            "action_path": action_path,
            "timeout_minutes": timeout,
            "inputs": {},
            "outputs_required": ["result"]
        }
        
        if enforcement == "soft":
            new_test["outputs_required"].append("score")
            new_test["score_mapping"] = {
                "output_field": "score",
                "min_score": 0,
                "max_score": 100
            }
        
        if "test_suite" not in self.config:
            self.config["test_suite"] = []
        
        self.config["test_suite"].append(new_test)
        self._save_config()
        
        print(f"✅ Added {enforcement} check: {name} ({test_id})")
        if enforcement == "soft":
            print(f"   Weight: {weight}%")
        print(f"   Action: {action_path}")
        
        return True
    
    def remove_test(self, test_id: str):
        """Remove a test from the configuration."""
        tests = self.config.get("test_suite", [])
        original_count = len(tests)
        
        self.config["test_suite"] = [t for t in tests if t.get("id") != test_id]
        
        if len(self.config["test_suite"]) == original_count:
            print(f"❌ Test '{test_id}' not found")
            return False
        
        self._save_config()
        print(f"✅ Removed test: {test_id}")
        return True
    
    def set_thresholds(self, auto_merge: int = None, manual_review: int = None, 
                      block: int = None):
        """Set scoring thresholds."""
        gc = self.config.setdefault("global_config", {})
        
        if auto_merge is not None:
            gc["auto_merge_threshold"] = auto_merge
        if manual_review is not None:
            gc["manual_review_threshold"] = manual_review
        if block is not None:
            gc["block_threshold"] = block
        
        self._save_config()
        print("✅ Thresholds updated:")
        print(f"   Auto-merge: ≥{gc.get('auto_merge_threshold')}%")
        print(f"   Manual review: ≥{gc.get('manual_review_threshold')}%")
        print(f"   Block: ≤{gc.get('block_threshold')}%")
    
    def validate_config(self):
        """Validate the current configuration."""
        errors = []
        warnings = []
        
        # Check global config
        gc = self.config.get("global_config", {})
        if not gc:
            errors.append("Missing global_config section")
        else:
            required_thresholds = ["auto_merge_threshold", "manual_review_threshold", "block_threshold"]
            for threshold in required_thresholds:
                if threshold not in gc:
                    errors.append(f"Missing {threshold} in global_config")
        
        # Check test suite
        tests = self.config.get("test_suite", [])
        if not tests:
            warnings.append("No tests configured in test_suite")
        
        test_ids = []
        total_weight = 0
        
        for i, test in enumerate(tests):
            test_id = test.get("id")
            if not test_id:
                errors.append(f"Test {i} missing required field: id")
            elif test_id in test_ids:
                errors.append(f"Duplicate test ID: {test_id}")
            else:
                test_ids.append(test_id)
            
            # Check required fields
            required_fields = ["name", "enforcement", "action_path"]
            for field in required_fields:
                if field not in test:
                    errors.append(f"Test '{test_id}' missing required field: {field}")
            
            # Check enforcement
            enforcement = test.get("enforcement")
            if enforcement not in ["hard", "soft"]:
                errors.append(f"Test '{test_id}' has invalid enforcement: {enforcement}")
            
            # Check weights for soft checks
            if enforcement == "soft":
                weight = test.get("weight", 0)
                if not isinstance(weight, int) or weight < 0 or weight > 100:
                    errors.append(f"Test '{test_id}' has invalid weight: {weight}")
                total_weight += weight
        
        # Check total weight
        if total_weight != 100:
            warnings.append(f"Soft check weights total {total_weight}%, expected 100%")
        
        # Report results
        print("🔍 Configuration Validation Results:")
        print("=" * 40)
        
        if errors:
            print("❌ Errors:")
            for error in errors:
                print(f"  • {error}")
        
        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"  • {warning}")
        
        if not errors and not warnings:
            print("✅ Configuration is valid!")
        
        return len(errors) == 0
    
    def export_config(self, format: str = "yaml"):
        """Export configuration in specified format."""
        if format == "json":
            print(json.dumps(self.config, indent=2))
        elif format == "yaml":
            print(yaml.dump(self.config, default_flow_style=False))
        else:
            print(f"❌ Unsupported format: {format}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Modular Test Configuration Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all configured tests
  python test_config_manager.py list

  # Add a new soft check test
  python test_config_manager.py add-test my_test "My Custom Test" --weight 15 --action-path .github/actions/my-test

  # Add a new hard check test
  python test_config_manager.py add-test security_check "Security Check" --enforcement hard --action-path .github/actions/security

  # Set scoring thresholds
  python test_config_manager.py set-thresholds --auto-merge 90 --manual-review 70

  # Validate configuration
  python test_config_manager.py validate
        """
    )
    
    parser.add_argument(
        "--config", 
        default=".github/pr-test-config.yml",
        help="Path to configuration file (default: .github/pr-test-config.yml)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    subparsers.add_parser("list", help="List all configured tests")
    
    # Add test command
    add_parser = subparsers.add_parser("add-test", help="Add a new test")
    add_parser.add_argument("test_id", help="Unique test identifier")
    add_parser.add_argument("name", help="Human-readable test name")
    add_parser.add_argument("--weight", type=int, default=10, 
                           help="Weight percentage for soft checks (default: 10)")
    add_parser.add_argument("--enforcement", choices=["hard", "soft"], default="soft",
                           help="Enforcement type (default: soft)")
    add_parser.add_argument("--action-path", required=True,
                           help="Path to GitHub Action")
    add_parser.add_argument("--timeout", type=int, default=10,
                           help="Timeout in minutes (default: 10)")
    
    # Remove test command
    remove_parser = subparsers.add_parser("remove-test", help="Remove a test")
    remove_parser.add_argument("test_id", help="Test ID to remove")
    
    # Set thresholds command
    threshold_parser = subparsers.add_parser("set-thresholds", help="Set scoring thresholds")
    threshold_parser.add_argument("--auto-merge", type=int, help="Auto-merge threshold")
    threshold_parser.add_argument("--manual-review", type=int, help="Manual review threshold")
    threshold_parser.add_argument("--block", type=int, help="Block threshold")
    
    # Validate command
    subparsers.add_parser("validate", help="Validate configuration")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export configuration")
    export_parser.add_argument("--format", choices=["yaml", "json"], default="yaml",
                              help="Export format (default: yaml)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = TestConfigManager(args.config)
    
    if args.command == "list":
        manager.list_tests()
    elif args.command == "add-test":
        manager.add_test(
            args.test_id, args.name, args.weight, args.enforcement,
            args.action_path, args.timeout
        )
    elif args.command == "remove-test":
        manager.remove_test(args.test_id)
    elif args.command == "set-thresholds":
        manager.set_thresholds(args.auto_merge, args.manual_review, args.block)
    elif args.command == "validate":
        is_valid = manager.validate_config()
        sys.exit(0 if is_valid else 1)
    elif args.command == "export":
        manager.export_config(args.format)


if __name__ == "__main__":
    main()
