#!/usr/bin/env python3
"""
Consistency Checker Framework

A modular, extensible framework for enforcing coding standards and quality rules.
Supports pluggable rules, comprehensive waiver management, and detailed reporting.
"""

import sys
import importlib.util
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Annotated, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import time

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.style import Style
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.layout import Layout
from rich import print as rprint

# Import components
from base_rule import BaseRule, CheckResult, Violation, RuleMetadata, Severity, FixResult
from waiver_manager import WaiverManager
from report_generator import ReportGenerator

# Initialize Rich console
console = Console()

# Typer app with styling
app = typer.Typer(
    name="consistency-checker",
    help="Consistency Checker Framework - Comprehensive code quality enforcement",
    rich_markup_mode="rich",
    no_args_is_help=False,  # Allow custom callback for no args
    add_completion=False,   # Disabled for better cross-platform compatibility
)


class ConsistencyChecker:
    """Consistency checker framework with comprehensive features"""
    
    def __init__(self, repo_root: Path = None, config_file: Path = None):
        self.repo_root = repo_root or self._find_repo_root()
        self.checker_dir = self.repo_root / "devops" / "consistency_checker"
        self.rules_dir = self.checker_dir / "rules"
        
        # Load configuration
        self.config_file = config_file or (self.checker_dir / "checker_config.yml")
        self.config = self._load_config()
        
        # Initialize components
        self.waiver_manager = WaiverManager(self.rules_dir)
        self.report_generator = ReportGenerator(console)
        
        # Discover available rules
        self.available_rules = self._discover_rules()
        self.enabled_rules = self._get_enabled_rules()
        
        # Statistics
        self.stats = {
            'total_files_checked': 0,
            'total_lines_checked': 0,
            'execution_start_time': None,
            'execution_end_time': None
        }
    
    def _find_repo_root(self) -> Path:
        """Find the Git repository root"""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        console.print("[red]Error: Not in a Git repository[/red]")
        raise typer.Exit(1)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load checker configuration"""
        default_config = {
            'settings': {
                'max_issues_per_file': 50,
                'parallel_execution': True,
                'show_timing': False,
                'debug': False
            },
            'file_patterns': ['**/*.py', '**/*.pyx'],
            'exclude_patterns': [
                '**/__pycache__/**', '**/.*/**', '**/venv/**',
                '**/env/**', '**/build/**', '**/dist/**'
            ],
            'rules': {
                'enabled_rules': [],
                'disabled_rules': [],
            }
        }
        
        if self.config_file and self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = yaml.safe_load(f) or {}
                
                # Merge with defaults
                for key, value in loaded_config.items():
                    if key in default_config and isinstance(value, dict) and isinstance(default_config[key], dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
                        
                console.print(f"[green]Loaded configuration from {self.config_file}[/green]")
                
            except Exception as e:
                console.print(f"[yellow]Warning: Error loading config {self.config_file}: {e}[/yellow]")
                console.print("[yellow]Using default configuration[/yellow]")
        
        return default_config
    
    def _discover_rules(self) -> Dict[str, Dict[str, Any]]:
        """Discover available consistency rules with metadata"""
        rules = {}
        
        if not self.rules_dir.exists():
            return rules
            
        for rule_dir in self.rules_dir.iterdir():
            if rule_dir.is_dir() and rule_dir.name != '__pycache__':
                rule_script = rule_dir / f"{rule_dir.name}.py"
                if rule_script.exists():
                    try:
                        # Load rule module to get metadata
                        rule_module = self._load_rule_module(rule_dir.name, rule_script)
                        
                        # Get rule class (assume it's the main class in the module)
                        rule_class = None
                        for attr_name in dir(rule_module):
                            attr = getattr(rule_module, attr_name)
                            if (isinstance(attr, type) and 
                                issubclass(attr, BaseRule) and 
                                attr != BaseRule):
                                rule_class = attr
                                break
                        
                        if rule_class:
                            # Create instance to get metadata
                            rule_instance = rule_class()
                            metadata = rule_instance.get_metadata()
                            
                            rules[rule_dir.name] = {
                                'path': rule_script,
                                'class': rule_class,
                                'metadata': metadata,
                                'config_file': rule_dir / f"{rule_dir.name}_config.yml"
                            }
                        else:
                            console.print(f"[red]Error: Rule '{rule_dir.name}' does not have a proper BaseRule class. Please modernize this rule.[/red]")
                            continue
                            
                    except Exception as e:
                        console.print(f"[yellow]Warning: Error loading rule {rule_dir.name}: {e}[/yellow]")
        
        return rules
    
    def _get_enabled_rules(self) -> List[str]:
        """Get list of enabled rules based on configuration"""
        all_rule_names = list(self.available_rules.keys())
        
        # Get explicit configuration
        enabled_rules = self.config.get('rules', {}).get('enabled_rules', [])
        disabled_rules = self.config.get('rules', {}).get('disabled_rules', [])
        
        # If no explicit enabled rules, use all rules except disabled ones
        if not enabled_rules:
            enabled_rules = [name for name in all_rule_names if name not in disabled_rules]
        else:
            # Filter out disabled rules from enabled list
            enabled_rules = [name for name in enabled_rules if name not in disabled_rules]
        
        # Only include rules that exist
        enabled_rules = [name for name in enabled_rules if name in self.available_rules]
        
        return enabled_rules
    
    def _load_rule_module(self, rule_name: str, rule_path: Path = None):
        """Dynamically load a rule module"""
        if rule_path is None:
            # For discovery phase, compute path directly
            rule_path = self.rules_dir / rule_name / f"{rule_name}.py"
        
        if not rule_path.exists():
            raise ValueError(f"Rule file not found: {rule_path}")
        
        spec = importlib.util.spec_from_file_location(rule_name, rule_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    def _create_rule_instance(self, rule_name: str) -> BaseRule:
        """Create an instance of a rule with its configuration"""
        rule_info = self.available_rules[rule_name]
        
        # Load rule-specific configuration
        rule_config = {}
        config_file = rule_info.get('config_file')
        if config_file and config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    rule_config = yaml.safe_load(f) or {}
                rule_config = rule_config.get('parameters', {})
            except Exception as e:
                console.print(f"[yellow]Warning: Error loading config for {rule_name}: {e}[/yellow]")
        
        # Merge with global rule config
        global_rule_config = self.config.get('rules', {}).get('rule_config', {}).get(rule_name, {})
        rule_config.update(global_rule_config)
        
        # Create rule instance
        if rule_info['class']:
            # New-style rule with BaseRule inheritance
            return rule_info['class'](rule_config)
        else:
            # No proper rule class found - rule needs to be modernized
            console.print(f"[red]Error: Rule '{rule_name}' does not have a proper BaseRule class. Please modernize this rule.[/red]")
            raise ValueError(f"Rule '{rule_name}' is not properly implemented - missing BaseRule class")
    
    def list_rules(self, verbose: bool = False, show_status: bool = True):
        """List all available rules with their status and metadata"""
        
        # Show header
        if show_status:
            console.print(Panel(
                Text.from_markup(
                    f"[bold]Repository:[/bold] {self.repo_root}\n"
                    f"[bold]Rules Available:[/bold] {len(self.available_rules)}\n"
                    f"[bold]Rules Enabled:[/bold] [green]{len(self.enabled_rules)}[/green]\n"
                    f"[bold]Rules Disabled:[/bold] [red]{len(self.available_rules) - len(self.enabled_rules)}[/red]"
                ),
                title="[bold cyan]Rule Status Overview[/bold cyan]",
                border_style="cyan",
                expand=False
            ))
            console.print()
        
        # Create rules table
        table = Table(
            title="[bold]Available Consistency Rules[/bold]",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            expand=True
        )
        
        table.add_column("Rule", style="bold", no_wrap=True)
        table.add_column("Status", justify="center", no_wrap=True)
        table.add_column("Category", style="dim")
        table.add_column("Description")
        
        if verbose:
            table.add_column("Version", style="dim", no_wrap=True)
            table.add_column("Auto-fix", justify="center", no_wrap=True)
            table.add_column("Performance", style="dim", no_wrap=True)
        
        for rule_name in sorted(self.available_rules.keys()):
            rule_info = self.available_rules[rule_name]
            metadata = rule_info.get('metadata')
            
            # Status
            if rule_name in self.enabled_rules:
                status = "[green]ENABLED[/green]"
            else:
                status = "[red]DISABLED[/red]"
            
            # Basic info
            category = metadata.category if metadata else "unknown"
            description = metadata.description if metadata else "No description available"
            
            row = [rule_name, status, category, description]
            
            if verbose and metadata:
                version = metadata.version
                auto_fix = "[green]Yes[/green]" if metadata.supports_auto_fix else "[red]No[/red]"
                performance = f"{metadata.estimated_runtime}/{metadata.memory_usage}"
                row.extend([version, auto_fix, performance])
            elif verbose:
                row.extend(["unknown", "[dim]N/A[/dim]", "[dim]N/A[/dim]"])
            
            table.add_row(*row)
        
        console.print(table)
        
        if show_status:
            # Show waiver statistics
            waiver_stats = self.waiver_manager.get_waiver_statistics()
            if waiver_stats['total_waivers'] > 0:
                console.print(f"\n[blue]ℹ Waivers configured: {waiver_stats['total_waivers']} total, "
                            f"{waiver_stats['active_waivers']} active, "
                            f"{waiver_stats['expired_waivers']} expired[/blue]")
            
            console.print(f"\n[dim]Run specific rule:[/dim] [bold]checker run-rule [rule_name][/bold]")
            console.print(f"[dim]Run all enabled rules:[/dim] [bold]checker run-all[/bold]")
    
    def run_rule(
        self, 
        rule_name: str, 
        files: Optional[List[Path]] = None,
        fix: bool = False, 
        verbose: bool = False
    ) -> CheckResult:
        """Run a specific consistency rule"""
        
        if rule_name not in self.available_rules:
            available = ', '.join(sorted(self.available_rules.keys()))
            console.print(f"[red]Error: Rule '{rule_name}' not found[/red]")
            console.print(f"[yellow]Available rules: {available}[/yellow]")
            raise typer.Exit(1)
        
        if rule_name not in self.enabled_rules:
            console.print(f"[yellow]Warning: Rule '{rule_name}' is disabled[/yellow]")
            if not Confirm.ask("Run anyway?"):
                raise typer.Exit(0)
        
        start_time = datetime.now()
        
        try:
            # Create rule instance
            rule = self._create_rule_instance(rule_name)
            
            if verbose:
                console.print(f"[blue]Running rule: {rule_name}[/blue]")
                if rule.get_metadata():
                    console.print(f"[dim]Description: {rule.get_metadata().description}[/dim]")
            
            # Execute rule
            result = rule.check(self.repo_root, files)
            
            # Apply waivers
            if result.violations:
                remaining_violations, waived_violations = self.waiver_manager.apply_waivers(
                    result.violations, str(self.repo_root)
                )
                result.violations = remaining_violations
                result.waived_violations = waived_violations
                result.waiver_count = len(waived_violations)
            
            # Run auto-fix if requested
            if fix and result.violations and hasattr(rule, 'fix'):
                try:
                    console.print(f"[yellow]Attempting to fix {len(result.violations)} violations...[/yellow]")
                    fix_result = rule.fix(self.repo_root, result.violations)
                    result.fix_result = fix_result
                    
                    if fix_result.fixed_violations:
                        console.print(f"[green]Fixed {len(fix_result.fixed_violations)} violations[/green]")
                        
                        # Update violation list (remove fixed violations)
                        fixed_ids = {v.id for v in fix_result.fixed_violations}
                        result.violations = [v for v in result.violations if v.id not in fixed_ids]
                    
                except Exception as e:
                    console.print(f"[yellow]Warning: Auto-fix failed: {e}[/yellow]")
            
            # Update execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                rule_name=rule_name,
                success=False,
                error_message=str(e),
                execution_time=execution_time,
                violations=[],
                warnings=[]
            )
    
    def run_all_rules(
        self, 
        files: Optional[List[Path]] = None,
        fix: bool = False, 
        verbose: bool = False
    ) -> List[CheckResult]:
        """Run all enabled consistency rules"""
        
        if not self.enabled_rules:
            console.print("[yellow]No rules enabled. Check your configuration.[/yellow]")
            return []
        
        self.stats['execution_start_time'] = datetime.now()
        results = []
        
        # Show execution header
        console.print(Panel(
            Text.from_markup(
                f"[bold]Repository:[/bold] {self.repo_root}\n"
                f"[bold]Enabled Rules:[/bold] {len(self.enabled_rules)}\n"
                f"[bold]Fix Mode:[/bold] {'Enabled' if fix else 'Disabled'}\n"
                f"[bold]Target:[/bold] {'Specific files' if files else 'All files'}"
            ),
            title="[bold cyan]Consistency Check Execution[/bold cyan]",
            border_style="cyan",
            expand=False
        ))
        console.print()
        
        # Execute rules with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("[bold cyan]Executing rules...[/bold cyan]", total=len(self.enabled_rules))
            
            for rule_name in sorted(self.enabled_rules):
                progress.update(task, description=f"[bold cyan]Running:[/bold cyan] [yellow]{rule_name}[/yellow]")
                
                result = self.run_rule(rule_name, files, fix, verbose)
                results.append(result)
                
                # Update statistics
                self.stats['total_files_checked'] += result.files_checked
                self.stats['total_lines_checked'] += result.lines_checked
                
                # Show immediate feedback
                if result.success:
                    if result.passed:
                        status_msg = f"[green]✓ PASSED[/green] {rule_name}"
                    else:
                        violations = len([v for v in result.violations if v.severity in [Severity.ERROR, Severity.CRITICAL]])
                        status_msg = f"[red]✗ FAILED[/red] {rule_name} ([red]{violations} issues[/red])"
                else:
                    status_msg = f"[red]✗ ERROR[/red] {rule_name} ({result.error_message})"
                
                timing = f"({result.execution_time:.2f}s)"
                progress.console.print(f"{status_msg} {timing}")
                
                if result.fix_result and result.fix_result.fixed_violations:
                    progress.console.print(f"[blue]  ↻ Fixed {len(result.fix_result.fixed_violations)} issues[/blue]")
                
                progress.advance(task)
        
        self.stats['execution_end_time'] = datetime.now()
        
        return results
    
    def generate_report(
        self,
        results: List[CheckResult],
        format_type: str = "console",
        output_file: Optional[Path] = None,
        show_details: bool = True
    ) -> int:
        """Generate comprehensive report"""
        
        if format_type == "console":
            return self.report_generator.generate_console_report(
                results, self.waiver_manager, show_details, True
            )
        elif format_type == "html":
            if not output_file:
                output_file = Path("consistency_report.html")
            self.report_generator.generate_html_report(results, output_file, self.waiver_manager)
            return 0
        elif format_type == "json":
            if not output_file:
                output_file = Path("consistency_report.json")
            self.report_generator.generate_json_report(results, output_file, self.waiver_manager)
            return 0
        elif format_type == "csv":
            if not output_file:
                output_file = Path("consistency_report.csv")
            self.report_generator.generate_csv_report(results, output_file)
            return 0
        else:
            console.print(f"[red]Error: Unknown report format '{format_type}'[/red]")
            return 1


# Initialize the checker instance
checker = ConsistencyChecker()


@app.command(name="run-all")
def run_all(
    fix: Annotated[bool, typer.Option("--fix", "-f", help="Attempt to automatically fix violations")] = False,
    format_type: Annotated[str, typer.Option("--format", help="Output format: console, html, json, csv")] = "console",
    output_file: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed information")] = False,
    files: Annotated[Optional[List[str]], typer.Option("--files", help="Specific files to check")] = None,
):
    """Run all enabled consistency rules"""
    
    # Convert file paths if provided
    file_paths = [Path(f) for f in files] if files else None
    
    # Run all rules
    results = checker.run_all_rules(file_paths, fix=fix, verbose=verbose)
    
    # Generate report
    output_path = Path(output_file) if output_file else None
    exit_code = checker.generate_report(results, format_type, output_path, verbose)
    
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command(name="run-rule")
def run_rule(
    rule_name: Annotated[str, typer.Argument(help="Name of the rule to run")],
    fix: Annotated[bool, typer.Option("--fix", "-f", help="Attempt to automatically fix violations")] = False,
    format_type: Annotated[str, typer.Option("--format", help="Output format: console, html, json, csv")] = "console",
    output_file: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed information")] = False,
    files: Annotated[Optional[List[str]], typer.Option("--files", help="Specific files to check")] = None,
):
    """Run a specific consistency rule"""
    
    # Convert file paths if provided
    file_paths = [Path(f) for f in files] if files else None
    
    # Run single rule
    result = checker.run_rule(rule_name, file_paths, fix=fix, verbose=verbose)
    results = [result]
    
    # Generate report
    output_path = Path(output_file) if output_file else None
    exit_code = checker.generate_report(results, format_type, output_path, verbose)
    
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command(name="list-rules")
def list_rules(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed information")] = False,
    status: Annotated[bool, typer.Option("--status", help="Show rule status overview")] = True,
):
    """List all available consistency rules"""
    checker.list_rules(verbose=verbose, show_status=status)


@app.command(name="show-waivers")
def show_waivers(
    expired: Annotated[bool, typer.Option("--expired", help="Show only expired waivers")] = False,
    unused: Annotated[bool, typer.Option("--unused", help="Show only unused waivers")] = False,
    expiring: Annotated[int, typer.Option("--expiring", help="Show waivers expiring within N days")] = 0,
    export_unused: Annotated[Optional[str], typer.Option("--export-unused", help="Export unused waivers to file")] = None,
    all_status: Annotated[bool, typer.Option("--all", help="Show all waivers with status columns")] = False,
):
    """Show configured waivers and their status"""
    
    if not checker.waiver_manager.waivers:
        console.print("[yellow]No waivers configured[/yellow]")
        return
    
    # Get waiver statistics
    stats = checker.waiver_manager.get_waiver_statistics()
    
    # Show header
    console.print(Panel(
        Text.from_markup(
            f"[bold]Total Waivers:[/bold] {stats['total_waivers']}\n"
            f"[bold]Active:[/bold] [green]{stats['active_waivers']}[/green]\n"
            f"[bold]Expired:[/bold] [red]{stats['expired_waivers']}[/red]\n"
            f"[bold]Unused:[/bold] [yellow]{stats['unused_waivers']}[/yellow]\n"
            f"[bold]Used:[/bold] [blue]{stats['used_waivers']}[/blue]"
        ),
        title="[bold cyan]Waiver Statistics[/bold cyan]",
        border_style="cyan",
        expand=False
    ))
    console.print()
    
    # Get waivers to show based on filters
    waivers_to_show = checker.waiver_manager.waivers.copy()
    
    if expired:
        waivers_to_show = [w for w in waivers_to_show if w.is_expired()]
        table_title = "[bold red]Expired Waivers[/bold red]"
    elif unused:
        waivers_to_show = [w for w in waivers_to_show if w.usage_count == 0]
        table_title = "[bold yellow]Unused Waivers[/bold yellow]"
    elif expiring > 0:
        waivers_to_show = [w for w in waivers_to_show if w.days_until_expiry() is not None and 0 <= w.days_until_expiry() <= expiring]
        table_title = f"[bold orange3]Waivers Expiring Within {expiring} Days[/bold orange3]"
    else:
        table_title = "[bold]All Configured Waivers[/bold]"
    
    if not waivers_to_show:
        filter_text = "expired" if expired else "unused" if unused else f"expiring within {expiring} days" if expiring else "configured"
        console.print(f"[green]No {filter_text} waivers found[/green]")
        return
    
    # Create table
    table = Table(
        title=table_title,
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        expand=True
    )
    
    # Add columns
    table.add_column("ID", style="bold", no_wrap=True, width=20)
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Pattern/Rule", style="yellow", width=25)
    table.add_column("Reason", style="dim", width=30)
    
    if all_status or not any([expired, unused, expiring]):
        table.add_column("Status", justify="center", no_wrap=True)
        table.add_column("Usage", justify="center", no_wrap=True)
        table.add_column("Expires", style="dim", no_wrap=True)
    
    table.add_column("Approved By", style="green", no_wrap=True)
    
    # Add rows
    for waiver in sorted(waivers_to_show, key=lambda w: (w.type.value, w.id)):
        # Basic info
        waiver_id = waiver.id or f"{waiver.type.value}_{hash(waiver.pattern) % 10000}"
        waiver_type = waiver.type.value.replace('_', ' ').title()
        
        # Pattern/Rule info
        if waiver.rule_names:
            pattern_rule = f"Rules: {', '.join(waiver.rule_names[:2])}" + ("..." if len(waiver.rule_names) > 2 else "")
        elif waiver.file_pattern:
            pattern_rule = f"Files: {waiver.file_pattern}"
        else:
            pattern_rule = waiver.pattern or "N/A"
        
        # Truncate long text
        reason = (waiver.reason[:27] + "...") if len(waiver.reason) > 30 else waiver.reason
        approved_by = waiver.approved_by or "N/A"
        
        row = [waiver_id, waiver_type, pattern_rule, reason]
        
        # Add status columns if requested
        if all_status or not any([expired, unused, expiring]):
            # Status
            if waiver.is_expired():
                status = "[red]EXPIRED[/red]"
            elif not waiver.active:
                status = "[dim]DISABLED[/dim]"
            else:
                status = "[green]ACTIVE[/green]"
            
            # Usage
            if waiver.usage_count == 0:
                usage = "[yellow]UNUSED[/yellow]"
            else:
                usage = f"[blue]{waiver.usage_count}x[/blue]"
            
            # Expiration
            if waiver.expires:
                days_left = waiver.days_until_expiry()
                if days_left is not None:
                    if days_left < 0:
                        expires = f"[red]{abs(days_left)}d ago[/red]"
                    elif days_left < 7:
                        expires = f"[orange3]{days_left}d left[/orange3]"
                    elif days_left < 30:
                        expires = f"[yellow]{days_left}d left[/yellow]"
                    else:
                        expires = f"[green]{days_left}d left[/green]"
                else:
                    expires = "[dim]N/A[/dim]"
            else:
                expires = "[dim]Never[/dim]"
            
            row.extend([status, usage, expires])
        
        row.append(approved_by)
        table.add_row(*row)
    
    console.print(table)
    
    # Export unused waivers if requested
    if export_unused:
        unused_waivers = [w for w in checker.waiver_manager.waivers if w.usage_count == 0]
        if unused_waivers:
            export_path = Path(export_unused)
            try:
                # Export to YAML format for easy review and cleanup
                export_data = {
                    'metadata': {
                        'exported_at': datetime.now().isoformat(),
                        'total_unused_waivers': len(unused_waivers),
                        'source_file': str(checker.waiver_manager.waiver_file),
                        'note': 'These waivers have never been used. Review before deletion.'
                    },
                    'unused_waivers': []
                }
                
                for waiver in unused_waivers:
                    waiver_dict = {
                        'id': waiver.id,
                        'type': waiver.type.value,
                        'pattern': waiver.pattern,
                        'rule_names': waiver.rule_names,
                        'file_pattern': waiver.file_pattern,
                        'reason': waiver.reason,
                        'approved_by': waiver.approved_by,
                        'created_date': waiver.created_date.isoformat() if waiver.created_date else None,
                        'expires': waiver.expires.isoformat() if waiver.expires else None,
                        'usage_count': waiver.usage_count,
                        'last_used': waiver.last_used.isoformat() if waiver.last_used else None
                    }
                    export_data['unused_waivers'].append(waiver_dict)
                
                with open(export_path, 'w') as f:
                    yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
                
                console.print(f"\n[green]✅ Exported {len(unused_waivers)} unused waivers to: {export_path}[/green]")
                console.print(f"[dim]Review the file and remove unused waivers from your main configuration.[/dim]")
                
            except Exception as e:
                console.print(f"\n[red]❌ Error exporting unused waivers: {e}[/red]")
        else:
            console.print(f"\n[green]✅ No unused waivers to export[/green]")
    
    # Show usage suggestions
    if unused and waivers_to_show:
        console.print(f"\n[blue]💡 Tip: Use --export-unused filename.yml to export these for cleanup[/blue]")
    elif not any([expired, unused, expiring]) and stats['unused_waivers'] > 0:
        console.print(f"\n[blue]💡 Use --unused to see {stats['unused_waivers']} unused waivers that can be cleaned up[/blue]")
    
    # Show header
    console.print(Panel(
        Text.from_markup(
            f"[bold]Total Waivers:[/bold] {stats['total_waivers']}\n"
            f"[bold]Active Waivers:[/bold] [green]{stats['active_waivers']}[/green]\n"
            f"[bold]Expired Waivers:[/bold] [red]{stats['expired_waivers']}[/red]\n"
            f"[bold]Unused Waivers:[/bold] [yellow]{stats['unused_waivers']}[/yellow]\n"
            f"[bold]Expiring Soon:[/bold] [yellow]{stats['expiring_soon']}[/yellow]"
        ),
        title="[bold cyan]Waiver Overview[/bold cyan]",
        border_style="cyan",
        expand=False
    ))
    
    # Filter waivers based on options
    waivers_to_show = checker.waiver_manager.waivers
    
    if expired:
        waivers_to_show = checker.waiver_manager.get_expired_waivers()
        console.print(f"\n[red]Expired Waivers ({len(waivers_to_show)}):[/red]")
    elif unused:
        waivers_to_show = checker.waiver_manager.get_unused_waivers()
        console.print(f"\n[yellow]Unused Waivers ({len(waivers_to_show)}):[/yellow]")
    elif expiring > 0:
        waivers_to_show = checker.waiver_manager.get_expiring_waivers(expiring)
        console.print(f"\n[yellow]Waivers Expiring Within {expiring} Days ({len(waivers_to_show)}):[/yellow]")
    
    if not waivers_to_show:
        console.print("[green]No waivers match the specified criteria[/green]")
        return
    
    # Create waiver table
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        expand=True
    )
    
    table.add_column("ID", style="bold", no_wrap=True)
    table.add_column("Type", style="dim")
    table.add_column("Rules", style="blue")
    table.add_column("Pattern/File", style="yellow")
    table.add_column("Reason", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Usage", justify="right", style="dim")
    
    for waiver in waivers_to_show[:20]:  # Limit to first 20 for readability
        # Status
        if waiver.is_expired():
            status = "[red]Expired[/red]"
        elif waiver.days_until_expiry() and waiver.days_until_expiry() <= 14:
            days_left = waiver.days_until_expiry()
            status = f"[yellow]Expires in {days_left}d[/yellow]"
        else:
            status = "[green]Active[/green]"
        
        # Rules
        rules_text = ", ".join(waiver.rule_names) if waiver.rule_names else "All"
        if len(rules_text) > 30:
            rules_text = rules_text[:27] + "..."
        
        # Pattern/File
        pattern = waiver.file_pattern or waiver.pattern
        if len(pattern) > 40:
            pattern = pattern[:37] + "..."
        
        # Reason
        reason = waiver.reason
        if len(reason) > 50:
            reason = reason[:47] + "..."
        
        table.add_row(
            waiver.id,
            waiver.type.value,
            rules_text,
            pattern,
            reason,
            status,
            str(waiver.usage_count)
        )
    
    console.print(table)
    
    if len(waivers_to_show) > 20:
        console.print(f"\n[dim]... and {len(waivers_to_show) - 20} more waivers[/dim]")


@app.command(name="validate-waivers")
def validate_waivers():
    """Validate all configured waivers"""
    issues = checker.waiver_manager.validate_waivers()
    
    has_issues = any(issues.values())
    
    if not has_issues:
        console.print("[green]✓ All waivers are valid[/green]")
        return
    
    console.print("[yellow]⚠ Waiver validation issues found:[/yellow]\n")
    
    for issue_type, issue_list in issues.items():
        if issue_list:
            console.print(f"[bold]{issue_type.replace('_', ' ').title()}:[/bold]")
            for issue in issue_list:
                console.print(f"  • {issue}")
            console.print()


@app.command(name="config")
def show_config():
    """Show current configuration"""
    console.print(Panel(
        Syntax(yaml.dump(checker.config, default_flow_style=False), "yaml"),
        title="[bold cyan]Current Configuration[/bold cyan]",
        border_style="cyan",
        expand=False
    ))


@app.command(name="stats")
def show_stats():
    """Show checker statistics and system information"""
    
    # System info
    console.print(Panel(
        Text.from_markup(
            f"[bold]Repository:[/bold] {checker.repo_root}\n"
            f"[bold]Rules Directory:[/bold] {checker.rules_dir}\n"
            f"[bold]Config File:[/bold] {checker.config_file}\n"
            f"[bold]Available Rules:[/bold] {len(checker.available_rules)}\n"
            f"[bold]Enabled Rules:[/bold] {len(checker.enabled_rules)}\n"
            f"[bold]Total Waivers:[/bold] {len(checker.waiver_manager.waivers)}"
        ),
        title="[bold cyan]System Information[/bold cyan]",
        border_style="cyan",
        expand=False
    ))
    
    # Execution statistics
    if checker.stats['execution_start_time']:
        total_time = (checker.stats['execution_end_time'] - checker.stats['execution_start_time']).total_seconds()
        console.print(Panel(
            Text.from_markup(
                f"[bold]Last Execution:[/bold] {checker.stats['execution_start_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"[bold]Total Time:[/bold] {total_time:.2f}s\n"
                f"[bold]Files Checked:[/bold] {checker.stats['total_files_checked']}\n"
                f"[bold]Lines Checked:[/bold] {checker.stats['total_lines_checked']}"
            ),
            title="[bold cyan]Last Execution Statistics[/bold cyan]",
            border_style="blue",
            expand=False
        ))


if __name__ == '__main__':
    # Check if no arguments provided
    if len(sys.argv) == 1:
        console.print("[bold blue]Consistency Checker Framework[/bold blue]")
        console.print("Welcome! This tool enforces coding standards and quality rules.")
        console.print("\n[cyan]Available commands:[/cyan]")
        console.print("  • [bold]run-all[/bold] - Run all enabled consistency rules")
        console.print("  • [bold]run-rule[/bold] - Run a specific rule by name")
        console.print("  • [bold]list-rules[/bold] - Show all available rules")
        console.print("  • [bold]show-waivers[/bold] - Display configured waivers")
        console.print("  • [bold]validate-waivers[/bold] - Check waiver configuration")
        console.print("  • [bold]config[/bold] - Show current configuration")
        console.print("  • [bold]stats[/bold] - Show system statistics")
        console.print("\n[green]Quick start:[/green] consistency_checker run-all")
        console.print("[blue]For help:[/blue] consistency_checker --help")
    else:
        app()
