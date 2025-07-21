#!/usr/bin/env python3
"""
Setup script for the pyCTH CI/CD Git Helper

This script is a cross-platform installer and configurator for the pyCTH CI/CD Git Helper tool.
It performs the following operations:
1. Validates system requirements (Python, Git, packages)
2. Auto-detects Git repository information
3. Creates configuration files for the git helper
4. Installs Git hooks for automated checks
5. Creates cross-platform shell scripts for easy access

Author: pyCTH Team
License: Intel Corporation 2025
Compatible with: Linux, macOS, Windows
"""

import os
import sys
import json
import subprocess
import re
import platform
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

# Third-party imports for CLI and formatting
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.text import Text
from rich.syntax import Syntax
from rich.box import ROUNDED


# Initialize Rich console for cross-platform output formatting
console = Console()

# Configure Typer CLI application with basic settings for maximum compatibility
app = typer.Typer(
    name="git-helper-setup",
    help="Setup script for pyCTH CI/CD Git Helper - POC Environment",
    rich_markup_mode="rich",
    no_args_is_help=False,  # Disabled to prevent empty error box
    add_completion=False,  # Disabled for better cross-platform compatibility
    context_settings={"help_option_names": ["-h", "--help"]},  # Enable -h support
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    help: bool = typer.Option(False, "--help", "-h", help="Show this message and exit."),
):
    """
    Git Helper Setup - POC Environment Configuration Tool
    
    This script configures your development environment for Git Helper tools.
    Run 'setup' command to initialize your environment.
    """
    if ctx.invoked_subcommand is None:
        if help:
            console.print(ctx.get_help())
            return
        
        # Show welcome message and guide user to main setup
        console.print("\n[bold cyan]Git Helper Setup Tool[/bold cyan]")
        console.print("[yellow]Welcome! This tool configures your Git Helper development environment.[/yellow]")
        console.print("\n[cyan]Available commands:[/cyan]")
        console.print("  • [bold]setup[/bold] - Complete environment setup (recommended)")
        console.print("  • [bold]install-hooks[/bold] - Install Git hooks only")
        console.print("  • [bold]update-config[/bold] - Update existing configuration")
        console.print("  • [bold]create-symlinks[/bold] - Create command symlinks")
        console.print("\n[green]Quick start:[/green] [bold]python setup.py setup[/bold]")
        console.print("[blue]For help:[/blue] [bold]python setup.py --help[/bold]")
        console.print()
        return


def _find_repo_root() -> Path:
    """
    Find the Git repository root directory by traversing up the directory tree.
    
    This function starts from the current working directory and moves up the
    directory hierarchy until it finds a .git folder or reaches the filesystem root.
    
    Returns:
        Path: Absolute path to the Git repository root
        
    Raises:
        Exception: If no Git repository is found in the directory hierarchy
    """
    current = Path.cwd()
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    raise Exception("Not in a Git repository")


def print_banner():
    """
    Display the welcome banner for the pyCTH CI/CD setup process.

    This function creates a visually appealing banner using Rich formatting
    that introduces users to the setup process and provides context about
    what the tool does.
    """
    banner_text = """
    [bold blue]Git Helper Environment Initializer[/bold blue]

    Welcome to the Git Helper development environment!
    
    This tool will configure your personal development environment for Git Helper.
    It works with GitHub repositories and adapts to your current setup.

    Features:
    • Auto-detects your Git configuration and GitHub repository
    • Sets up quality assurance hooks and checks  
    • Creates personalized workflow configurations
    • Enables seamless integration with Git Helper tools

    @copyright 2025 Intel Corporation
    Author: [bold green]pyCTH Team[/bold green]

    [yellow]Let's get your environment ready for development![/yellow]
    """
    
    banner = Panel(
        Text.from_markup(banner_text),
        border_style="blue",
        title="[bold cyan]Welcome[/bold cyan]",
        subtitle="[cyan]v1.0.0[/cyan]"
    )
    console.print(banner)


