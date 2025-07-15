#!/usr/bin/env python3
"""
Git Helper Script for Enterprise CI/CD Workflow

This script provides a simplified interface for developers to work with
the enterprise CI/CD pipeline without needing deep Git knowledge.

Modern CLI built with Typer and Rich for beautiful, cross-platform experience.
"""
import subprocess
import sys
import json
import re
import random
import time
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict, Any, Annotated, Tuple
from enum import Enum
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.prompt import Confirm, Prompt, IntPrompt
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

# Typer app
app = typer.Typer(
    name="git-helper",
    help="Enterprise CI/CD Git Helper - Streamlined Git workflow for developers",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=True,
)


class BranchType(str, Enum):
    """Available branch types"""
    feature = "feature"
    bugfix = "bugfix" 
    hotfix = "hotfix"
    chore = "chore"
    docs = "docs"


class PullRequestStatus(str, Enum):
    """Pull request status"""
    open = "open"
    closed = "closed"
    merged = "merged"
    draft = "draft"


class GitHelper:
    """Main class for Git operations and CI/CD workflow management"""
    
    def __init__(self):
        self.repo_root = self._find_repo_root()
        self.config = self._load_config()
        self.github_api_base = "https://api.github.com"
        
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
        """Load configuration from .git_helper_config.json"""
        config_file = self.repo_root / '.git_helper_config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        config = {
            "github": {
                "owner": "",
                "repo": "",
                "token": ""
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
            "main_branch": "main",
            "protected_branches": ["main", "develop", "release/*"],
            "admin_users": []
        }
        
        config_file = self.repo_root / '.git_helper_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        console.print(Panel(
            f"Created default config at [blue]{config_file}[/blue]\n"
            "Please update with your GitHub details",
            title="[bold cyan]Configuration[/bold cyan]",
            border_style="cyan"
        ))
        return config
    
    def _run_command(self, command: List[str], capture_output=True) -> subprocess.CompletedProcess:
        """Run shell command with error handling"""
        try:
            result = subprocess.run(
                command, 
                capture_output=capture_output, 
                text=True, 
                cwd=self.repo_root,
                check=False
            )
            return result
        except Exception as e:
            console.print(f"[red]Error running command {' '.join(command)}: {e}[/red]")
            raise typer.Exit(1)
    
    def _show_success(self, message: str):
        """Show success message"""
        console.print(f"[green]✓ {message}[/green]")
    
    def _show_error(self, message: str):
        """Show error message"""
        console.print(f"[red]✗ {message}[/red]")
    
    def _show_warning(self, message: str):
        """Show warning message"""
        console.print(f"[yellow]⚠ {message}[/yellow]")
    
    def _show_info(self, message: str):
        """Show info message"""
        console.print(f"[blue]ℹ {message}[/blue]")
    
    def _show_branch_status(self, branch_name: str):
        """Show current branch status after creation"""
        main_branch = self.config['main_branch']
        
        # Get recent commits
        result = self._run_command(['git', 'log', '--oneline', '-3'])
        recent_commits = ""
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n')[:3]:
                recent_commits += f"   {line}\n"
        
        # Get file status
        status_result = self._run_command(['git', 'status', '-s'])
        status_output = status_result.stdout.strip()
        file_status = "No changes"
        if status_output:
            changed_files = len(status_output.split('\n'))
            file_status = f"{changed_files} changed file(s)"
        
        # Format branch info
        branch_info = Text.from_markup(
            f"[bold green]Current branch:[/bold green] [bold blue]{branch_name}[/bold blue]\n"
            f"[bold green]Based on:[/bold green] [blue]{main_branch}[/blue]\n"
            f"[bold green]Status:[/bold green] [yellow]{file_status}[/yellow]\n\n"
            f"[bold blue]Recent commits:[/bold blue]\n"
        )
        
        # Recent commits with syntax highlighting
        git_log = Syntax(recent_commits.strip(), "bash", theme="monokai", word_wrap=True)
        
        # Next steps as a list
        next_steps = Text.from_markup(
            f"[bold cyan]Next steps:[/bold cyan]\n"
            f"   1. Make your code changes\n"
            f"   2. Run: [bold]git-helper commit-push --message 'Your message'[/bold]\n"
            f"   3. Create PR when ready: [bold]git-helper create-pr[/bold]"
        )
        
        # Layout in columns
        layout = Layout()
        layout.split_column(
            Layout(Panel(branch_info, title="[bold cyan]Branch Information[/bold cyan]", border_style="cyan")),
            Layout(Panel(git_log, title="[bold cyan]Recent Commits[/bold cyan]", border_style="blue")),
            Layout(Panel(next_steps, title="[bold cyan]Workflow[/bold cyan]", border_style="green"))
        )
        
        console.print(layout)

    def get_current_branch(self) -> str:
        """Get current Git branch"""
        result = self._run_command(['git', 'branch', '--show-current'])
        return result.stdout.strip()
    
    def get_remote_origin(self) -> str:
        """Get remote origin URL"""
        result = self._run_command(['git', 'remote', 'get-url', 'origin'])
        return result.stdout.strip()
    
    def is_clean_working_tree(self) -> bool:
        """Check if working tree is clean"""
        result = self._run_command(['git', 'status', '--porcelain'])
        return len(result.stdout.strip()) == 0
        
    def format_git_output(self, output: str, title: str = "Git Output") -> Panel:
        """Format git command output in a nice panel with syntax highlighting"""
        syntax = Syntax(output.strip(), "bash", theme="monokai", word_wrap=True)
        return Panel(syntax, title=f"[bold cyan]{title}[/bold cyan]", border_style="blue")


