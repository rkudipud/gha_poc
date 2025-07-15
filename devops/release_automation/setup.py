#!/usr/bin/env python3
"""
Setup script for the Enterprise CI/CD Git Helper

This script installs and configures the git_helper tool for developers.
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from typing import Annotated, Tuple, Optional, Dict, Any, List
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.text import Text
from rich.tree import Tree
from rich.syntax import Syntax
from rich.style import Style
from rich.markdown import Markdown
from rich.layout import Layout
from rich.columns import Columns
from rich.box import Box, ROUNDED, HEAVY, SIMPLE
from rich import print as rprint


# Initialize Rich console
console = Console()

# Typer app with styling
app = typer.Typer(
    name="git-helper-setup",
    help="Setup script for Enterprise CI/CD Git Helper",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=True,
)


def _find_repo_root() -> Path:
    """Find the Git repository root"""
    current = Path.cwd()
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    raise Exception("Not in a Git repository")


def print_banner():
    """Print setup banner"""
    banner_text = """
    [bold blue]Enterprise CI/CD Git Helper Setup[/bold blue]
    
    This tool will guide you through the setup process for the Enterprise CI/CD Git Helper.
    The Git Helper simplifies common Git workflows and enforces best practices.
    
    [yellow]Please follow the prompts to complete the setup.[/yellow]
    """
    
    banner = Panel(
        Text.from_markup(banner_text),
        border_style="blue",
        title="[bold cyan]Welcome[/bold cyan]",
        subtitle="[cyan]v1.0.0[/cyan]"
    )
    console.print(banner)


def check_requirements() -> bool:
    """Check system requirements"""
    console.print("[cyan]Checking system requirements...[/cyan]")
    
    requirements_table = Table(title="System Requirements", box=ROUNDED)
    requirements_table.add_column("Component", style="cyan")
    requirements_table.add_column("Required", style="yellow")
    requirements_table.add_column("Status", style="green")
    requirements_table.add_column("Details", style="blue")
    
    # Check Python version
    python_ok = sys.version_info >= (3, 7)
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    requirements_table.add_row(
        "Python", 
        "≥ 3.7", 
        "✓" if python_ok else "✗", 
        f"Found {python_version}"
    )
    
    # Check Git
    git_ok = False
    git_version = "Not found"
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, check=True, text=True)
        git_version = result.stdout.strip()
        git_ok = True
        requirements_table.add_row("Git", "Any version", "✓", git_version)
    except (subprocess.CalledProcessError, FileNotFoundError):
        requirements_table.add_row("Git", "Any version", "✗", "Not found")
    
    # Check if in git repository
    repo_ok = False
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True, check=True)
        requirements_table.add_row("Git Repository", "Required", "✓", "Repository found")
        repo_ok = True
    except subprocess.CalledProcessError:
        requirements_table.add_row("Git Repository", "Required", "✗", "Not in a Git repository")
    
    # Check for required Python packages
    packages = [
        ("typer", "≥ 0.9.0"),
        ("rich", "≥ 13.0.0"),
    ]
    
    package_ok = True
    for package, version in packages:
        try:
            module = __import__(package)
            ver = getattr(module, "__version__", "unknown")
            requirements_table.add_row(f"Package: {package}", version, "✓", f"Found {ver}")
        except ImportError:
            requirements_table.add_row(f"Package: {package}", version, "✗", "Not installed")
            package_ok = False
    
    console.print(requirements_table)
    
    all_ok = python_ok and git_ok and repo_ok and package_ok
    
    if all_ok:
        console.print("\n[green]✓ All requirements met![/green]")
    else:
        console.print("\n[red]✗ Some requirements are not met.[/red]")
        
        # Provide installation help
        if not package_ok:
            console.print("\n[yellow]To install missing packages:[/yellow]")
            console.print("pip install -r requirements.txt")
    
    return all_ok


def get_git_remote_info() -> Tuple[Optional[str], Optional[str]]:
    """Auto-detect GitHub repository information from remote URL"""
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'], 
            capture_output=True, 
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return None, None
            
        remote_url = result.stdout.strip()
        
        # Parse GitHub URL format (HTTPS or SSH)
        github_https_pattern = r'https://github\.com/([^/]+)/([^/.]+)(?:\.git)?'
        github_ssh_pattern = r'git@github\.com:([^/]+)/([^/.]+)(?:\.git)?'
        
        https_match = re.match(github_https_pattern, remote_url)
        ssh_match = re.match(github_ssh_pattern, remote_url)
        
        match = https_match or ssh_match
        if match:
            return match.group(1), match.group(2)
            
    except Exception:
        pass
        
    return None, None


def get_git_user_info() -> Tuple[Optional[str], Optional[str]]:
    """Get Git user name and email"""
    try:
        name_result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            check=False
        )
        
        email_result = subprocess.run(
            ['git', 'config', 'user.email'],
            capture_output=True,
            text=True,
            check=False
        )
        
        user_name = name_result.stdout.strip() if name_result.returncode == 0 else None
        user_email = email_result.stdout.strip() if email_result.returncode == 0 else None
        
        return user_name, user_email
        
    except Exception:
        pass
        
    return None, None


def create_config() -> Dict[str, Any]:
    """Create configuration file"""
    console.print("\n[cyan]Creating configuration file...[/cyan]")
    
    # Auto-detect GitHub info
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Auto-detecting repository information...[/cyan]")
        auto_owner, auto_repo = get_git_remote_info()
        git_user, git_email = get_git_user_info()
        progress.update(task, completed=True)
    
    if auto_owner and auto_repo:
        console.print(f"[green]✓ Detected GitHub repository: {auto_owner}/{auto_repo}[/green]")
    if git_user:
        console.print(f"[green]✓ Detected Git user: {git_user} <{git_email}>[/green]")
    
    # Create configuration with auto-detected values or prompt for input
    config = {
        "github": {
            "owner": auto_owner or Prompt.ask("[yellow]GitHub repository owner[/yellow]"),
            "repo": auto_repo or Prompt.ask("[yellow]GitHub repository name[/yellow]"),
            "token": "YOUR_GITHUB_TOKEN"  # This should be set by the user manually for security
        },
        "issue_tracking": {
            "use_github_issues": True,
            "issue_prefix": "GH"
        },
        "branch_naming": {
            "feature": "feature/{issue}-{description}",
            "bugfix": "bugfix/{issue}-{description}",
            "hotfix": "hotfix/{issue}-{description}",
            "chore": "chore/{description}",
            "docs": "docs/{description}"
        },
        "main_branch": Prompt.ask("[yellow]Main branch name[/yellow]", default="main"),
        "protected_branches": ["main", "develop", "release/*"],
        "admin_users": [git_user] if git_user else []
    }
    
    # Show configuration preview
    config_panel = Panel(
        Syntax(json.dumps(config, indent=2), "json", theme="monokai"),
        title="[bold cyan]Configuration Preview[/bold cyan]",
        border_style="cyan"
    )
    
    console.print("\n[yellow]Configuration Preview:[/yellow]")
    console.print(config_panel)
    
    # Confirm and save
    if Confirm.ask("[yellow]Save this configuration?[/yellow]", default=True):
        try:
            repo_root = _find_repo_root()
            config_file = repo_root / '.git_helper_config.json'
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            console.print(f"[green]✓ Configuration saved to {config_file}[/green]")
            console.print("[yellow]Note: Update the GitHub token manually for security[/yellow]")
            
        except Exception as e:
            console.print(f"[red]✗ Error saving configuration: {e}[/red]")
            return None
    else:
        console.print("[yellow]Configuration not saved[/yellow]")
        
    return config


def install_git_hooks(config: Dict[str, Any]) -> bool:
    """Install Git hooks"""
    console.print("\n[cyan]Setting up Git hooks...[/cyan]")
    
    try:
        repo_root = _find_repo_root()
        hooks_dir = repo_root / '.git' / 'hooks'
        
        if not hooks_dir.exists():
            console.print("[yellow]Git hooks directory not found[/yellow]")
            return False
        
        # Pre-push hook to run consistency checks
        pre_push_hook = hooks_dir / 'pre-push'
        
        pre_push_content = f"""#!/bin/sh