def check_requirements() -> bool:
    """
    Validate system requirements for the Git Helper.
    
    This function checks for:
    - Python version (3.7 or higher required)
    - Git installation and availability
    - Current directory is within a Git repository
    - Required Python packages (typer, rich)
    
    Returns:
        bool: True if all requirements are met, False otherwise
    """
    console.print("[cyan]Checking system requirements...[/cyan]")
    
    # Create a formatted table to display requirement check results
    requirements_table = Table(title="System Requirements", box=ROUNDED)
    requirements_table.add_column("Component", style="cyan")
    requirements_table.add_column("Required", style="yellow")
    requirements_table.add_column("Status", style="green")
    requirements_table.add_column("Details", style="blue")
    
    # Check Python version compatibility
    python_ok = sys.version_info >= (3, 7)
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    requirements_table.add_row(
        "Python", 
        "≥ 3.7", 
        "✓" if python_ok else "✗", 
        f"Found {python_version}"
    )
    
    # Check Git installation and version
    git_ok = False
    git_version = "Not found"
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, check=True, text=True)
        git_version = result.stdout.strip()
        git_ok = True
        requirements_table.add_row("Git", "Any version", "✓", git_version)
    except (subprocess.CalledProcessError, FileNotFoundError):
        requirements_table.add_row("Git", "Any version", "✗", "Not found")
    
    # Verify we're inside a Git repository
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
    
    # Determine overall status
    all_ok = python_ok and git_ok and repo_ok and package_ok
    
    if all_ok:
        console.print("\n[green]✓ All requirements met![/green]")
    else:
        console.print("\n[red]✗ Some requirements are not met.[/red]")
        
        # Provide helpful installation instructions
        if not package_ok:
            console.print("\n[yellow]To install missing packages:[/yellow]")
            console.print("pip install -r requirements.txt")

        if not git_ok:
            console.print("\n[yellow]To install Git:[/yellow]")
            console.print("Visit https://inner-source.intel.com/ for onboarding instructions.")

        if not python_ok:
            console.print("\n[yellow]To install Python 3.7 or later:[/yellow]")
            console.print("Visit https://www.python.org/downloads/ for installation instructions.")
        
        if not repo_ok:
            console.print("\n[yellow]Not in Git repository:[/yellow]")
            console.print("Please run this setup from within a Git repository.")

    return all_ok


def get_git_remote_info() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Auto-detect GitHub repository information from remote URL.
    
    Extracts repository details from the Git remote origin URL.
    Supports GitHub (including Intel Inner Source) with both HTTPS and SSH URL formats.
    
    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: (owner, repository_name, remote_url) or (None, None, None) if not found
        
    Examples:
        - GitHub: "https://github.com/owner/repo.git" returns ("owner", "repo", "https://github.com/owner/repo.git")
        - Intel Inner Source: "https://github.com/intel-innersource/applications.services.design-system.peacock.repo" 
          returns ("intel-innersource", "applications.services.design-system.peacock.repo", "https://...")
    """
    try:
        # Get the remote origin URL using git command
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'], 
            capture_output=True, 
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return None, None, None
            
        remote_url = result.stdout.strip()
        
        # Parse GitHub URLs (including Intel Inner Source)
        # GitHub HTTPS: https://github.com/owner/repo.git
        # Note: Intel Inner Source repos can have complex names with dots
        github_https_pattern = r'https://github\.com/([^/]+)/([^/\s]+?)(?:\.git)?/?$'
        # GitHub SSH: git@github.com:owner/repo.git
        github_ssh_pattern = r'git@github\.com:([^/]+)/([^/\s]+?)(?:\.git)?/?$'
        
        # Try to match GitHub patterns
        https_match = re.match(github_https_pattern, remote_url)
        ssh_match = re.match(github_ssh_pattern, remote_url)
        
        match = https_match or ssh_match
        if match:
            return match.group(1), match.group(2), remote_url  # owner, repo, url
            
    except Exception:
        # Silently handle any subprocess or parsing errors
        pass
        
    return None, None, None


def get_git_user_info() -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieve Git user configuration (name and email) from local Git settings.
    
    This information is typically set using:
    - git config user.name "Your Name"
    - git config user.email "your.email@example.com"
    
    This is the current user's Git identity that will be used for all Git operations
    in the pyCTH environment.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: (user_name, user_email) or (None, None) if not configured
    """
    try:
        # Get Git user name
        name_result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Get Git user email
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
        # Handle any subprocess errors gracefully
        pass
        
    return None, None