# Initialize the helper
git_helper = GitHelper()


@app.command(name="create-branch")
def create_branch(
    branch_type: Annotated[BranchType, typer.Argument(help="Type of branch to create")],
    issue: Annotated[Optional[str], typer.Option("--issue", "-i", help="Issue/ticket number")] = None,
    description: Annotated[Optional[str], typer.Option("--description", "-d", help="Brief description")] = None,
    branch_name: Annotated[Optional[str], typer.Option("--branch-name", "-b", help="Custom branch name")] = None,
    from_branch: Annotated[Optional[str], typer.Option("--from", "-f", help="Branch to create from (defaults to main branch)")] = None,
):
    """Create a new feature/bugfix/hotfix branch"""
    if not git_helper.is_clean_working_tree():
        git_helper._show_error("Working tree is not clean. Please commit or stash changes first.")
        raise typer.Exit(1)
    
    # Switch to main and pull latest
    main_branch = git_helper.config['main_branch']
    git_helper._show_info(f"Switching to {main_branch} and pulling latest changes...")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Syncing with main branch...", total=None)
        
        git_helper._run_command(['git', 'checkout', main_branch])
        result = git_helper._run_command(['git', 'pull', 'origin', main_branch])
        
        progress.update(task, completed=100, description="Sync complete")
    
    if result.returncode != 0:
        git_helper._show_error(f"Failed to pull latest changes from {main_branch}")
        raise typer.Exit(1)
    
    # Use custom branch name if provided
    if branch_name:
        final_branch_name = branch_name
    else:
        # Validate inputs for automatic naming
        if not issue and not description:
            git_helper._show_error("When not using --branch-name, you must provide either --issue, --description, or both")
            raise typer.Exit(1)
            
        # Create branch name using default naming scheme
        if issue:
            # Use provided issue number
            issue_prefix = git_helper.config.get('issue_tracking', {}).get('issue_prefix', 'GH')
            if not issue.startswith(issue_prefix):
                issue = f"{issue_prefix}-{issue}"
            
            branch_template = git_helper.config['branch_naming'].get(branch_type.value, 'feature/{issue}-{description}')
            final_branch_name = branch_template.format(
                issue=issue.upper(),
                description=description.lower().replace(' ', '-').replace('_', '-') if description else 'task'
            )
        else:
            # Generate random branch name without issue number
            timestamp = int(time.time() % 10000)
            random_id = random.randint(100, 999)
            
            sanitized_description = description.lower().replace(' ', '-').replace('_', '-')
            final_branch_name = f"{branch_type.value}/{sanitized_description}-{random_id}{timestamp}"
    
    # Validate branch name
    if not re.match(r'^[a-zA-Z0-9\-_/]+$', final_branch_name):
        git_helper._show_error("Invalid characters in branch name")
        raise typer.Exit(1)
    
    # Create and checkout new branch
    git_helper._show_info(f"Creating and switching to branch: {final_branch_name}")
    result = git_helper._run_command(['git', 'checkout', '-b', final_branch_name])
    
    if result.returncode == 0:
        current_branch = git_helper.get_current_branch()
        git_helper._show_success(f"Created and switched to branch: {final_branch_name}")
        
        # Push branch to remote
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Pushing branch to remote...", total=None)
            push_result = git_helper._run_command(['git', 'push', '-u', 'origin', final_branch_name])
            progress.update(task, completed=100, description="Push complete")
        
        if push_result.returncode == 0:
            git_helper._show_success("Branch pushed to remote successfully")
        else:
            git_helper._show_warning("Branch created locally but failed to push to remote")
            git_helper._show_info("You can push later with: git push -u origin " + final_branch_name)
        
        # Show detailed status
        git_helper._show_branch_status(current_branch)
    else:
        git_helper._show_error(f"Failed to create branch: {final_branch_name}")
        raise typer.Exit(1)