# Git Helper pre-push hook
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
# This hook runs consistency checks before pushing to remote

echo "Running consistency checks..."
python {repo_root}/devops/consistency_checker/checker.py run-all

if [ $? -ne 0 ]; then
  echo "❌ Consistency checks failed. Please fix issues before pushing."
  echo "Run 'python {repo_root}/devops/consistency_checker/checker.py run-all --fix' to attempt automatic fixes."
  exit 1
fi

echo "✅ Consistency checks passed."
"""
        
        with open(pre_push_hook, 'w') as f:
            f.write(pre_push_content)
        
        # Make hook executable
        pre_push_hook.chmod(0o755)
        
        console.print(f"[green]✓ Installed pre-push hook at {pre_push_hook}[/green]")
        
        # Create pre-commit hook
        pre_commit_hook = hooks_dir / 'pre-commit'
        
        pre_commit_content = f"""#!/bin/sh
# Git Helper pre-commit hook
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
# This hook runs checks on the files being committed

echo "Running pre-commit checks..."

# Check for large files
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  against=HEAD
else
  against=$(git hash-object -t tree /dev/null)
fi

# Redirect output to stderr
exec 1>&2

# Check if any large files are being committed
large_files=$(git diff --cached --name-only --diff-filter=A $against | xargs -I{{}} sh -c 'if [ $(git ls-files --stage {{}} | cut -f2 | xargs -I% git cat-file -s %) -gt 10485760 ]; then echo "{{}}"; fi')