def get_current_user_context() -> Dict[str, Any]:
    """
    Gather current user Git context for environment setup.
    
    This function collects Git user information and repository context
    to properly configure the development environment.
    
    Returns:
        Dict[str, Any]: Dictionary containing user Git context information
    """
    context = {}
    
    # Get basic system information
    context['system'] = {
        'platform': platform.system()
    }
    
    # Get current working directory and repository info
    try:
        repo_root = _find_repo_root()
        context['repository'] = {
            'root_path': str(repo_root),
            'current_path': str(Path.cwd())
        }
    except Exception:
        context['repository'] = {
            'root_path': None,
            'current_path': str(Path.cwd())
        }
    
    # Get Git user information
    git_user, git_email = get_git_user_info()
    context['git_user'] = {
        'name': git_user,
        'email': git_email,
        'configured': git_user is not None and git_email is not None
    }
    
    # Get remote repository information (GitHub only)
    repo_owner, repo_name, remote_url = get_git_remote_info()
    context['remote'] = {
        'owner': repo_owner,
        'repository': repo_name,
        'url': remote_url,
        'detected': repo_owner is not None and repo_name is not None,
        'is_github': remote_url is not None and 'github.com' in remote_url
    }
    
    # Get current branch information
    try:
        branch_result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=False
        )
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
        context['git_status'] = {
            'current_branch': current_branch,
            'has_remote': remote_url is not None
        }
    except Exception:
        context['git_status'] = {
            'current_branch': None,
            'has_remote': False
        }
    
    return context


