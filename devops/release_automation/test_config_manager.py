#!/usr/bin/env python3
"""
Modular Test Configuration Manager

A CLI tool for managing the modular test framework configuration.
Provides easy ways to add tests, modify weights, and validate configuration.

Usage:
    python devops/release_automation/test_config_manager.py list
    python devops/release_automation/test_config_manager.py add-test my_test "My Custom Test" --weight 15 --action-path .github/actions/my-test
    python devops/release_automation/test_config_manager.py validate
"""

import json
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Annotated, Optional, List
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax
from rich.prompt import Confirm, Prompt, IntPrompt, FloatPrompt
from rich.columns import Columns
from rich.layout import Layout
from rich import print as rprint


# Initialize Rich console
console = Console()

# Typer app
app = typer.Typer(
    name="test-config-manager",
    help="Modular Test Configuration Manager - Manage test framework configuration",
    rich_markup_mode="rich",
    no_args_is_help=False,  # Allow custom callback for no args
    add_completion=False,   # Disabled for better cross-platform compatibility
    context_settings={"help_option_names": ["-h", "--help"]},  # Enable -h support
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
):
    """
    Modular Test Configuration Manager
    
    A CLI tool for managing the modular test framework configuration.
    Provides easy ways to add tests, modify weights, and validate configuration.
    """
    if ctx.invoked_subcommand is None:
        console.print("[bold blue]Modular Test Configuration Manager[/bold blue]")
        console.print("A CLI tool for managing the modular test framework configuration.")
        console.print("\n[cyan]Available commands:[/cyan]")
        console.print("  • [bold]list[/bold] - List all configured tests")
        console.print("  • [bold]add[/bold] - Add a new test to the configuration")
        console.print("  • [bold]update[/bold] - Update an existing test")
        console.print("  • [bold]remove[/bold] - Remove a test from the configuration")
        console.print("  • [bold]validate[/bold] - Validate the configuration for common issues")
        console.print("  • [bold]show[/bold] - Show the full configuration file")
        console.print("  • [bold]set-thresholds[/bold] - Set global thresholds for test scoring")
        console.print("\n[green]Quick start:[/green] test_config_manager.py list")
        console.print("[blue]For help:[/blue] test_config_manager.py --help")
        return


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
        console.print("[red]Error: Not in a Git repository[/red]")
        raise typer.Exit(1)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            console.print(f"[yellow]Configuration file not found: {self.config_path}[/yellow]")
            console.print("[cyan]Creating default configuration...[/cyan]")
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                console.print(f"[green]Loaded configuration from {self.config_path}[/green]")
                return config
        except yaml.YAMLError as e:
            console.print(f"[red]Invalid YAML in configuration file: {e}[/red]")
            raise typer.Exit(1)
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        default_config = {
            "global_config": {
                "auto_merge_threshold": 85,
                "manual_review_threshold": 65,
                "block_threshold": 64
            },
            "test_suite": [
                {
                    "name": "lint_check",
                    "display_name": "Code Linting",
                    "weight": 25,
                    "action_path": ".github/actions/lint-check",
                    "required": True,
                    "category": "code_quality"
                },
                {
                    "name": "security_scan",
                    "display_name": "Security Scan",
                    "weight": 20,
                    "action_path": ".github/actions/security-scan",
                    "required": True,
                    "category": "security"
                },
                {
                    "name": "unit_tests",
                    "display_name": "Unit Tests",
                    "weight": 25,
                    "action_path": ".github/actions/unit-tests",
                    "required": False,
                    "category": "testing"
                },
                {
                    "name": "documentation",
                    "display_name": "Documentation Check",
                    "weight": 15,
                    "action_path": ".github/actions/documentation-check",
                    "required": False,
                    "category": "documentation"
                },
                {
                    "name": "compliance",
                    "display_name": "Compliance Check",
                    "weight": 15,
                    "action_path": ".github/actions/compliance-check",
                    "required": False,
                    "category": "compliance"
                }
            ]
        }
        
        # Save the default configuration
        self._save_config_data(default_config)
        return default_config
    
    def _save_config(self):
        """Save configuration to YAML file."""
        self._save_config_data(self.config)
    
    def _save_config_data(self, config_data: Dict[str, Any]):
        """Save given configuration data to YAML file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        console.print(f"[green]Configuration saved to {self.config_path}[/green]")
    
    def list_tests(self, show_details: bool = False):
        """List all configured tests."""
        tests = self.config.get("test_suite", [])
        global_config = self.config.get("global_config", {})
        
        # Show global configuration
        global_panel = Panel(
            Text.from_markup(
                f"[bold]Auto-merge threshold:[/bold] [green]{global_config.get('auto_merge_threshold', 85)}%[/green]\n"
                f"[bold]Manual review threshold:[/bold] [yellow]{global_config.get('manual_review_threshold', 65)}%[/yellow]\n"
                f"[bold]Block threshold:[/bold] [red]{global_config.get('block_threshold', 64)}%[/red]"
            ),
            title="[bold cyan]Global Configuration[/bold cyan]",
            border_style="cyan"
        )
        console.print(global_panel)
        
        if not tests:
            console.print("[yellow]No tests configured[/yellow]")
            return
        
        # Create a detailed table
        table = Table(title=f"Test Suite Configuration ({len(tests)} tests)")
        table.add_column("Name", style="cyan")
        table.add_column("Display Name", style="white")
        table.add_column("Weight", style="yellow", justify="right")
        table.add_column("Required", style="green")
        table.add_column("Category", style="blue")
        
        if show_details:
            table.add_column("Action Path", style="dim")
        
        # Group tests by category
        categories = {}
        total_weight = 0
        
        for test in tests:
            category = test.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(test)
            total_weight += test.get('weight', 0)
        
        # Add tests to table, grouped by category
        for category, category_tests in sorted(categories.items()):
            for i, test in enumerate(category_tests):
                name = test.get('name', 'unknown')
                display_name = test.get('display_name', name)
                weight = test.get('weight', 0)
                required = "Yes" if test.get('required', False) else "No"
                category_name = category.replace('_', ' ').title()
                
                row = [name, display_name, f"{weight}%", required, category_name]
                
                if show_details:
                    action_path = test.get('action_path', 'Not specified')
                    row.append(action_path)
                
                table.add_row(*row)
        
        console.print(table)
        
        # Show summary
        summary = Panel(
            f"[bold]Total tests:[/bold] {len(tests)}\n"
            f"[bold]Total weight:[/bold] {total_weight}%\n"
            f"[bold]Categories:[/bold] {len(categories)}",
            title="[bold green]Summary[/bold green]",
            border_style="green"
        )
        console.print(summary)
    
    def add_test(self, name: str, display_name: str, weight: int, 
                 action_path: str, required: bool = False, category: str = "other"):
        """Add a new test to the configuration."""
        tests = self.config.get("test_suite", [])
        
        # Check if test already exists
        existing_test = next((test for test in tests if test.get('name') == name), None)
        if existing_test:
            console.print(f"[red]Test '{name}' already exists[/red]")
            
            if Confirm.ask("[yellow]Do you want to update the existing test?[/yellow]"):
                self.update_test(name, display_name, weight, action_path, required, category)
            return
        
        # Validate weight
        current_total = sum(test.get('weight', 0) for test in tests)
        if current_total + weight > 100:
            console.print(f"[red]Total weight would exceed 100% (current: {current_total}%, adding: {weight}%)[/red]")
            
            if not Confirm.ask("[yellow]Continue anyway?[/yellow]"):
                return
        
        # Create new test
        new_test = {
            "name": name,
            "display_name": display_name,
            "weight": weight,
            "action_path": action_path,
            "required": required,
            "category": category
        }
        
        tests.append(new_test)
        self.config["test_suite"] = tests
        self._save_config()
        
        console.print(f"[green]Added test '{name}' successfully[/green]")
        
        # Show the new test
        self._show_test_details(new_test)
    
    def update_test(self, name: str, display_name: str = None, weight: int = None,
                   action_path: str = None, required: bool = None, category: str = None):
        """Update an existing test."""
        tests = self.config.get("test_suite", [])
        
        # Find the test
        test_index = None
        for i, test in enumerate(tests):
            if test.get('name') == name:
                test_index = i
                break
        
        if test_index is None:
            console.print(f"[red]Test '{name}' not found[/red]")
            return
        
        # Update fields
        test = tests[test_index]
        old_test = test.copy()
        
        if display_name is not None:
            test['display_name'] = display_name
        if weight is not None:
            test['weight'] = weight
        if action_path is not None:
            test['action_path'] = action_path
        if required is not None:
            test['required'] = required
        if category is not None:
            test['category'] = category
        
        self.config["test_suite"] = tests
        self._save_config()
        
        console.print(f"[green]Updated test '{name}' successfully[/green]")
        
        # Show changes
        changes_table = Table(title="Changes Made")
        changes_table.add_column("Field", style="cyan")
        changes_table.add_column("Old Value", style="red")
        changes_table.add_column("New Value", style="green")
        
        for field in ['display_name', 'weight', 'action_path', 'required', 'category']:
            old_value = old_test.get(field)
            new_value = test.get(field)
            if old_value != new_value:
                changes_table.add_row(field, str(old_value), str(new_value))
        
        if changes_table.rows:
            console.print(changes_table)
    
    def remove_test(self, name: str):
        """Remove a test from the configuration."""
        tests = self.config.get("test_suite", [])
        
        # Find and remove the test
        test_to_remove = None
        for i, test in enumerate(tests):
            if test.get('name') == name:
                test_to_remove = tests.pop(i)
                break
        
        if test_to_remove is None:
            console.print(f"[red]Test '{name}' not found[/red]")
            return
        
        self.config["test_suite"] = tests
        self._save_config()
        
        console.print(f"[green]Removed test '{name}' successfully[/green]")
        self._show_test_details(test_to_remove, title="Removed Test")
    
    def _show_test_details(self, test: Dict[str, Any], title: str = "Test Details"):
        """Show details of a single test."""
        details = Text.from_markup(
            f"[bold]Name:[/bold] {test.get('name', 'unknown')}\n"
            f"[bold]Display Name:[/bold] {test.get('display_name', 'N/A')}\n"
            f"[bold]Weight:[/bold] {test.get('weight', 0)}%\n"
            f"[bold]Required:[/bold] {'Yes' if test.get('required', False) else 'No'}\n"
            f"[bold]Category:[/bold] {test.get('category', 'other')}\n"
            f"[bold]Action Path:[/bold] {test.get('action_path', 'N/A')}"
        )
        
        panel = Panel(details, title=f"[bold cyan]{title}[/bold cyan]", border_style="cyan")
        console.print(panel)
    
    def validate_config(self):
        """Validate the configuration for common issues."""
        tests = self.config.get("test_suite", [])
        global_config = self.config.get("global_config", {})
        
        issues = []
        warnings = []
        
        # Check global config
        thresholds = {
            'auto_merge_threshold': global_config.get('auto_merge_threshold'),
            'manual_review_threshold': global_config.get('manual_review_threshold'),
            'block_threshold': global_config.get('block_threshold')
        }
        
        for name, value in thresholds.items():
            if value is None:
                issues.append(f"Missing {name} in global configuration")
            elif not isinstance(value, (int, float)) or value < 0 or value > 100:
                issues.append(f"Invalid {name}: {value} (must be 0-100)")
        
        # Check threshold logic
        auto_merge = thresholds.get('auto_merge_threshold', 0)
        manual_review = thresholds.get('manual_review_threshold', 0)
        block = thresholds.get('block_threshold', 0)
        
        if auto_merge <= manual_review:
            issues.append(f"Auto-merge threshold ({auto_merge}) should be higher than manual review threshold ({manual_review})")
        
        if manual_review <= block:
            warnings.append(f"Manual review threshold ({manual_review}) should be higher than block threshold ({block})")
        
        # Check tests
        if not tests:
            warnings.append("No tests configured")
        else:
            total_weight = 0
            names = set()
            
            for i, test in enumerate(tests):
                test_name = test.get('name')
                if not test_name:
                    issues.append(f"Test {i} missing name")
                elif test_name in names:
                    issues.append(f"Duplicate test name: {test_name}")
                else:
                    names.add(test_name)
                
                weight = test.get('weight')
                if weight is None:
                    issues.append(f"Test '{test_name}' missing weight")
                elif not isinstance(weight, (int, float)) or weight < 0:
                    issues.append(f"Test '{test_name}' has invalid weight: {weight}")
                else:
                    total_weight += weight
                
                if not test.get('display_name'):
                    warnings.append(f"Test '{test_name}' missing display name")
                
                if not test.get('action_path'):
                    warnings.append(f"Test '{test_name}' missing action path")
            
            if total_weight != 100:
                if total_weight > 100:
                    issues.append(f"Total weight exceeds 100%: {total_weight}%")
                else:
                    warnings.append(f"Total weight is less than 100%: {total_weight}%")
        
        # Display results
        if not issues and not warnings:
            console.print(Panel(
                "[green]Configuration is valid![/green]",
                title="[bold green]Validation Results[/bold green]",
                border_style="green"
            ))
        else:
            # Create validation results
            if issues:
                issues_text = "\n".join(f"• {issue}" for issue in issues)
                console.print(Panel(
                    issues_text,
                    title="[bold red]Issues Found[/bold red]",
                    border_style="red"
                ))
            
            if warnings:
                warnings_text = "\n".join(f"• {warning}" for warning in warnings)
                console.print(Panel(
                    warnings_text,
                    title="[bold yellow]Warnings[/bold yellow]",
                    border_style="yellow"
                ))
        
        return len(issues) == 0
    
    def show_config(self):
        """Show the full configuration with syntax highlighting."""
        config_yaml = yaml.dump(self.config, default_flow_style=False, sort_keys=False)
        
        syntax = Syntax(config_yaml, "yaml", theme="monokai", line_numbers=True)
        
        panel = Panel(
            syntax,
            title=f"[bold cyan]Configuration File: {self.config_path}[/bold cyan]",
            border_style="cyan"
        )
        
        console.print(panel)


# Initialize the manager
manager = TestConfigManager()


@app.command(name="list")
def list_tests(
    details: Annotated[bool, typer.Option("--details", "-d", help="Show detailed information including action paths")] = False,
):
    """List all configured tests"""
    manager.list_tests(show_details=details)


@app.command(name="add")
def add_test(
    name: Annotated[str, typer.Argument(help="Test name (unique identifier)")],
    display_name: Annotated[str, typer.Argument(help="Human-readable test name")],
    weight: Annotated[int, typer.Option("--weight", "-w", help="Test weight percentage (0-100)")] = 10,
    action_path: Annotated[str, typer.Option("--action-path", "-a", help="Path to GitHub action")] = "",
    required: Annotated[bool, typer.Option("--required", "-r", help="Mark as required test")] = False,
    category: Annotated[str, typer.Option("--category", "-c", help="Test category")] = "other",
):
    """Add a new test to the configuration"""
    if not action_path:
        action_path = f".github/actions/{name.replace('_', '-')}"
    
    manager.add_test(name, display_name, weight, action_path, required, category)


@app.command(name="update")
def update_test(
    name: Annotated[str, typer.Argument(help="Test name to update")],
    display_name: Annotated[Optional[str], typer.Option("--display-name", "-n", help="New display name")] = None,
    weight: Annotated[Optional[int], typer.Option("--weight", "-w", help="New weight percentage")] = None,
    action_path: Annotated[Optional[str], typer.Option("--action-path", "-a", help="New action path")] = None,
    required: Annotated[Optional[bool], typer.Option("--required", "-r", help="Mark as required test")] = None,
    category: Annotated[Optional[str], typer.Option("--category", "-c", help="New category")] = None,
):
    """Update an existing test"""
    manager.update_test(name, display_name, weight, action_path, required, category)


@app.command(name="remove")
def remove_test(
    name: Annotated[str, typer.Argument(help="Test name to remove")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation prompt")] = False,
):
    """Remove a test from the configuration"""
    if not force:
        if not Confirm.ask(f"[yellow]Are you sure you want to remove test '{name}'?[/yellow]"):
            console.print("[blue]Operation cancelled[/blue]")
            return
    
    manager.remove_test(name)


@app.command(name="validate")
def validate():
    """Validate the configuration for common issues"""
    is_valid = manager.validate_config()
    
    if not is_valid:
        raise typer.Exit(1)


@app.command(name="show")
def show_config():
    """Show the full configuration file with syntax highlighting"""
    manager.show_config()


@app.command(name="set-thresholds")
def set_thresholds(
    auto_merge: Annotated[Optional[int], typer.Option("--auto-merge", "-a", help="Auto-merge threshold (0-100)")] = None,
    manual_review: Annotated[Optional[int], typer.Option("--manual-review", "-m", help="Manual review threshold (0-100)")] = None,
    block: Annotated[Optional[int], typer.Option("--block", "-b", help="Block threshold (0-100)")] = None,
):
    """Set global thresholds for test scoring"""
    global_config = manager.config.get("global_config", {})
    
    if auto_merge is not None:
        global_config["auto_merge_threshold"] = auto_merge
    if manual_review is not None:
        global_config["manual_review_threshold"] = manual_review
    if block is not None:
        global_config["block_threshold"] = block
    
    manager.config["global_config"] = global_config
    manager._save_config()
    
    console.print("[green]Global thresholds updated successfully[/green]")
    
    # Show current thresholds
    threshold_table = Table(title="Updated Thresholds")
    threshold_table.add_column("Threshold", style="cyan")
    threshold_table.add_column("Value", style="green")
    
    threshold_table.add_row("Auto-merge", f"{global_config.get('auto_merge_threshold', 85)}%")
    threshold_table.add_row("Manual review", f"{global_config.get('manual_review_threshold', 65)}%")
    threshold_table.add_row("Block", f"{global_config.get('block_threshold', 64)}%")
    
    console.print(threshold_table)


if __name__ == '__main__':
    app()