if [ -n "$large_files" ]; then
  echo "❌ Error: Attempting to commit large files (>10MB):"
  echo "$large_files"
  echo "Please remove these files and use Git LFS or alternative storage."
  exit 1
fi

echo "✅ Pre-commit checks passed."
"""
        
        with open(pre_commit_hook, 'w') as f:
            f.write(pre_commit_content)
        
        # Make hook executable
        pre_commit_hook.chmod(0o755)
        
        console.print(f"[green]✓ Installed pre-commit hook at {pre_commit_hook}[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Error installing Git hooks: {e}[/red]")
        return False


def create_shell_script() -> bool:
    """Create shell script to activate the tool"""
    console.print("\n[cyan]Creating shell script...[/cyan]")
    
    try:
        repo_root = _find_repo_root()
        bin_dir = repo_root / 'bin'
        
        # Create bin directory if it doesn't exist
        if not bin_dir.exists():
            bin_dir.mkdir()
            console.print(f"[green]✓ Created bin directory at {bin_dir}[/green]")
        
        # Create git-helper script
        script_path = bin_dir / 'git-helper'
        
        script_content = f"""#!/bin/sh
# Git Helper wrapper script
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

REPO_ROOT="{repo_root}"
HELPER_SCRIPT="$REPO_ROOT/devops/release_automation/git_helper.py"

# Activate virtual environment if it exists
if [ -f "$REPO_ROOT/venv/bin/activate" ]; then
  . "$REPO_ROOT/venv/bin/activate"
fi

# Run the git helper
python "$HELPER_SCRIPT" "$@"
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        script_path.chmod(0o755)
        
        console.print(f"[green]✓ Created git-helper script at {script_path}[/green]")
        console.print(f"[yellow]Add {bin_dir} to your PATH to use the git-helper command globally[/yellow]")
        
        # Show instructions for adding to PATH
        path_instructions = f"""
[bold cyan]To add git-helper to your PATH:[/bold cyan]

For bash/zsh users, add to ~/.bashrc or ~/.zshrc:
[dim]export PATH="{bin_dir}:$PATH"[/dim]

For tcsh users, add to ~/.tcshrc or ~/.cshrc:
[dim]setenv PATH {bin_dir}:$PATH[/dim]

Then reload your shell configuration or restart your terminal.
        """
        
        console.print(Panel(path_instructions, title="Path Configuration", border_style="blue"))
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Error creating shell script: {e}[/red]")
        return False