def create_config() -> Dict[str, Any]:
    """
    Create and save configuration file for the Git Helper.
    
    This function performs the following operations:
    1. Gathers current user Git context (system, git, repository info)
    2. Auto-detects GitHub repository information from git remote
    3. Auto-detects Git user information from git config
    4. Prompts user for any missing critical information
    5. Creates a user-specific configuration dictionary
    6. Displays configuration preview for user review
    7. Saves configuration to .git_helper_config.json if confirmed
    
    Returns:
        Dict[str, Any]: Configuration dictionary if successful, None if failed/cancelled
    """
    console.print("\n[cyan]Creating Git Helper configuration...[/cyan]")
    
    # Gather user Git context with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Analyzing current Git environment...[/cyan]")
        user_context = get_current_user_context()
        progress.update(task, completed=True)
    
    # Display detected information
    if user_context['git_user']['configured']:
        console.print(f"[green]✓ Detected Git user: {user_context['git_user']['name']} <{user_context['git_user']['email']}>[/green]")
    else:
        console.print("[yellow]⚠ Git user not configured - will prompt for setup[/yellow]")
        
    if user_context['remote']['detected'] and user_context['remote']['is_github']:
        console.print(f"[green]✓ Detected GitHub repository: {user_context['remote']['owner']}/{user_context['remote']['repository']}[/green]")
        console.print(f"[blue]  Remote URL: {user_context['remote']['url']}[/blue]")
    elif user_context['remote']['detected']:
        console.print(f"[yellow]⚠ Detected non-GitHub repository: {user_context['remote']['url']}[/yellow]")
        console.print("[yellow]  This tool is optimized for GitHub repositories[/yellow]")
    else:
        console.print("[yellow]⚠ Repository remote not detected - will use generic settings[/yellow]")
    
    console.print(f"[blue]✓ System: {user_context['system']['platform']}[/blue]")
    
   
    # Prompt for Git user info if not configured
    git_user = user_context['git_user']['name']
    git_email = user_context['git_user']['email']
    
    if not git_user:
        git_user = Prompt.ask("[yellow]Enter your Git username[/yellow]")
        console.print("[yellow]Setting up Git user configuration...[/yellow]")
        try:
            subprocess.run(['git', 'config', '--global', 'user.name', git_user], check=True)
            console.print(f"[green]✓ Set Git user.name to: {git_user}[/green]")
        except subprocess.CalledProcessError:
            console.print("[red]✗ Failed to set Git user.name[/red]")
    
    if not git_email:
        git_email = Prompt.ask("[yellow]Enter your Git email[/yellow]")
        try:
            subprocess.run(['git', 'config', '--global', 'user.email', git_email], check=True)
            console.print(f"[green]✓ Set Git user.email to: {git_email}[/green]")
        except subprocess.CalledProcessError:
            console.print("[red]✗ Failed to set Git user.email[/red]")
    
    # Create user-centric configuration
    config = {
        "user_profile": {
            "name": git_user,
            "email": git_email,
            "setup_date": datetime.now().isoformat(),
            "platform": user_context['system']['platform']
        },
        "repository": {
            "owner": user_context['remote']['owner'] or "unknown",
            "name": user_context['remote']['repository'] or Path.cwd().name,
            "remote_url": user_context['remote']['url'] or "not-detected",
            "root_path": user_context['repository']['root_path'],
            "current_branch": user_context['git_status']['current_branch'] or "main",
            "is_github": user_context['remote']['is_github']
        },
        "git_helper": {
            "auto_hooks": True,
            "consistency_checks": True,
            "commit_validation": True,
            "github_integration": user_context['remote']['is_github']
        },
        "workflow": {
            "default_branch": user_context['git_status']['current_branch'] or Prompt.ask("[yellow]Default branch name[/yellow]", default="main"),
            "branch_naming": {
                "feature": "feature/{issue}-{description}",
                "bugfix": "bugfix/{issue}-{description}",
                "hotfix": "hotfix/{issue}-{description}",
                "chore": "chore/{description}",
                "docs": "docs/{description}"
            }
        }
    }
    
    # Display configuration preview using Rich syntax highlighting
    config_panel = Panel(
        Syntax(json.dumps(config, indent=2), "json", theme="monokai"),
        title="[bold cyan]Git Helper Configuration[/bold cyan]",
        border_style="cyan"
    )
    
    console.print("\n[yellow]Configuration Preview:[/yellow]")
    console.print(config_panel)
    
    # Confirm and save configuration
    if Confirm.ask("[yellow]Save this Git Helper configuration?[/yellow]", default=True):
        try:
            repo_root = _find_repo_root()
            config_file = repo_root / '.git_helper_config.json'
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            console.print(f"[green]✓ Configuration saved to {config_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Error saving configuration: {e}[/red]")
            return None
    else:
        console.print("[yellow]Configuration not saved[/yellow]")
        exit(0)
        
    return config