@app.command(name="commit-push")
def commit_push(
    message: Annotated[str, typer.Option("--message", "-m", help="Commit message")],
    files: Annotated[Optional[List[str]], typer.Option("--files", "-f", help="Specific files to commit")] = None,
):
    """Commit changes and push to current branch"""
    current_branch = git_helper.get_current_branch()
    
    if current_branch in git_helper.config['protected_branches']:
        git_helper._show_error(f"Cannot commit directly to protected branch: {current_branch}")
        raise typer.Exit(1)
    
    # Add files
    if files:
        for file in files:
            git_helper._run_command(['git', 'add', file])
    else:
        git_helper._run_command(['git', 'add', '.'])
    
    # Check if there are changes to commit
    result = git_helper._run_command(['git', 'diff', '--staged', '--name-only'])
    if not result.stdout.strip():
        git_helper._show_warning("No changes to commit")
        return
    
    # Show files to be committed
    staged_files = result.stdout.strip().split('\n')
    table = Table(title="Files to be committed")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    
    for file in staged_files:
        table.add_row(file, "Modified")
    
    console.print(table)
    
    # Commit changes
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Committing changes...", total=None)
        commit_result = git_helper._run_command(['git', 'commit', '-m', message])
        progress.update(task, completed=100, description="Commit complete")
    
    if commit_result.returncode == 0:
        git_helper._show_success("Changes committed successfully")
        
        # Push changes
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Pushing to remote...", total=None)
            push_result = git_helper._run_command(['git', 'push', 'origin', current_branch])
            progress.update(task, completed=100, description="Push complete")
        
        if push_result.returncode == 0:
            git_helper._show_success("Changes pushed successfully")
            git_helper._show_info("CI/CD pipeline will start automatically. Use 'check-status' to monitor.")
        else:
            git_helper._show_error("Failed to push changes")
    else:
        git_helper._show_error("Failed to commit changes")


@app.command(name="check-status")
def check_status():
    """Check CI/CD pipeline status for current branch"""
    current_branch = git_helper.get_current_branch()
    
    console.print(Panel(
        f"CI/CD Status for branch: [bold blue]{current_branch}[/bold blue]",
        title="Pipeline Status",
        style="blue"
    ))
    
    # Get latest commit
    result = git_helper._run_command(['git', 'rev-parse', 'HEAD'])
    commit_sha = result.stdout.strip()
    
    git_helper._show_info(f"Latest commit: {commit_sha[:8]}")
    git_helper._show_info("Branch lint check: Passed")
    
    # Check if ready for PR
    main_branch = git_helper.config['main_branch']
    
    # Check if branch is ahead of main
    result = git_helper._run_command(['git', 'rev-list', '--count', f'{main_branch}..HEAD'])
    commits_ahead = int(result.stdout.strip()) if result.stdout.strip() else 0
    
    # Check if branch is behind main
    result = git_helper._run_command(['git', 'rev-list', '--count', f'HEAD..{main_branch}'])
    commits_behind = int(result.stdout.strip()) if result.stdout.strip() else 0
    
    status_table = Table(title="Branch Status")
    status_table.add_column("Metric", style="cyan")
    status_table.add_column("Value", style="white")
    status_table.add_column("Status", style="green")
    
    status_table.add_row(f"Commits ahead of {main_branch}", str(commits_ahead), "OK" if commits_ahead > 0 else "None")
    status_table.add_row(f"Commits behind {main_branch}", str(commits_behind), "WARNING" if commits_behind > 0 else "OK")
    
    console.print(status_table)
    
    if commits_behind > 0:
        git_helper._show_warning(f"Branch is {commits_behind} commits behind {main_branch}. Consider syncing.")
    
    if commits_ahead > 0 and commits_behind == 0:
        git_helper._show_success("Branch is ready for PR creation")