@app.command(name="setup")
def setup():
    """Run the complete setup process"""
    print_banner()
    
    steps = [
        ("Check Requirements", check_requirements),
        ("Create Configuration", create_config),
        ("Install Git Hooks", install_git_hooks),
        ("Create Shell Script", create_shell_script)
    ]
    
    step_results = {}
    config = None
    
    for i, (step_name, step_func) in enumerate(steps, 1):
        console.print(f"\n[bold cyan]Step {i}/{len(steps)}: {step_name}[/bold cyan]")
        
        if step_name == "Install Git Hooks" and config is None:
            # Skip Git hooks if no config
            console.print("[yellow]Skipping Git hooks installation (no configuration)[/yellow]")
            step_results[step_name] = False
            continue
            
        if step_name == "Create Configuration":
            config = step_func()
            step_results[step_name] = config is not None
        else:
            if step_name == "Install Git Hooks":
                result = step_func(config)
            else:
                result = step_func()
            step_results[step_name] = result
        
        if not step_results[step_name]:
            if Confirm.ask(f"[yellow]Step '{step_name}' failed. Continue anyway?[/yellow]", default=True):
                continue
            else:
                console.print("[red]Setup aborted[/red]")
                return
    
    # Summary
    console.print("\n[bold cyan]Setup Summary[/bold cyan]")
    
    summary_table = Table(title="Setup Results")
    summary_table.add_column("Step", style="cyan")
    summary_table.add_column("Status", style="green")
    
    for step_name, result in step_results.items():
        summary_table.add_row(
            step_name,
            "[green]✓ Success[/green]" if result else "[yellow]⚠ Skipped/Failed[/yellow]"
        )
    
    console.print(summary_table)
    
    # Final instructions
    if all(step_results.values()):
        console.print("\n[green]✓ Setup completed successfully![/green]")
    else:
        console.print("\n[yellow]⚠ Setup completed with some steps skipped or failed[/yellow]")
    
    console.print("""
[bold cyan]Next Steps:[/bold cyan]

1. Run [bold]git-helper --help[/bold] to see available commands
2. Use [bold]git-helper create-branch[/bold] to create your first branch
3. Review the documentation in the devops/docs directory
    """)


@app.command(name="install-hooks")
def install_hooks():
    """Install Git hooks only"""
    print_banner()
    
    if not check_requirements():
        if not Confirm.ask("[yellow]Some requirements are not met. Continue anyway?[/yellow]", default=False):
            return
    
    try:
        repo_root = _find_repo_root()
        config_file = repo_root / '.git_helper_config.json'
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            console.print("[yellow]No configuration found. Creating default configuration.[/yellow]")
            config = create_config()
            
            if not config:
                console.print("[red]Failed to create configuration[/red]")
                return
        
        if install_git_hooks(config):
            console.print("[green]✓ Git hooks installed successfully[/green]")
        else:
            console.print("[red]✗ Failed to install Git hooks[/red]")
            
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


@app.command(name="update-config")
def update_config():
    """Update existing configuration"""
    print_banner()
    
    try:
        repo_root = _find_repo_root()
        config_file = repo_root / '.git_helper_config.json'
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
                
            console.print("[green]✓ Found existing configuration[/green]")
            
            # Show current config
            console.print("\n[yellow]Current Configuration:[/yellow]")
            console.print(Panel(
                Syntax(json.dumps(existing_config, indent=2), "json", theme="monokai"),
                title="Current Configuration",
                border_style="blue"
            ))
            
            if Confirm.ask("[yellow]Update this configuration?[/yellow]", default=True):
                new_config = create_config()
                
                if new_config:
                    console.print("[green]✓ Configuration updated[/green]")
            else:
                console.print("[yellow]Configuration update cancelled[/yellow]")
        else:
            console.print("[yellow]No existing configuration found[/yellow]")
            
            if Confirm.ask("[yellow]Create new configuration?[/yellow]", default=True):
                if create_config():
                    console.print("[green]✓ Configuration created[/green]")
            else:
                console.print("[yellow]Configuration creation cancelled[/yellow]")
                
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


if __name__ == '__main__':
    app()