def install_git_hooks(config: Dict[str, Any]) -> bool:
    """
    Install Git hooks for automated quality checks.
    
    This function creates and installs two Git hooks:
    1. Pre-push hook: Runs consistency checks before allowing pushes
    2. Pre-commit hook: Checks for large files before allowing commits
    
    The hooks are platform-aware and use shell scripts for maximum compatibility.
    
    Args:
        config: Configuration dictionary containing repository settings
        
    Returns:
        bool: True if hooks were installed successfully, False otherwise
    """
    console.print("\n[cyan]Setting up Git hooks...[/cyan]")
    
    try:
        repo_root = _find_repo_root()
        hooks_dir = repo_root / '.git' / 'hooks'
        
        if not hooks_dir.exists():
            console.print("[yellow]Git hooks directory not found[/yellow]")
            return False
        
        # Create pre-push hook for running consistency checks
        pre_push_hook = hooks_dir / 'pre-push'
        pre_push_content = f"""#!/bin/sh
# Git Helper pre-push hook
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
# This hook runs consistency checks before pushing to remote repository

echo "Running consistency checks..."
python "{repo_root}/devops/consistency_checker/checker.py" run-all -o consistency.html --format html

if [ $? -ne 0 ]; then
  echo "❌ Consistency checks failed. Please fix issues before pushing."
  echo "Run 'python {repo_root}/devops/consistency_checker/checker.py ' to check for report and apply waivers or repair code."
  exit 1
fi

echo "✅ Consistency checks passed."
"""
        
        with open(pre_push_hook, 'w') as f:
            f.write(pre_push_content)
        pre_push_hook.chmod(0o755)
        
        # Create pre-commit hook for file size validation
        pre_commit_hook = hooks_dir / 'pre-commit'
        pre_commit_content = f"""#!/bin/sh
# Git Helper pre-commit hook
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
# This hook runs checks on the files being committed

echo "Running pre-commit checks..."

# Check for large files (>10MB threshold)
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  against=HEAD
else
  # Initial commit: diff against an empty tree object
  against=$(git hash-object -t tree /dev/null)
fi

# Redirect output to stderr for proper Git hook behavior
exec 1>&2

# Find large files in the commit
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
        pre_commit_hook.chmod(0o755)
        
        console.print("[green]✓ Installed pre-commit and pre-push hooks[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Error installing Git hooks: {e}[/red]")
        return False


def ensure_scripts_executable() -> bool:
    """
    Ensure all Git Helper and automation scripts are executable.
    
    This function makes the necessary Python scripts executable so they can be
    run directly from the command line when added to PATH.
    
    Returns:
        bool: True if scripts were made executable successfully, False otherwise
    """
    console.print("\n[cyan]Making scripts executable...[/cyan]")
    
    try:
        repo_root = _find_repo_root()
        release_automation_dir = repo_root / 'devops' / 'release_automation'
        consistency_checker_dir = repo_root / 'devops' / 'consistency_checker'
        
        # Make Python scripts executable
        scripts = [
            release_automation_dir / 'git_helper.py',
            release_automation_dir / 'setup.py',
            consistency_checker_dir / 'checker.py'
        ]
        
        executable_count = 0
        for script in scripts:
            if script.exists():
                script.chmod(0o755)
                executable_count += 1
        
        console.print(f"[green]✓ Made {executable_count} scripts executable[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Error making scripts executable: {e}[/red]")
        return False


def create_user_symlinks() -> bool:
    """
    Create user-specific symlinks for Git Helper and automation scripts in ~/.local/bin.
    
    This function:
    1. Creates ~/.local/bin directory if it doesn't exist
    2. Creates symlinks for all executable scripts with clean command names
    3. Provides a better user experience than PATH manipulation
    4. Works across all shells and persists across sessions
    
    Returns:
        bool: True if symlinks were created successfully, False otherwise
    """
    console.print("\n[cyan]Creating user command symlinks...[/cyan]")
    
    try:
        repo_root = _find_repo_root()
        release_automation_dir = repo_root / 'devops' / 'release_automation'
        consistency_checker_dir = repo_root / 'devops' / 'consistency_checker'
        
        # Create ~/.local/bin if it doesn't exist
        local_bin = Path.home() / '.local' / 'bin'
        local_bin.mkdir(parents=True, exist_ok=True)
        
        # Define script mappings: (source_script, target_command_name)
        script_mappings = [
            (release_automation_dir / 'git_helper.py', 'git_helper'),
            (consistency_checker_dir / 'checker.py', 'consistency_checker'),
        ]
        
        created_links = []
        updated_links = []
        
        for source_script, command_name in script_mappings:
            if not source_script.exists():
                console.print(f"[yellow]⚠ Script not found: {source_script}[/yellow]")
                continue
                
            symlink_path = local_bin / command_name
            
            # Remove existing symlink if it exists
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()
                updated_links.append(command_name)
            
            # Create new symlink
            symlink_path.symlink_to(source_script)
            created_links.append(command_name)
        
        # Report results
        if created_links:
            console.print(f"[green]✓ Created symlinks: {', '.join(created_links)}[/green]")
        
        if updated_links:
            console.print(f"[blue]✓ Updated existing symlinks: {', '.join(updated_links)}[/blue]")
        
        # Verify ~/.local/bin is in PATH
        local_bin_str = str(local_bin)
        current_path = os.environ.get('PATH', '')
        
        if local_bin_str not in current_path:
            console.print(f"[yellow]⚠ {local_bin} not in PATH[/yellow]")
            console.print("[yellow]Add this to your shell config for automatic command discovery:[/yellow]")
            
            # Detect user's shell for instructions
            shell = os.environ.get('SHELL', '/bin/sh')
            shell_name = Path(shell).name
            
            if shell_name in ['tcsh', 'csh']:
                console.print(f"[dim]setenv PATH \"{local_bin}:$PATH\"[/dim]")
            else:
                console.print(f"[dim]export PATH=\"{local_bin}:$PATH\"[/dim]")
        else:
            console.print(f"[green]✓ {local_bin} already in PATH[/green]")
        
        console.print(f"\n[cyan]Available commands:[/cyan]")
        for command_name in created_links:
            console.print(f"  • [bold green]{command_name}[/bold green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Error creating symlinks: {e}[/red]")
        return False


@app.command(name="setup")
def setup():
    """
    Run the complete Git Helper environment setup process for the current user.
    
    This command initializes the Git Helper environment for any user entering
    the development environment. It:
    1. Displays welcome banner
    2. Checks system requirements
    3. Gathers user Git context and configures Git if needed
    4. Creates user-specific Git Helper configuration
    5. Installs Git hooks for automated quality checks
    6. Creates shell script wrapper for easy access
    7. Provides setup summary and next steps
    
    This setup is designed to work with GitHub repositories and will adapt
    to the user's current environment and repository structure.
    """
    print_banner()
    
    # Define setup steps with their corresponding functions
    steps = [
        ("Check Requirements", check_requirements),
        ("Create Configuration", create_config),
        ("Install Git Hooks", install_git_hooks),
        ("Make Scripts Executable", ensure_scripts_executable),
        ("Create User Symlinks", create_user_symlinks)
    ]
    
    step_results = {}
    config = None
    
    # Execute each setup step sequentially
    for i, (step_name, step_func) in enumerate(steps, 1):
        console.print(f"\n[bold cyan]Step {i}/{len(steps)}: {step_name}[/bold cyan]")
        
        # Special handling for Git hooks installation (requires config)
        if step_name == "Install Git Hooks" and config is None:
            console.print("[yellow]Skipping Git hooks installation (no configuration)[/yellow]")
            step_results[step_name] = False
            continue
            
        # Execute the step function with appropriate parameters
        if step_name == "Create Configuration":
            config = step_func()
            step_results[step_name] = config is not None
        elif step_name == "Install Git Hooks":
            step_results[step_name] = step_func(config)
        else:
            step_results[step_name] = step_func()
        
        # Allow user to continue if step fails
        if not step_results[step_name]:
            if Confirm.ask(f"[yellow]Step '{step_name}' failed. Continue anyway?[/yellow]", default=True):
                continue
            else:
                console.print("[red]Setup aborted[/red]")
                return
    
    # Display setup summary table
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
    
    # Provide final status and instructions
    if all(step_results.values()):
        console.print("\n[green]✓ Setup completed successfully![/green]")
    else:
        console.print("\n[yellow]⚠ Setup completed with some steps skipped or failed[/yellow]")
    
    # Display next steps for the user
    console.print("""