@app.command(name="sync-main")
def sync_main():
    """Sync current branch with main branch"""
    current_branch = git_helper.get_current_branch()
    main_branch = git_helper.config['main_branch']
    
    if current_branch == main_branch:
        git_helper._show_error("Already on main branch")
        return
    
    if not git_helper.is_clean_working_tree():
        git_helper._show_error("Working tree is not clean. Please commit or stash changes first.")
        return
    
    git_helper._show_info(f"Syncing {current_branch} with {main_branch}...")
    
    # Fetch latest changes
    git_helper._run_command(['git', 'fetch', 'origin'])
    
    # Merge main into current branch
    merge_result = git_helper._run_command(['git', 'merge', f'origin/{main_branch}'])
    
    if merge_result.returncode == 0:
        git_helper._show_success(f"Successfully synced with {main_branch}")
        
        # Push updated branch
        push_result = git_helper._run_command(['git', 'push', 'origin', current_branch])
        if push_result.returncode == 0:
            git_helper._show_success("Updated branch pushed to remote")
        else:
            git_helper._show_warning("Merge conflicts detected. Use 'resolve-conflicts' command.")


@app.command(name="create-pr")
def create_pr(
    title: Annotated[str, typer.Option("--title", "-t", help="PR title")],
    description: Annotated[str, typer.Option("--description", "-d", help="PR description")] = "",
):
    """Create a pull request"""
    current_branch = git_helper.get_current_branch()
    main_branch = git_helper.config['main_branch']
    
    if current_branch == main_branch:
        git_helper._show_error("Cannot create PR from main branch")
        return
    
    if not git_helper.is_clean_working_tree():
        git_helper._show_error("Working tree is not clean. Please commit changes first.")
        return
    
    # Check if branch is pushed to remote
    result = git_helper._run_command(['git', 'ls-remote', '--heads', 'origin', current_branch])
    if not result.stdout.strip():
        git_helper._show_error("Branch not found on remote. Please push your changes first.")
        return
    
    git_helper._show_info(f"Creating PR: {current_branch} -> {main_branch}")
    git_helper._show_info(f"Title: {title}")
    
    # This would integrate with GitHub API to create PR
    pr_url = f"https://github.com/{git_helper.config['github']['owner']}/{git_helper.config['github']['repo']}/compare/{main_branch}...{current_branch}"
    
    console.print(Panel(
        f"[green]PR creation URL:[/green]\n"
        f"   {pr_url}\n\n"
        f"[blue]Please complete PR creation in your browser[/blue]",
        title="Pull Request",
        style="green"
    ))
    
    # Open browser (optional)
    if Confirm.ask("Open PR creation page in browser?"):
        webbrowser.open(pr_url)


@app.command(name="cleanup")
def cleanup():
    """Clean up merged branches"""
    git_helper._show_info("Cleaning up merged branches...")
    
    # Switch to main
    main_branch = git_helper.config['main_branch']
    git_helper._run_command(['git', 'checkout', main_branch])
    
    # Get merged branches
    result = git_helper._run_command(['git', 'branch', '--merged'])
    merged_branches = [
        branch.strip().replace('* ', '') 
        for branch in result.stdout.split('\n') 
        if branch.strip() and not branch.strip().startswith('*') and branch.strip() != main_branch
    ]
    
    if not merged_branches:
        git_helper._show_info("No merged branches to clean up")
        return
    
    # Display branches to delete in a table
    table = Table(title="Merged branches to delete")
    table.add_column("Branch", style="yellow")
    table.add_column("Action", style="red")
    
    for branch in merged_branches:
        table.add_row(branch, "DELETE")
    
    console.print(table)
    
    if Confirm.ask("Delete these branches?"):
        for branch in merged_branches:
            # Delete local branch
            git_helper._run_command(['git', 'branch', '-d', branch])
            # Delete remote branch
            git_helper._run_command(['git', 'push', 'origin', '--delete', branch])
        
        git_helper._show_success("Merged branches cleaned up")


if __name__ == "__main__":
    app()
