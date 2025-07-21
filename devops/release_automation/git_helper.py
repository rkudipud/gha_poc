#!/usr/bin/env python3
"""
Git Helper Script for pyCTH CI/CD Workflow

This script provides a simplified interface for developers to work with
Git repositories in an pyCTH CI/CD environment. It automates common
Git operations like branch creation, commits, pulls requests, and cleanup.

Features:
- Automated branch naming with issue tracking
- Safe commit and push operations
- Pull request creation
- Branch synchronization with main
- Cleanup of merged branches

Author: pyCTH Team
License: Intel Corporation 2025
Compatible with: GitHub repositories
"""

import subprocess
import sys
import json
import re
import random
import time
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict, Any, Annotated
from enum import Enum
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Confirm, Prompt


# Initialize Rich console for consistent output formatting
console = Console()

# Configure Typer CLI application with -h support
app = typer.Typer(
    name="git-helper",
    help="pyCTH CI/CD Git Helper - Streamlined Git workflow for developers",
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
    Git Helper - pyCTH CI/CD Tool
    
    This tool streamlines Git workflows for pyCTH development.
    """
    if ctx.invoked_subcommand is None:
        console.print("[bold blue]Git Helper - pyCTH CI/CD Tool[/bold blue]")
        console.print("Welcome! This tool streamlines Git workflows for pyCTH development.")
        console.print("\n[cyan]Available commands:[/cyan]")
        console.print("  • [bold]create-branch[/bold] - Create feature/bugfix/hotfix branches")
        console.print("  • [bold]commit-push[/bold] - Commit and push changes safely")
        console.print("  • [bold]check-status[/bold] - Check CI/CD pipeline status")
        console.print("  • [bold]sync-main[/bold] - Synchronize with main branch")
        console.print("  • [bold]create-pr[/bold] - Create pull request")
        console.print("  • [bold]cleanup[/bold] - Clean up merged branches")
        console.print("\n[green]Quick start:[/green] git_helper create-branch feature --issue 123 --description 'new feature'")
        console.print("[blue]For help:[/blue] git_helper --help")
        return


class BranchType(str, Enum):
    """
    Available branch types for consistent naming conventions.
    
    These types align with common Git workflow patterns:
    - feature: New functionality development
    - bugfix: Bug fixes and corrections
    - hotfix: Critical production fixes
    - chore: Maintenance tasks, refactoring
    - docs: Documentation updates
    """
    feature = "feature"
    bugfix = "bugfix" 
    hotfix = "hotfix"
    chore = "chore"
    docs = "docs"


class GitHelper:
    """
    Main class for Git operations and CI/CD workflow management.
    
    This class provides a simplified interface for common Git operations
    in an pyCTH environment, including branch management, commits,
    and pull request creation.
    """
    
    def __init__(self):
        """Initialize GitHelper with repository configuration."""
        self.repo_root = self._find_repo_root()
        self.config = self._load_config()
        self.github_api_base = "https://api.github.com"
        
    def _find_repo_root(self) -> Path:
        """
        Find the Git repository root directory by traversing up the directory tree.
        
        Returns:
            Path: Absolute path to the Git repository root
            
        Raises:
            typer.Exit: If no Git repository is found in the directory hierarchy
        """
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        console.print("[red]✗ Error: Not in a Git repository[/red]")
        raise typer.Exit(1)
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from .git_helper_config.json file.
        
        If no configuration file exists, creates a default one with
        standard settings for GitHub integration. Handles both old
        and new configuration formats for compatibility.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        config_file = self.repo_root / '.git_helper_config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            # Handle different configuration formats for compatibility
            if 'main_branch' not in config:
                # Try to get main branch from workflow.default_branch (setup.py format)
                if 'workflow' in config and 'default_branch' in config['workflow']:
                    config['main_branch'] = config['workflow']['default_branch']
                else:
                    # Default to 'main' if not specified
                    config['main_branch'] = 'main'
            
            # Ensure protected_branches exists
            if 'protected_branches' not in config:
                config['protected_branches'] = [config['main_branch'], 'develop', 'release/*']
            
            # Ensure branch_naming exists
            if 'branch_naming' not in config:
                if 'workflow' in config and 'branch_naming' in config['workflow']:
                    config['branch_naming'] = config['workflow']['branch_naming']
                else:
                    config['branch_naming'] = {
                        "feature": "feature/{issue}-{description}",
                        "bugfix": "bugfix/{issue}-{description}",
                        "hotfix": "hotfix/{issue}-{description}",
                        "chore": "chore/{description}",
                        "docs": "docs/{description}"
                    }
            
            return config
        return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create default configuration file with standard GitHub settings.
        
        This configuration includes:
        - GitHub repository settings
        - Branch naming conventions
        - Protected branch definitions
        - Issue tracking preferences
        
        Returns:
            Dict[str, Any]: Default configuration dictionary
        """
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
        
        # Save configuration to file
        config_file = self.repo_root / '.git_helper_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        console.print(f"[yellow]✓ Created default config at {config_file}[/yellow]")
        console.print("[yellow]Please update with your GitHub repository details[/yellow]")
        return config
    
    def _run_command(self, command: List[str], capture_output=True) -> subprocess.CompletedProcess:
        """
        Execute shell command with proper error handling and working directory.
        
        Args:
            command: List of command components (e.g., ['git', 'status'])
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            subprocess.CompletedProcess: Command execution result
            
        Raises:
            typer.Exit: If command execution fails
        """
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
            console.print(f"[red]✗ Error running command {' '.join(command)}: {e}[/red]")
            raise typer.Exit(1)
    
    def _show_success(self, message: str):
        """Display success message with consistent formatting."""
        console.print(f"[green]✓ {message}[/green]")
    
    def _show_error(self, message: str):
        """Display error message with consistent formatting."""
        console.print(f"[red]✗ {message}[/red]")
    
    def _show_warning(self, message: str):
        """Display warning message with consistent formatting."""
        console.print(f"[yellow]⚠ {message}[/yellow]")
    
    def _show_info(self, message: str):
        """Display informational message with consistent formatting."""
        console.print(f"[blue]ℹ {message}[/blue]")
    
    def _is_protected_branch(self, branch_name: str) -> bool:
        """
        Check if a branch is protected and should not be deleted.
        
        Args:
            branch_name: Name of the branch to check
            
        Returns:
            bool: True if the branch is protected, False otherwise
        """
        if not branch_name:
            return True  # Treat empty/None as protected for safety
            
        protected_branches = self.config.get('protected_branches', [self.config['main_branch'], 'develop', 'release/*'])
        
        for protected in protected_branches:
            if protected.endswith('*'):
                # Pattern matching for branches like 'release/*'
                pattern = protected[:-1]  # Remove the '*'
                if branch_name.startswith(pattern):
                    return True
            elif branch_name == protected:
                # Exact match
                return True
        
        # Always protect main branch as an additional safety measure
        if branch_name == self.config['main_branch']:
            return True
            
        return False
    
    def _show_branch_status(self, branch_name: str):
        """
        Display current branch status after creation with simplified output.
        
        Args:
            branch_name: Name of the current branch
        """
        main_branch = self.config['main_branch']
        
        # Get recent commits (simplified)
        result = self._run_command(['git', 'log', '--oneline', '-2'])
        if result.returncode == 0 and result.stdout.strip():
            recent_commits = result.stdout.strip().split('\n')
            console.print(f"\n[cyan]Recent commits:[/cyan]")
            for commit in recent_commits[:2]:
                console.print(f"  {commit}")
        
        # Show next steps
        console.print(f"\n[cyan]Next steps:[/cyan]")
        console.print(f"  1. Make your code changes")
        console.print(f"  2. Run: [bold]git_helper commit-push --message 'Your message'[/bold]")
        console.print(f"  3. Create PR: [bold]git_helper create-pr --title 'Your PR title'[/bold]")

    def get_current_branch(self) -> str:
        """
        Get the name of the current Git branch.
        
        Returns:
            str: Current branch name
        """
        result = self._run_command(['git', 'branch', '--show-current'])
        return result.stdout.strip()
    
    def get_remote_origin(self) -> str:
        """
        Get the remote origin URL for the repository.
        
        Returns:
            str: Remote origin URL
        """
        result = self._run_command(['git', 'remote', 'get-url', 'origin'])
        return result.stdout.strip()
    
    def is_clean_working_tree(self) -> bool:
        """
        Check if the working tree has no uncommitted changes.
        
        Returns:
            bool: True if working tree is clean, False otherwise
        """
        result = self._run_command(['git', 'status', '--porcelain'])
        return len(result.stdout.strip()) == 0


# Initialize the GitHelper instance for use in commands
git_helper = GitHelper()


@app.command(name="create-branch")
def create_branch(
    branch_type: Annotated[BranchType, typer.Argument(help="Type of branch to create")],
    issue: Annotated[Optional[str], typer.Option("--issue", "-i", help="Issue/ticket number")] = None,
    description: Annotated[Optional[str], typer.Option("--description", "-d", help="Brief description")] = None,
    branch_name: Annotated[Optional[str], typer.Option("--branch-name", "-b", help="Custom branch name")] = None,
    from_branch: Annotated[Optional[str], typer.Option("--from", "-f", help="Branch to create from (defaults to main branch)")] = None,
):
    """
    Create a new feature/bugfix/hotfix branch with automated naming.
    
    This command:
    1. Ensures working tree is clean
    2. Switches to main branch and pulls latest changes
    3. Creates new branch with appropriate naming convention
    4. Pushes branch to remote repository
    5. Displays next steps for development workflow
    
    Examples:
        git_helper create-branch feature --issue 123 --description "user authentication"
        git_helper create-branch bugfix --description "fix login issue"
        git_helper create-branch hotfix --branch-name "critical-security-fix"
    """
    # Step 1: Validate working tree state
    if not git_helper.is_clean_working_tree():
        git_helper._show_error("Working tree is not clean. Please commit or stash changes first.")
        raise typer.Exit(1)
    
    # Step 2: Switch to main branch and sync with remote
    main_branch = git_helper.config['main_branch']
    git_helper._show_info(f"Switching to {main_branch} and pulling latest changes...")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Syncing with main branch...", total=None)
        
        # Switch to main branch
        git_helper._run_command(['git', 'checkout', main_branch])
        
        # Pull latest changes from remote
        result = git_helper._run_command(['git', 'pull', 'origin', main_branch])
        
        progress.update(task, completed=100, description="Sync complete")
    
    if result.returncode != 0:
        git_helper._show_error(f"Failed to pull latest changes from {main_branch}")
        raise typer.Exit(1)
    
    # Step 3: Generate branch name using naming conventions
    if branch_name:
        # Use custom branch name if provided
        final_branch_name = branch_name
    else:
        # Validate inputs for automatic naming
        if not issue and not description:
            git_helper._show_error("When not using --branch-name, you must provide either --issue, --description, or both")
            raise typer.Exit(1)
            
        # Create branch name using configured naming scheme
        if issue:
            # Format issue number with prefix if needed
            issue_prefix = git_helper.config.get('issue_tracking', {}).get('issue_prefix', 'GH')
            if not issue.startswith(issue_prefix):
                issue = f"{issue_prefix}-{issue}"
            
            # Use template from configuration
            branch_template = git_helper.config['branch_naming'].get(branch_type.value, 'feature/{issue}-{description}')
            final_branch_name = branch_template.format(
                issue=issue.upper(),
                description=description.lower().replace(' ', '-').replace('_', '-') if description else 'task'
            )
        else:
            # Generate branch name without issue number
            timestamp = int(time.time() % 10000)
            random_id = random.randint(100, 999)
            
            sanitized_description = description.lower().replace(' ', '-').replace('_', '-')
            final_branch_name = f"{branch_type.value}/{sanitized_description}-{random_id}{timestamp}"
    
    # Step 4: Validate branch name format
    if not re.match(r'^[a-zA-Z0-9\-_/]+$', final_branch_name):
        git_helper._show_error("Invalid characters in branch name. Use only letters, numbers, hyphens, and underscores.")
        raise typer.Exit(1)
    
    # Step 5: Create and checkout new branch
    git_helper._show_info(f"Creating and switching to branch: {final_branch_name}")
    result = git_helper._run_command(['git', 'checkout', '-b', final_branch_name])
    
    if result.returncode != 0:
        git_helper._show_error(f"Failed to create branch: {final_branch_name}")
        raise typer.Exit(1)
    
    git_helper._show_success(f"Created and switched to branch: {final_branch_name}")
    
    # Step 6: Push branch to remote repository
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
        git_helper._show_info(f"You can push later with: git push -u origin {final_branch_name}")
    
    # Step 7: Display branch status and next steps
    current_branch = git_helper.get_current_branch()
    git_helper._show_branch_status(current_branch)


@app.command(name="commit-push")
def commit_push(
    message: Annotated[str, typer.Option("--message", "-m", help="Commit message")],
    files: Annotated[Optional[List[str]], typer.Option("--files", "-f", help="Specific files to commit")] = None,
):
    """
    Commit changes and push to current branch with safety checks.
    
    This command:
    1. Validates that current branch is not protected
    2. Adds specified files (or all changes if none specified)
    3. Creates commit with provided message
    4. Pushes changes to remote repository
    5. Provides feedback on CI/CD pipeline status
    
    Examples:
        git_helper commit-push --message "Add user authentication feature"
        git_helper commit-push --message "Fix login bug" --files src/login.py tests/test_login.py
    """
    current_branch = git_helper.get_current_branch()
    
    # Step 1: Validate branch protection
    if current_branch in git_helper.config['protected_branches']:
        git_helper._show_error(f"Cannot commit directly to protected branch: {current_branch}")
        git_helper._show_info("Create a feature branch first using: git_helper create-branch")
        raise typer.Exit(1)
    
    # Step 2: Add files to staging area
    if files:
        # Add specific files
        git_helper._show_info(f"Adding {len(files)} specified files...")
        for file in files:
            result = git_helper._run_command(['git', 'add', file])
            if result.returncode != 0:
                git_helper._show_error(f"Failed to add file: {file}")
                raise typer.Exit(1)
    else:
        # Add all changes
        git_helper._show_info("Adding all changes...")
        git_helper._run_command(['git', 'add', '.'])
    
    # Step 3: Check if there are changes to commit
    result = git_helper._run_command(['git', 'diff', '--staged', '--name-only'])
    if not result.stdout.strip():
        git_helper._show_warning("No changes staged for commit")
        return
    
    # Step 4: Display files to be committed
    staged_files = result.stdout.strip().split('\n')
    console.print(f"\n[cyan]Files to be committed ({len(staged_files)}):[/cyan]")
    for file in staged_files:
        console.print(f"  • {file}")
    
    # Step 5: Create commit
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating commit...", total=None)
        commit_result = git_helper._run_command(['git', 'commit', '-m', message])
        progress.update(task, completed=100, description="Commit complete")
    
    if commit_result.returncode != 0:
        git_helper._show_error("Failed to create commit")
        raise typer.Exit(1)
    
    git_helper._show_success("Changes committed successfully")
    
    # Step 6: Push changes to remote
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
        git_helper._show_info("CI/CD pipeline will start automatically")
        git_helper._show_info("Use 'git_helper check-status' to monitor progress")
    else:
        git_helper._show_error("Failed to push changes")
        git_helper._show_info("You can try pushing manually with: git push origin " + current_branch)


@app.command(name="check-status")
def check_status():
    """
    Check CI/CD pipeline status and branch synchronization.
    
    This command:
    1. Displays current branch information
    2. Shows commit differences with main branch
    3. Provides synchronization recommendations
    4. Indicates readiness for pull request creation
    """
    current_branch = git_helper.get_current_branch()
    main_branch = git_helper.config['main_branch']
    
    console.print(f"\n[cyan]Branch Status: {current_branch}[/cyan]")
    
    # Get latest commit information
    result = git_helper._run_command(['git', 'rev-parse', 'HEAD'])
    commit_sha = result.stdout.strip()
    git_helper._show_info(f"Latest commit: {commit_sha[:8]}")
    
    # Check commits ahead and behind main branch
    result = git_helper._run_command(['git', 'rev-list', '--count', f'{main_branch}..HEAD'])
    commits_ahead = int(result.stdout.strip()) if result.stdout.strip() else 0
    
    result = git_helper._run_command(['git', 'rev-list', '--count', f'HEAD..{main_branch}'])
    commits_behind = int(result.stdout.strip()) if result.stdout.strip() else 0
    
    # Display branch synchronization status
    console.print(f"\n[cyan]Synchronization with {main_branch}:[/cyan]")
    console.print(f"  • Commits ahead: {commits_ahead}")
    console.print(f"  • Commits behind: {commits_behind}")
    
    # Provide recommendations
    if commits_behind > 0:
        git_helper._show_warning(f"Branch is {commits_behind} commits behind {main_branch}")
        git_helper._show_info("Consider running: git_helper sync-main")
    elif commits_ahead > 0:
        git_helper._show_success("Branch is ready for pull request creation")
        git_helper._show_info("Run: git_helper create-pr --title 'Your PR title'")
    else:
        git_helper._show_info("Branch is synchronized with main")


@app.command(name="sync-main")
def sync_main():
    """
    Synchronize current branch with main branch.
    
    This command:
    1. Validates working tree is clean
    2. Fetches latest changes from remote
    3. Merges main branch into current branch
    4. Pushes updated branch to remote
    """
    current_branch = git_helper.get_current_branch()
    main_branch = git_helper.config['main_branch']
    
    # Step 1: Validate branch and working tree
    if current_branch == main_branch:
        git_helper._show_error("Already on main branch")
        return
    
    if not git_helper.is_clean_working_tree():
        git_helper._show_error("Working tree is not clean. Please commit or stash changes first.")
        return
    
    git_helper._show_info(f"Synchronizing {current_branch} with {main_branch}...")
    
    # Step 2: Fetch latest changes from remote
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching latest changes...", total=None)
        git_helper._run_command(['git', 'fetch', 'origin'])
        progress.update(task, completed=100, description="Fetch complete")
    
    # Step 3: Merge main branch into current branch
    merge_result = git_helper._run_command(['git', 'merge', f'origin/{main_branch}'])
    
    if merge_result.returncode == 0:
        git_helper._show_success(f"Successfully synchronized with {main_branch}")
        
        # Step 4: Push updated branch to remote
        push_result = git_helper._run_command(['git', 'push', 'origin', current_branch])
        if push_result.returncode == 0:
            git_helper._show_success("Updated branch pushed to remote")
        else:
            git_helper._show_warning("Sync successful but failed to push")
    else:
        git_helper._show_error("Merge conflicts detected")
        git_helper._show_info("Please resolve conflicts manually and commit")


@app.command(name="create-pr")
def create_pr(
    title: Annotated[str, typer.Option("--title", "-t", help="Pull request title")],
    description: Annotated[str, typer.Option("--description", "-d", help="Pull request description")] = "",
):
    """
    Create a pull request for the current branch.
    
    This command:
    1. Validates current branch is not main
    2. Ensures branch is pushed to remote
    3. Constructs GitHub PR creation URL
    4. Opens browser for PR creation
    
    Examples:
        git_helper create-pr --title "Add user authentication feature"
        git_helper create-pr --title "Fix login bug" --description "Resolves issue with session timeout"
    """
    current_branch = git_helper.get_current_branch()
    main_branch = git_helper.config['main_branch']
    
    # Step 1: Validate branch
    if current_branch == main_branch:
        git_helper._show_error("Cannot create PR from main branch")
        return
    
    if not git_helper.is_clean_working_tree():
        git_helper._show_error("Working tree is not clean. Please commit changes first.")
        return
    
    # Step 2: Check if branch exists on remote
    result = git_helper._run_command(['git', 'ls-remote', '--heads', 'origin', current_branch])
    if not result.stdout.strip():
        git_helper._show_error("Branch not found on remote")
        git_helper._show_info("Push your changes first: git_helper commit-push")
        return
    
    # Step 3: Construct PR creation URL
    git_helper._show_info(f"Creating PR: {current_branch} → {main_branch}")
    git_helper._show_info(f"Title: {title}")
    
    # Build GitHub PR URL (works for both GitHub.com and GitHub pyCTH)
    remote_url = git_helper.get_remote_origin()
    if 'github.com' in remote_url:
        # Extract owner and repo from URL
        import re
        match = re.search(r'github\.com[:/]([^/]+)/([^/\s]+?)(?:\.git)?/?$', remote_url)
        if match:
            owner, repo = match.groups()
            pr_url = f"https://github.com/{owner}/{repo}/compare/{main_branch}...{current_branch}"
        else:
            pr_url = "GitHub URL not detected"
    else:
        pr_url = "Non-GitHub repository detected"
    
    console.print(f"\n[green]✓ PR Creation URL:[/green]")
    console.print(f"  {pr_url}")
    console.print(f"\n[blue]Please complete PR creation in your browser[/blue]")
    
    # Step 4: Open browser (optional)
    if pr_url.startswith('https://') and Confirm.ask("Open PR creation page in browser?"):
        webbrowser.open(pr_url)


@app.command(name="cleanup")
def cleanup():
    """
    Clean up merged branches from local and remote repositories.
    
    This command:
    1. Switches to main branch and syncs with remote
    2. Identifies branches that have been merged (excluding protected branches)
    3. Displays list of branches to be deleted with safety checks
    4. Removes branches locally and from remote (with confirmation)
    5. Returns to main branch
    """
    git_helper._show_info("Cleaning up merged branches...")
    
    # Step 1: Switch to main branch and sync
    main_branch = git_helper.config['main_branch']
    protected_branches = git_helper.config.get('protected_branches', [main_branch, 'develop', 'release/*'])
    
    # Ensure we're on main branch and sync with remote
    current_branch_result = git_helper._run_command(['git', 'branch', '--show-current'])
    current_branch = current_branch_result.stdout.strip() if current_branch_result.returncode == 0 else None
    
    git_helper._run_command(['git', 'checkout', main_branch])
    git_helper._show_info(f"Syncing {main_branch} with remote...")
    sync_result = git_helper._run_command(['git', 'pull', 'origin', main_branch])
    if sync_result.returncode != 0:
        git_helper._show_warning(f"Failed to sync {main_branch} with remote, continuing with local state")
    
    # Step 2: Get list of merged branches with enhanced filtering
    result = git_helper._run_command(['git', 'branch', '--merged'])
    if result.returncode != 0:
        git_helper._show_error("Failed to get list of merged branches")
        return
    
    all_branches = [
        branch.strip().replace('* ', '').replace('  ', '') 
        for branch in result.stdout.split('\n') 
        if branch.strip()
    ]
    
    # Filter out protected branches using helper method
    merged_branches = []
    for branch in all_branches:
        # Skip empty branches and current branch indicator
        if not branch or branch.startswith('*'):
            continue
            
        # Use helper method to check if branch is protected
        if not git_helper._is_protected_branch(branch):
            merged_branches.append(branch)
    
    # Additional safety check: never delete current branch
    if current_branch:
        merged_branches = [b for b in merged_branches if b != current_branch]
    
    if not merged_branches:
        git_helper._show_info("No merged branches to clean up")
        # Ensure we're back on main branch
        git_helper._run_command(['git', 'checkout', main_branch])
        return
    
    # Step 3: Display branches to be deleted with safety information
    console.print(f"\n[yellow]Merged branches to delete ({len(merged_branches)}):[/yellow]")
    for branch in merged_branches:
        console.print(f"  • {branch}")
    
    console.print(f"\n[green]Protected branches (will NOT be deleted):[/green]")
    for protected in protected_branches:
        console.print(f"  • {protected}")
    
    # Step 4: Confirm and delete branches
    if Confirm.ask(f"\nDelete {len(merged_branches)} merged branches? (Protected branches will be preserved)"):
        deleted_count = 0
        failed_count = 0
        
        for branch in merged_branches:
            try:
                # Delete local branch
                local_result = git_helper._run_command(['git', 'branch', '-d', branch])
                if local_result.returncode == 0:
                    deleted_count += 1
                    console.print(f"[green]✓ Deleted local branch: {branch}[/green]")
                    
                    # Delete remote branch (ignore errors if branch doesn't exist on remote)
                    remote_result = git_helper._run_command(['git', 'push', 'origin', '--delete', branch])
                    if remote_result.returncode == 0:
                        console.print(f"[green]✓ Deleted remote branch: {branch}[/green]")
                    else:
                        console.print(f"[yellow]⚠ Could not delete remote branch: {branch} (may not exist on remote)[/yellow]")
                else:
                    failed_count += 1
                    console.print(f"[red]✗ Failed to delete local branch: {branch}[/red]")
                    
            except Exception as e:
                failed_count += 1
                console.print(f"[red]✗ Error deleting branch {branch}: {e}[/red]")
        
        # Final sync and checkout to main
        git_helper._run_command(['git', 'checkout', main_branch])
        
        if deleted_count > 0:
            git_helper._show_success(f"Cleaned up {deleted_count} merged branches")
        if failed_count > 0:
            git_helper._show_warning(f"{failed_count} branches could not be deleted")
    else:
        git_helper._show_info("Branch cleanup cancelled")
        # Ensure we're back on main branch
        git_helper._run_command(['git', 'checkout', main_branch])


# Entry point for script execution
if __name__ == "__main__":
    app()
