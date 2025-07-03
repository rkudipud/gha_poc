#!/usr/bin/env python3
"""
Local Consistency Checker Framework

A modular framework for running pre-push consistency checks to catch issues
before they reach the CI/CD pipeline. This helps developers identify and fix
problems locally, reducing CI failures and improving productivity.

Usage:
    python devops/consistency_checker/checker.py --all
    python devops/consistency_checker/checker.py --rule python_imports
    python devops/consistency_checker/checker.py --rule naming_conventions --fix
    python devops/consistency_checker/checker.py --list-rules
"""


import argparse
import sys
import os
import importlib.util
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import subprocess


@dataclass
class CheckResult:
    """Result of a consistency check"""
    rule_name: str
    passed: bool
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    fixed_issues: List[Dict[str, Any]]
    execution_time: float


@dataclass
class WaiverRule:
    """Waiver rule configuration"""
    pattern: str
    reason: str
    approved_by: str
    expires: Optional[str]
    file_pattern: Optional[str] = None


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ConsistencyChecker:
    """Main consistency checker framework"""
    
    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or self._find_repo_root()
        self.checker_dir = self.repo_root / "devops" / "consistency_checker"
        self.rules_dir = self.checker_dir / "rules"
        self.waivers = self._load_waivers()
        self.available_rules = self._discover_rules()
        
    def _find_repo_root(self) -> Path:
        """Find the Git repository root"""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        raise Exception("Not in a Git repository")
    
    def _load_waivers(self) -> Dict[str, List[WaiverRule]]:
        """Load waiver rules from centralized waiver file"""
        waivers = {}
        
        # Use centralized waivers
        centralized_waiver_file = self.rules_dir.parent / "waivers.yml"
        if centralized_waiver_file.exists():
            try:
                with open(centralized_waiver_file, 'r') as f:
                    waiver_data = yaml.safe_load(f) or {}
                
                # Process global waivers that apply to all rules
                for rule_name in self._get_rule_names():
                    rule_waivers = []
                    
                    # Add rule-based waivers
                    for waiver in waiver_data.get('rule_waivers', []):
                        rule_waivers.append(WaiverRule(
                            pattern=waiver.get('file', ''),
                            reason=waiver.get('reason', ''),
                            approved_by=waiver.get('approved_by', ''),
                            expires=waiver.get('expires'),
                            file_pattern=waiver.get('file', '')
                        ))
                    
                    # Add bulk waivers
                    for waiver in waiver_data.get('bulk_waivers', []):
                        rule_waivers.append(WaiverRule(
                            pattern=waiver.get('pattern', ''),
                            reason=waiver.get('reason', ''),
                            approved_by=waiver.get('approved_by', ''),
                            expires=waiver.get('expires'),
                            file_pattern=waiver.get('pattern', '')
                        ))
                    
                    # Add rule-specific waivers from consistency_waivers section
                    consistency_waivers = waiver_data.get('consistency_waivers', {})
                    rule_specific = consistency_waivers.get(rule_name, {})
                    
                    for waiver in rule_specific.get('file_waivers', []):
                        rule_waivers.append(WaiverRule(
                            pattern=waiver.get('pattern', ''),
                            reason=waiver.get('reason', ''),
                            approved_by=waiver.get('approved_by', ''),
                            expires=waiver.get('expires'),
                            file_pattern=waiver.get('pattern', '')
                        ))
                    
                    waivers[rule_name] = rule_waivers
                
                print(f"{Colors.GREEN}✓ Loaded centralized waivers from {centralized_waiver_file}{Colors.END}")
                return waivers
                
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️ Error loading centralized waivers: {e}{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠️ No centralized waiver file found at {centralized_waiver_file}{Colors.END}")
        
        return waivers
    
    def _get_rule_names(self) -> List[str]:
        """Get list of available rule names"""
        rule_names = []
        if self.rules_dir.exists():
            for rule_dir in self.rules_dir.iterdir():
                if rule_dir.is_dir() and not rule_dir.name.startswith('.'):
                    rule_names.append(rule_dir.name)
        return rule_names
    
    def _discover_rules(self) -> Dict[str, Path]:
        """Discover available consistency rules"""
        rules = {}
        
        if not self.rules_dir.exists():
            return rules
            
        for rule_dir in self.rules_dir.iterdir():
            if rule_dir.is_dir():
                rule_script = rule_dir / f"{rule_dir.name}.py"
                if rule_script.exists():
                    rules[rule_dir.name] = rule_script
        
        return rules
    
    def _load_rule_module(self, rule_name: str):
        """Dynamically load a rule module"""
        rule_path = self.available_rules.get(rule_name)
        if not rule_path:
            raise ValueError(f"Rule '{rule_name}' not found")
        
        spec = importlib.util.spec_from_file_location(rule_name, rule_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    def _apply_waivers(self, rule_name: str, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply waivers to filter out waived violations"""
        rule_waivers = self.waivers.get(rule_name, [])
        if not rule_waivers:
            return violations
        
        filtered_violations = []
        waived_count = 0
        
        for violation in violations:
            waived = False
            
            for waiver in rule_waivers:
                # Check if waiver has expired
                if waiver.expires:
                    try:
                        expire_date = datetime.strptime(waiver.expires, '%Y-%m-%d').date()
                        if datetime.now().date() > expire_date:
                            continue
                    except ValueError:
                        continue
                
                # Check if violation matches waiver pattern
                violation_text = violation.get('message', '')
                file_path = violation.get('file', '')
                
                if waiver.pattern in violation_text or waiver.pattern in file_path:
                    if waiver.file_pattern:
                        import fnmatch
                        if fnmatch.fnmatch(file_path, waiver.file_pattern):
                            waived = True
                            waived_count += 1
                            break
                    else:
                        waived = True
                        waived_count += 1
                        break
            
            if not waived:
                filtered_violations.append(violation)
        
        if waived_count > 0:
            print(f"{Colors.BLUE}ℹ️ Applied {waived_count} waivers for rule '{rule_name}'{Colors.END}")
        
        return filtered_violations
    
    def run_rule(self, rule_name: str, fix: bool = False) -> CheckResult:
        """Run a specific consistency rule"""
        start_time = datetime.now()
        
        try:
            rule_module = self._load_rule_module(rule_name)
            
            # Check if rule has required functions
            if not hasattr(rule_module, 'check'):
                raise ValueError(f"Rule '{rule_name}' missing required 'check' function")
            
            # Run the check
            result = rule_module.check(self.repo_root)
            
            # Apply waivers
            if result.get('violations'):
                result['violations'] = self._apply_waivers(rule_name, result['violations'])
            
            # Run fix if requested and available
            fixed_issues = []
            if fix and hasattr(rule_module, 'fix') and result.get('violations'):
                try:
                    fix_result = rule_module.fix(self.repo_root, result['violations'])
                    fixed_issues = fix_result.get('fixed', [])
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️ Fix failed for rule '{rule_name}': {e}{Colors.END}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CheckResult(
                rule_name=rule_name,
                passed=len(result.get('violations', [])) == 0,
                violations=result.get('violations', []),
                warnings=result.get('warnings', []),
                fixed_issues=fixed_issues,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                rule_name=rule_name,
                passed=False,
                violations=[{
                    'file': 'checker',
                    'line': 0,
                    'message': f"Rule execution failed: {e}",
                    'severity': 'error'
                }],
                warnings=[],
                fixed_issues=[],
                execution_time=execution_time
            )
    
    def run_all_rules(self, fix: bool = False) -> List[CheckResult]:
        """Run all available consistency rules"""
        results = []
        
        print(f"{Colors.BOLD}🔍 Running consistency checks...{Colors.END}")
        print(f"Repository: {self.repo_root}")
        print(f"Rules directory: {self.rules_dir}")
        print()
        
        for rule_name in sorted(self.available_rules.keys()):
            print(f"Running rule: {Colors.CYAN}{rule_name}{Colors.END}")
            result = self.run_rule(rule_name, fix)
            results.append(result)
            
            # Print immediate feedback
            if result.passed:
                print(f"  ✅ {Colors.GREEN}PASSED{Colors.END} ({result.execution_time:.2f}s)")
            else:
                print(f"  ❌ {Colors.RED}FAILED{Colors.END} ({len(result.violations)} violations, {result.execution_time:.2f}s)")
            
            if result.fixed_issues:
                print(f"  🔧 {Colors.BLUE}FIXED{Colors.END} {len(result.fixed_issues)} issues")
            
            print()
        
        return results
    
    def print_summary(self, results: List[CheckResult]):
        """Print a summary of all check results"""
        total_rules = len(results)
        passed_rules = sum(1 for r in results if r.passed)
        total_violations = sum(len(r.violations) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        total_fixed = sum(len(r.fixed_issues) for r in results)
        total_time = sum(r.execution_time for r in results)
        
        print("=" * 70)
        print(f"{Colors.BOLD}📊 CONSISTENCY CHECK SUMMARY{Colors.END}")
        print("=" * 70)
        print(f"Rules executed: {total_rules}")
        print(f"Rules passed: {Colors.GREEN}{passed_rules}{Colors.END}")
        print(f"Rules failed: {Colors.RED}{total_rules - passed_rules}{Colors.END}")
        print(f"Total violations: {Colors.RED}{total_violations}{Colors.END}")
        print(f"Total warnings: {Colors.YELLOW}{total_warnings}{Colors.END}")
        if total_fixed > 0:
            print(f"Issues fixed: {Colors.BLUE}{total_fixed}{Colors.END}")
        print(f"Execution time: {total_time:.2f}s")
        print()
        
        # Detailed violations
        if total_violations > 0:
            print(f"{Colors.RED}🚨 VIOLATIONS FOUND:{Colors.END}")
            for result in results:
                if result.violations:
                    print(f"\n{Colors.BOLD}{result.rule_name}:{Colors.END}")
                    for violation in result.violations[:5]:  # Show max 5 per rule
                        file_path = violation.get('file', 'unknown')
                        line = violation.get('line', 0)
                        message = violation.get('message', 'No message')
                        print(f"  {file_path}:{line} - {message}")
                    
                    if len(result.violations) > 5:
                        print(f"  ... and {len(result.violations) - 5} more violations")
        
        # Return exit code
        return 0 if total_violations == 0 else 1
    
    def list_rules(self):
        """List all available rules"""
        print(f"{Colors.BOLD}📋 Available Consistency Rules:{Colors.END}")
        print()
        
        if not self.available_rules:
            print(f"{Colors.YELLOW}No rules found in {self.rules_dir}{Colors.END}")
            print("Create rule directories with rule scripts to get started.")
            return
        
        for rule_name, rule_path in sorted(self.available_rules.items()):
            print(f"{Colors.CYAN}{rule_name}{Colors.END}")
            
            # Try to get rule description
            try:
                rule_module = self._load_rule_module(rule_name)
                description = getattr(rule_module, 'DESCRIPTION', 'No description available')
                print(f"  {description}")
                
                # Check if rule supports fixing
                if hasattr(rule_module, 'fix'):
                    print(f"  {Colors.GREEN}✅ Supports auto-fix{Colors.END}")
                
                # Show waiver count
                waiver_count = len(self.waivers.get(rule_name, []))
                if waiver_count > 0:
                    print(f"  {Colors.BLUE}🔒 {waiver_count} active waivers{Colors.END}")
                
            except Exception as e:
                print(f"  {Colors.RED}❌ Error loading rule: {e}{Colors.END}")
            
            print()


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Local Consistency Checker Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python checker.py --all                    # Run all rules
  python checker.py --rule python_imports   # Run specific rule
  python checker.py --rule naming --fix     # Run rule with auto-fix
  python checker.py --list-rules            # List available rules
        """
    )
    
    parser.add_argument('--all', action='store_true', 
                       help='Run all available consistency rules')
    parser.add_argument('--rule', type=str, 
                       help='Run a specific rule')
    parser.add_argument('--fix', action='store_true', 
                       help='Attempt to automatically fix violations')
    parser.add_argument('--list-rules', action='store_true', 
                       help='List all available rules')
    parser.add_argument('--json', action='store_true', 
                       help='Output results in JSON format')
    
    args = parser.parse_args()
    
    if not any([args.all, args.rule, args.list_rules]):
        parser.print_help()
        return
    
    try:
        checker = ConsistencyChecker()
        
        if args.list_rules:
            checker.list_rules()
            return
        
        results = []
        
        if args.all:
            results = checker.run_all_rules(fix=args.fix)
        elif args.rule:
            if args.rule not in checker.available_rules:
                print(f"{Colors.RED}❌ Rule '{args.rule}' not found{Colors.END}")
                print("Available rules:")
                for rule_name in sorted(checker.available_rules.keys()):
                    print(f"  - {rule_name}")
                sys.exit(1)
            
            result = checker.run_rule(args.rule, fix=args.fix)
            results = [result]
        
        if args.json:
            # Output JSON format
            json_results = []
            for result in results:
                json_results.append({
                    'rule_name': result.rule_name,
                    'passed': result.passed,
                    'violations': result.violations,
                    'warnings': result.warnings,
                    'fixed_issues': result.fixed_issues,
                    'execution_time': result.execution_time
                })
            print(json.dumps(json_results, indent=2))
        else:
            # Human-readable output
            exit_code = checker.print_summary(results)
            sys.exit(exit_code)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Check interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == '__main__':
    main()
