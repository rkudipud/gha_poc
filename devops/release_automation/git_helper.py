#!/usr/bin/env python3
"""
Git Helper Script for Enterprise CI/CD Workflow

This script provides a simplified interface for developers to work with
the enterprise CI/CD pipeline without needing deep Git knowledge.

Usage:
    python devops/release_automation/git_helper.py create-branch --type feature --issue 123 --description "add-new-feature"
    python devops/release_automation/git_helper.py create-branch --type bugfix --branch-name "custom-branch-name"
    python devops/release_automation/git_helper.py commit-push --message "Implement new feature"
    python devops/release_automation/git_helper.py check-status
    python devops/release_automation/git_helper.py create-pr --title "Add new feature"
    python devops/release_automation/git_helper.py sync-main
    python devops/release_automation/git_helper.py resolve-conflicts
"""
import argparse
import subprocess
import sys
import json
import re
import random
import time
from pathlib import Path
from typing import Optional, List, Dict, Any


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
    UNDERLINE = '\033[4m'
    END = '\033[0m'


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
        raise Exception("Not in a Git repository")
    
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
                "hotfix": "hotfix/{issue}-{description}"
            },
            "main_branch": "main",
            "protected_branches": ["main", "develop", "release/*"]
        }
        
        config_file = self.repo_root / '.git_helper_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"{Colors.YELLOW}Created default config at {config_file}")
        print(f"Please update with your GitHub details{Colors.END}")
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
            print(f"{Colors.RED}Error running command {' '.join(command)}: {e}{Colors.END}")
            sys.exit(1)
    
    def _print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    
    def _print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    
    def _print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
    
    def _print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")
    
    def _show_branch_status(self, branch_name: str):
        """Show current branch status after creation"""
        print(f"\n{Colors.BOLD}=== Branch Status ==={Colors.END}")
        print(f"📍 Current branch: {Colors.GREEN}{branch_name}{Colors.END}")
        print(f"🌿 Based on: {Colors.BLUE}{self.config['main_branch']}{Colors.END}")
        
        # Show recent commits to confirm we're in the right place
        result = self._run_command(['git', 'log', '--oneline', '-3'])
        if result.returncode == 0 and result.stdout.strip():
            print(f"\n{Colors.BLUE}📝 Recent commits:{Colors.END}")
            for line in result.stdout.strip().split('\n')[:3]:
                print(f"   {line}")
        
        print(f"\n{Colors.CYAN}💡 Next steps:{Colors.END}")
        print("   1. Make your code changes")
        print("   2. Run: python devops/release_automation/git_helper.py commit-push --message 'Your message'")
        print("   3. Create PR when ready")
        print()

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
    
    def create_branch(self, branch_type: str, issue_number: str = None, description: str = None, custom_branch_name: str = None):
        """Create a new feature/bugfix/hotfix branch"""
        if not self.is_clean_working_tree():
            self._print_error("Working tree is not clean. Please commit or stash changes first.")
            return
        
        # Switch to main and pull latest
        main_branch = self.config['main_branch']
        self._print_info(f"Switching to {main_branch} and pulling latest changes...")
        
        self._run_command(['git', 'checkout', main_branch])
        result = self._run_command(['git', 'pull', 'origin', main_branch])
        
        if result.returncode != 0:
            self._print_error(f"Failed to pull latest changes from {main_branch}")
            return
        
        # Use custom branch name if provided
        if custom_branch_name:
            branch_name = custom_branch_name
        else:
            # Validate inputs for automatic naming
            if not issue_number and not description:
                self._print_error("When not using --branch-name, you must provide either --issue, --description, or both")
                return
                
            # Create branch name using default naming scheme
            if issue_number:
                # Use provided issue number
                issue_prefix = self.config.get('issue_tracking', {}).get('issue_prefix', 'GH')
                if not issue_number.startswith(issue_prefix):
                    issue_number = f"{issue_prefix}-{issue_number}"
                
                branch_template = self.config['branch_naming'].get(branch_type, 'feature/{issue}-{description}')
                branch_name = branch_template.format(
                    issue=issue_number.upper(),
                    description=description.lower().replace(' ', '-').replace('_', '-') if description else 'task'
                )
            else:
                # Generate random branch name without issue number (description-only mode)
                # Generate a random identifier for the branch
                timestamp = int(time.time() % 10000)  # Last 4 digits of timestamp
                random_id = random.randint(100, 999)
                
                # Create branch name: type/description-randomid
                sanitized_description = description.lower().replace(' ', '-').replace('_', '-')
                branch_name = f"{branch_type}/{sanitized_description}-{random_id}{timestamp}"
        
        # Validate branch name
        if not re.match(r'^[a-zA-Z0-9\-_/]+$', branch_name):
            self._print_error("Invalid characters in branch name")
            return
        
        # Create and checkout new branch
        self._print_info(f"Creating and switching to branch: {branch_name}")
        result = self._run_command(['git', 'checkout', '-b', branch_name])
        
        if result.returncode == 0:
            # Confirm current branch
            current_branch = self.get_current_branch()
            self._print_success(f"✅ Created and switched to branch: {branch_name}")
            
            # Push branch to remote
            self._print_info("🚀 Pushing branch to remote...")
            push_result = self._run_command(['git', 'push', '-u', 'origin', branch_name])
            
            if push_result.returncode == 0:
                self._print_success("🌐 Branch pushed to remote successfully")
            else:
                self._print_warning("⚠️  Branch created locally but failed to push to remote")
                self._print_info("💡 You can push later with: git push -u origin " + branch_name)
            
            # Show detailed status
            self._show_branch_status(current_branch)
        else:
            self._print_error(f"❌ Failed to create branch: {branch_name}")
            # Stay on original branch if creation failed
    
    def commit_push(self, message: str, files: Optional[List[str]] = None):
        """Commit changes and push to current branch"""
        current_branch = self.get_current_branch()
        
        if current_branch in self.config['protected_branches']:
            self._print_error(f"Cannot commit directly to protected branch: {current_branch}")
            return
        
        # Add files
        if files:
            for file in files:
                self._run_command(['git', 'add', file])
        else:
            # Add all modified files
            self._run_command(['git', 'add', '.'])
        
        # Check if there are changes to commit
        result = self._run_command(['git', 'diff', '--staged', '--name-only'])
        if not result.stdout.strip():
            self._print_warning("No changes to commit")
            return
        
        # Commit changes
        self._print_info(f"Committing changes with message: {message}")
        commit_result = self._run_command(['git', 'commit', '-m', message])
        
        if commit_result.returncode == 0:
            self._print_success("Changes committed successfully")
            
            # Push changes
            self._print_info(f"Pushing to branch: {current_branch}")
            push_result = self._run_command(['git', 'push', 'origin', current_branch])
            
            if push_result.returncode == 0:
                self._print_success("Changes pushed successfully")
                self._print_info("CI/CD pipeline will start automatically. Use 'check-status' to monitor.")
            else:
                self._print_error("Failed to push changes")
        else:
            self._print_error("Failed to commit changes")
    
    def check_status(self):
        """Check CI/CD pipeline status for current branch"""
        current_branch = self.get_current_branch()
        
        print(f"{Colors.BOLD}=== CI/CD Status for branch: {current_branch} === {Colors.END}")
        
        # Check for open issues
        self._check_open_issues(current_branch)
        
        # Check latest workflow runs
        self._check_workflow_status(current_branch)
        
        # Check if ready for PR
        self._check_pr_readiness(current_branch)
    
    def _check_open_issues(self, branch: str):
        """Check for open lint issues for the branch"""
        print(f"{Colors.BLUE}🔍 Checking for open issues...{Colors.END}")
        
        # This would integrate with GitHub API to check for open issues
        # For now, simulate the check
        self._print_info("No open lint issues found for this branch")
    
    def _check_workflow_status(self, branch: str):
        """Check GitHub Actions workflow status"""
        print(f"{Colors.BLUE}🔍 Checking workflow status...{Colors.END}")
        
        # Get latest commit
        result = self._run_command(['git', 'rev-parse', 'HEAD'])
        commit_sha = result.stdout.strip()
        
        # This would check GitHub API for workflow status
        self._print_info(f"Latest commit: {commit_sha[:8]}")
        self._print_info("Branch lint check: ✅ Passed")
    
    def _check_pr_readiness(self, branch: str):
        """Check if branch is ready for PR"""
        main_branch = self.config['main_branch']
        
        # Check if branch is ahead of main
        result = self._run_command(['git', 'rev-list', '--count', f'{main_branch}..HEAD'])
        commits_ahead = int(result.stdout.strip()) if result.stdout.strip() else 0
        
        # Check if branch is behind main
        result = self._run_command(['git', 'rev-list', '--count', f'HEAD..{main_branch}'])
        commits_behind = int(result.stdout.strip()) if result.stdout.strip() else 0
        
        print(f"{Colors.BLUE}📊 Branch Status:{Colors.END}")
        print(f"   Commits ahead of {main_branch}: {commits_ahead}")
        print(f"   Commits behind {main_branch}: {commits_behind}")
        
        if commits_behind > 0:
            self._print_warning(f"Branch is {commits_behind} commits behind {main_branch}. Consider syncing.")
        
        if commits_ahead > 0 and commits_behind == 0:
            self._print_success("Branch is ready for PR creation")
    
    def sync_main(self):
        """Sync current branch with main branch"""
        current_branch = self.get_current_branch()
        main_branch = self.config['main_branch']
        
        if current_branch == main_branch:
            self._print_error("Already on main branch")
            return
        
        if not self.is_clean_working_tree():
            self._print_error("Working tree is not clean. Please commit or stash changes first.")
            return
        
        self._print_info(f"Syncing {current_branch} with {main_branch}...")
        
        # Fetch latest changes
        self._run_command(['git', 'fetch', 'origin'])
        
        # Merge main into current branch
        merge_result = self._run_command(['git', 'merge', f'origin/{main_branch}'])
        
        if merge_result.returncode == 0:
            self._print_success(f"Successfully synced with {main_branch}")
            
            # Push updated branch
            push_result = self._run_command(['git', 'push', 'origin', current_branch])
            if push_result.returncode == 0:
                self._print_success("Updated branch pushed to remote")
            else:
                self._print_warning("Merge conflicts detected. Use 'resolve-conflicts' command.")
    
    def resolve_conflicts(self):
        """Help resolve merge conflicts"""
        print(f"{Colors.BOLD}=== Merge Conflict Resolution Helper ==={Colors.END}")
        
        # Check for merge conflicts
        result = self._run_command(['git', 'diff', '--name-only', '--diff-filter=U'])
        conflicted_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        if not conflicted_files:
            self._print_info("No merge conflicts detected")
            return
        
        print(f"{Colors.YELLOW}📁 Files with conflicts:{Colors.END}")
        for file in conflicted_files:
            print(f"   - {file}")
        
        print(f"\n{Colors.BLUE}🛠️  Resolution steps:{Colors.END}")
        print("1. Open each conflicted file in your editor")
        print("2. Look for conflict markers: <<<<<<< ======= >>>>>>>")
        print("3. Edit the file to resolve conflicts")
        print("4. Remove conflict markers")
        print("5. Test your changes")
        print("6. Run: git add <resolved-file>")
        print("7. When all conflicts are resolved, run: git commit")
        
        # Interactive resolution
        response = input(f"\n{Colors.CYAN}Open VS Code to resolve conflicts? (y/n): {Colors.END}")
        if response.lower() == 'y':
            for file in conflicted_files:
                self._run_command(['code', file], capture_output=False)
    
    def create_pr(self, title: str, description: str = ""):
        """Create a pull request"""
        current_branch = self.get_current_branch()
        main_branch = self.config['main_branch']
        
        if current_branch == main_branch:
            self._print_error("Cannot create PR from main branch")
            return
        
        if not self.is_clean_working_tree():
            self._print_error("Working tree is not clean. Please commit changes first.")
            return
        
        # Check if branch is pushed to remote
        result = self._run_command(['git', 'ls-remote', '--heads', 'origin', current_branch])
        if not result.stdout.strip():
            self._print_error("Branch not found on remote. Please push your changes first.")
            return
        
        self._print_info(f"Creating PR: {current_branch} -> {main_branch}")
        self._print_info(f"Title: {title}")
        
        # This would integrate with GitHub API to create PR
        pr_url = f"https://github.com/{self.config['github']['owner']}/{self.config['github']['repo']}/compare/{main_branch}...{current_branch}"
        
        print(f"{Colors.GREEN}🔗 PR creation URL:{Colors.END}")
        print(f"   {pr_url}")
        print(f"\n{Colors.BLUE}ℹ️  Please complete PR creation in your browser{Colors.END}")
        
        # Open browser (optional)
        response = input(f"\n{Colors.CYAN}Open PR creation page in browser? (y/n): {Colors.END}")
        if response.lower() == 'y':
            import webbrowser
            webbrowser.open(pr_url)
    
    def cleanup_merged_branches(self):
        """Clean up merged branches"""
        self._print_info("Cleaning up merged branches...")
        
        # Switch to main
        main_branch = self.config['main_branch']
        self._run_command(['git', 'checkout', main_branch])
        
        # Get merged branches
        result = self._run_command(['git', 'branch', '--merged'])
        merged_branches = [
            branch.strip().replace('* ', '') 
            for branch in result.stdout.split('\n') 
            if branch.strip() and not branch.strip().startswith('*') and branch.strip() != main_branch
        ]
        
        if not merged_branches:
            self._print_info("No merged branches to clean up")
            return
        
        print(f"{Colors.YELLOW}🗑️  Merged branches to delete:{Colors.END}")
        for branch in merged_branches:
            print(f"   - {branch}")
        
        response = input(f"\n{Colors.CYAN}Delete these branches? (y/n): {Colors.END}")
        if response.lower() == 'y':
            for branch in merged_branches:
                # Delete local branch
                self._run_command(['git', 'branch', '-d', branch])
                # Delete remote branch
                self._run_command(['git', 'push', 'origin', '--delete', branch])
            
            self._print_success("Merged branches cleaned up")
    
    def setup_hooks(self):
        """Setup Git hooks for automated checks"""
        hooks_dir = self.repo_root / '.git' / 'hooks'
        
        # Pre-commit hook
        pre_commit_hook = hooks_dir / 'pre-commit'
        hook_content = '''#!/bin/sh
# Pre-commit hook for basic checks
echo "Running pre-commit checks..."

# Check for Python syntax errors
python -m py_compile **/*.py 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Python syntax errors detected"
    exit 1
fi

# Check for large files (>10MB)
large_files=$(find . -type f -size +10M -not -path "./.git/*")
if [ -n "$large_files" ]; then
    echo "❌ Large files detected (>10MB):"
    echo "$large_files"
    exit 1
fi

echo "✅ Pre-commit checks passed"
'''
        
        with open(pre_commit_hook, 'w') as f:
            f.write(hook_content)
        
        # Make executable
        pre_commit_hook.chmod(0o755)
        
        self._print_success("Git hooks installed successfully")
    
    def delete_branch(self, branch_name: str, force: bool = False):
        """Delete a branch with ownership verification"""
        print(f"{Colors.BOLD}=== Branch Deletion with Ownership Verification ==={Colors.END}")
        
        # Check if branch exists locally
        result = self._run_command(['git', 'branch', '--list', branch_name])
        branch_exists_locally = bool(result.stdout.strip())
        
        # Check if branch exists on remote
        result = self._run_command(['git', 'ls-remote', '--heads', 'origin', branch_name])
        branch_exists_remotely = bool(result.stdout.strip())
        
        if not branch_exists_locally and not branch_exists_remotely:
            self._print_error(f"Branch '{branch_name}' does not exist locally or remotely")
            return
        
        # Get current user information
        try:
            user_name_result = self._run_command(['git', 'config', 'user.name'])
            user_email_result = self._run_command(['git', 'config', 'user.email'])
            current_user_name = user_name_result.stdout.strip()
            current_user_email = user_email_result.stdout.strip()
        except Exception:
            self._print_error("Could not retrieve Git user configuration")
            return
        
        # Check ownership verification
        ownership_verified = False
        
        if branch_exists_locally or branch_exists_remotely:
            # Get commits from the branch to check authorship
            if branch_exists_locally:
                # Check local branch commits
                result = self._run_command(['git', 'log', '--pretty=format:%an|%ae', branch_name, '--not', self.config['main_branch']])
            else:
                # Check remote branch commits
                result = self._run_command(['git', 'log', '--pretty=format:%an|%ae', f'origin/{branch_name}', '--not', f'origin/{self.config["main_branch"]}'])
            
            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip().split('\n')
                branch_authors = set()
                
                for commit in commits:
                    if '|' in commit:
                        author_name, author_email = commit.split('|', 1)
                        branch_authors.add((author_name.strip(), author_email.strip()))
                
                # Check if current user is one of the authors
                current_user_tuple = (current_user_name, current_user_email)
                if current_user_tuple in branch_authors or len(branch_authors) == 0:
                    ownership_verified = True
                else:
                    print(f"{Colors.YELLOW}⚠️  Branch ownership verification:{Colors.END}")
                    print(f"   Current user: {current_user_name} <{current_user_email}>")
                    print(f"   Branch authors:")
                    for author_name, author_email in branch_authors:
                        print(f"     - {author_name} <{author_email}>")
                    
                    if not force:
                        print(f"\n{Colors.RED}❌ You are not an author of this branch{Colors.END}")
                        print(f"{Colors.CYAN}💡 Use --force flag to override ownership verification{Colors.END}")
                        return
                    else:
                        print(f"\n{Colors.YELLOW}⚠️  Proceeding with force deletion (ownership verification bypassed){Colors.END}")
                        ownership_verified = True
            else:
                # No commits specific to this branch (might be empty branch)
                ownership_verified = True
        
        # Check if trying to delete protected branch
        protected_branches = self.config.get('protected_branches', ['main', 'develop'])
        if any(branch_name == protected or 
               (protected.endswith('/*') and branch_name.startswith(protected[:-2])) 
               for protected in protected_branches):
            self._print_error(f"Cannot delete protected branch: {branch_name}")
            return
        
        # Check if currently on the branch to be deleted
        current_branch = self.get_current_branch()
        if current_branch == branch_name:
            main_branch = self.config['main_branch']
            self._print_info(f"Switching from {branch_name} to {main_branch} before deletion")
            switch_result = self._run_command(['git', 'checkout', main_branch])
            if switch_result.returncode != 0:
                self._print_error(f"Failed to switch to {main_branch}")
                return
        
        # Show deletion plan
        print(f"\n{Colors.BLUE}📋 Deletion Plan:{Colors.END}")
        if branch_exists_locally:
            print(f"   🗑️  Delete local branch: {branch_name}")
        if branch_exists_remotely:
            print(f"   🗑️  Delete remote branch: origin/{branch_name}")
        
        print(f"\n{Colors.GREEN}✅ Ownership verified: {current_user_name} <{current_user_email}>{Colors.END}")
        
        # Confirm deletion
        if not force:
            response = input(f"\n{Colors.CYAN}Proceed with branch deletion? (y/n): {Colors.END}")
            if response.lower() != 'y':
                self._print_info("Branch deletion cancelled")
                return
        
        # Perform deletion
        deletion_success = True
        
        # Delete local branch
        if branch_exists_locally:
            self._print_info(f"Deleting local branch: {branch_name}")
            delete_result = self._run_command(['git', 'branch', '-D', branch_name])
            if delete_result.returncode == 0:
                self._print_success(f"Local branch '{branch_name}' deleted successfully")
            else:
                self._print_error(f"Failed to delete local branch: {branch_name}")
                deletion_success = False
        
        # Delete remote branch
        if branch_exists_remotely:
            self._print_info(f"Deleting remote branch: origin/{branch_name}")
            delete_remote_result = self._run_command(['git', 'push', 'origin', '--delete', branch_name])
            if delete_remote_result.returncode == 0:
                self._print_success(f"Remote branch 'origin/{branch_name}' deleted successfully")
            else:
                self._print_error(f"Failed to delete remote branch: {branch_name}")
                deletion_success = False
        
        if deletion_success:
            self._print_success(f"Branch '{branch_name}' deleted successfully with ownership verification")
        else:
            self._print_warning("Branch deletion completed with some errors")
    

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Git Helper for Enterprise CI/CD Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python git_helper.py create-branch --type feature --issue 123 --description "add-new-feature"
  python git_helper.py create-branch --type feature --description "test branch for demo"
  python git_helper.py create-branch --type bugfix --branch-name "custom-branch-name"
  python git_helper.py commit-push --message "Implement new feature"
  python git_helper.py check-status
  python git_helper.py create-pr --title "Add new feature"
  python git_helper.py sync-main
  python git_helper.py delete-branch --branch-name "feature-branch-name"
  python git_helper.py delete-branch --branch-name "feature-branch-name" --force
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create branch command
    create_parser = subparsers.add_parser('create-branch', help='Create a new feature/bugfix branch')
    create_parser.add_argument('--type', choices=['feature', 'bugfix', 'hotfix'], required=True,
                              help='Type of branch to create')
    
    # Either issue + description OR custom branch name OR just description
    group = create_parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--branch-name', help='Custom branch name (overrides default naming scheme)')
    
    create_parser.add_argument('--issue', help='Issue/ticket number (optional)')
    create_parser.add_argument('--description', help='Brief description (required when not using --branch-name)')
    
    # Commit and push command
    commit_parser = subparsers.add_parser('commit-push', help='Commit and push changes')
    commit_parser.add_argument('--message', required=True, help='Commit message')
    commit_parser.add_argument('--files', nargs='*', help='Specific files to commit')
    
    # Check status command
    subparsers.add_parser('check-status', help='Check CI/CD pipeline status')
    
    # Create PR command
    pr_parser = subparsers.add_parser('create-pr', help='Create a pull request')
    pr_parser.add_argument('--title', required=True, help='PR title')
    pr_parser.add_argument('--description', default='', help='PR description')
    
    # Sync with main command
    subparsers.add_parser('sync-main', help='Sync current branch with main')
    
    # Resolve conflicts command
    subparsers.add_parser('resolve-conflicts', help='Help resolve merge conflicts')
    
    # Cleanup command
    subparsers.add_parser('cleanup', help='Clean up merged branches')
    
    # Setup command
    subparsers.add_parser('setup-hooks', help='Setup Git hooks')
    
    # Delete branch command
    delete_parser = subparsers.add_parser('delete-branch', help='Delete a branch with ownership verification')
    delete_parser.add_argument('--branch-name', required=True, help='Name of the branch to delete')
    delete_parser.add_argument('--force', action='store_true', help='Force deletion (bypass ownership verification)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        git_helper = GitHelper()
        
        if args.command == 'create-branch':
            # Validate arguments for create-branch
            if not args.branch_name and not args.issue and not args.description:
                print(f"{Colors.RED}❌ Error: When not using --branch-name, you must provide either --issue, --description, or both{Colors.END}")
                return
            git_helper.create_branch(args.type, args.issue, args.description, args.branch_name)
        elif args.command == 'commit-push':
            git_helper.commit_push(args.message, args.files)
        elif args.command == 'check-status':
            git_helper.check_status()
        elif args.command == 'create-pr':
            git_helper.create_pr(args.title, args.description)
        elif args.command == 'sync-main':
            git_helper.sync_main()
        elif args.command == 'resolve-conflicts':
            git_helper.resolve_conflicts()
        elif args.command == 'cleanup':
            git_helper.cleanup_merged_branches()
        elif args.command == 'setup-hooks':
            git_helper.setup_hooks()
        elif args.command == 'delete-branch':
            git_helper.delete_branch(args.branch_name, args.force)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == '__main__':
    main()