[bold cyan]Setup Complete![/bold cyan]

[green]✓ Git Helper configured for this repository[/green]
[green]✓ User command symlinks created in ~/.local/bin[/green]
[green]✓ Git hooks installed (pre-commit, pre-push)[/green]
[green]✓ Available commands: git_helper, consistency_checker[/green]

[yellow]Quick Start:[/yellow]
• Run: [bold]git_helper --help[/bold]
• Check code: [bold]consistency_checker --help[/bold]
• Config: [bold].git_helper_config.json[/bold] for settings
• Note: Commands available from any directory (via ~/.local/bin symlinks)
    """)


@app.command(name="install-hooks")
def install_hooks():
    """
    Install Git hooks only (without running full setup).
    
    This command allows users to install or reinstall Git hooks without
    going through the complete setup process. It will use existing
    configuration if available, or prompt to create one if needed.
    """
    print_banner()
    
    # Check system requirements first
    if not check_requirements():
        if not Confirm.ask("[yellow]Some requirements are not met. Continue anyway?[/yellow]", default=False):
            return
    
    try:
        repo_root = _find_repo_root()
        config_file = repo_root / '.git_helper_config.json'
        
        # Load existing configuration or create new one
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            console.print("[green]✓ Found existing Git Helper configuration[/green]")
        else:
            console.print("[yellow]No Git Helper configuration found. Creating user environment setup.[/yellow]")
            config = create_config()
            
            if not config:
                console.print("[red]Failed to create Git Helper configuration[/red]")
                return
        
        # Install the Git hooks
        if install_git_hooks(config):
            console.print("[green]✓ Git hooks installed successfully[/green]")
        else:
            console.print("[red]✗ Failed to install Git hooks[/red]")
            
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


@app.command(name="update-config")
def update_config():
    """
    Update existing configuration file.
    
    This command allows users to modify their existing Git Helper configuration
    without running the complete setup process. It will display the current
    configuration and prompt for updates.
    """
    print_banner()
    
    try:
        repo_root = _find_repo_root()
        config_file = repo_root / '.git_helper_config.json'
        
        # Check if configuration file exists
        if config_file.exists():
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
                
            console.print("[green]✓ Found existing Git Helper configuration[/green]")
            
            # Display current configuration for review
            console.print("\n[yellow]Current Git Helper Configuration:[/yellow]")
            console.print(Panel(
                Syntax(json.dumps(existing_config, indent=2), "json", theme="monokai"),
                title="Current Git Helper Configuration",
                border_style="blue"
            ))
            
            # Prompt user to update configuration
            if Confirm.ask("[yellow]Update this Git Helper configuration?[/yellow]", default=True):
                new_config = create_config()
                
                if new_config:
                    console.print("[green]✓ Git Helper configuration updated[/green]")
            else:
                console.print("[yellow]Git Helper configuration update cancelled[/yellow]")
        else:
            console.print("[yellow]No existing Git Helper configuration found[/yellow]")
            
            # Offer to create new configuration if none exists
            if Confirm.ask("[yellow]Create new Git Helper environment configuration?[/yellow]", default=True):
                if create_config():
                    console.print("[green]✓ Git Helper configuration created[/green]")
            else:
                console.print("[yellow]Git Helper configuration creation cancelled[/yellow]")
                
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


@app.command(name="create-symlinks")
def create_symlinks():
    """
    Create user symlinks for Git Helper and release automation scripts in ~/.local/bin.
    
    This command creates symlinks in ~/.local/bin with underscore naming for easy 
    command access without needing to modify PATH or remember full script paths.
    Creates: git_helper, consistency_checker
    """
    # Skip banner for this simple command
    console.print("[cyan]Git Helper Symlink Creation[/cyan]")
    
    # Quick requirements check
    try:
        _find_repo_root()
    except Exception:
        console.print("[red]✗ Not in a Git repository[/red]")
        return
    
    # Run symlink creation
    if create_user_symlinks():
        console.print("[green]✓ Symlinks created successfully[/green]")
    else:
        console.print("[red]✗ Failed to create symlinks[/red]")


# Entry point for script execution
if __name__ == '__main__':
    app()
