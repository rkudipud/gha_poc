#!/usr/bin/env python3
"""
Setup script for the Enterprise CI/CD Git Helper

This script installs and configures the git-helper tool for developers.
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path


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
    print("=" * 70)
    print("  Enterprise CI/CD Git Helper Setup")
    print("=" * 70)
    print()


def check_requirements():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    
    # Check Git
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        print("✅ Git is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git is not installed or not in PATH")
        return False
    
    # Check if in git repository
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True, check=True)
        print("✅ In a Git repository")
    except subprocess.CalledProcessError:
        print("❌ Not in a Git repository")
        return False
    
    print("✅ All requirements met")
    return True


def create_config():
    """Create configuration file"""
    print("\n📝 Creating configuration file...")
    
    config = {
        "github": {
            "owner": "",
            "repo": "",
            "token": ""
        },
        "jira": {
            "base_url": "",
            "token": ""
        },
        "branch_naming": {
            "feature": "feature/{jira}-{description}",
            "bugfix": "bugfix/{jira}-{description}",
            "hotfix": "hotfix/{jira}-{description}"
        },
        "main_branch": "main",
        "protected_branches": ["main", "develop", "release/*"]
    }
    
    # Interactive configuration
    print("\nPlease provide the following information:")
    
    # GitHub configuration
    github_owner = input("GitHub repository owner: ").strip()
    if github_owner:
        config["github"]["owner"] = github_owner
    
    github_repo = input("GitHub repository name: ").strip()
    if github_repo:
        config["github"]["repo"] = github_repo
    
    print("\nNote: GitHub token can be set later in the config file or as environment variable")
    
    # JIRA configuration (optional)
    jira_url = input("JIRA base URL (optional): ").strip()
    if jira_url:
        config["jira"]["base_url"] = jira_url
    
    # Main branch
    main_branch = input("Main branch name [main]: ").strip()
    if main_branch:
        config["main_branch"] = main_branch
    
    # Save configuration
    config_file = Path('.git-helper-config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuration saved to {config_file}")
    return config_file


def install_git_helper():
    """Install git-helper script"""
    print("\n🔧 Installing git-helper...")
    
    # Get current script directory
    script_dir = Path(__file__).parent
    git_helper_path = script_dir / 'git-helper.py'
    
    if not git_helper_path.exists():
        # Try looking in the repo root
        repo_root = _find_repo_root()
        alt_path = repo_root / 'devops' / 'release_automation' / 'git-helper.py'
        if alt_path.exists():
            git_helper_path = alt_path
        else:
            print("❌ git-helper.py not found in current directory or devops/release_automation")
            return False
    
    # Make git-helper executable
    git_helper_path.chmod(0o755)
    
    # Create symlink in user's local bin directory
    local_bin = Path.home() / '.local' / 'bin'
    local_bin.mkdir(parents=True, exist_ok=True)
    
    symlink_path = local_bin / 'git-helper'
    
    try:
        if symlink_path.exists():
            symlink_path.unlink()
        symlink_path.symlink_to(git_helper_path.absolute())
        print(f"✅ Created symlink: {symlink_path} -> {git_helper_path}")
    except OSError as e:
        print(f"⚠️ Could not create symlink: {e}")
        print(f"You can manually run: {git_helper_path}")
        return False
    
    # Check if ~/.local/bin is in PATH
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    if str(local_bin) not in path_dirs:
        print(f"\n⚠️ {local_bin} is not in your PATH")
        print("Add this line to your shell profile (.bashrc, .zshrc, etc.):")
        print(f'export PATH="$PATH:{local_bin}"')
    
    return True


def setup_git_hooks():
    """Setup Git hooks"""
    print("\n🪝 Setting up Git hooks...")
    
    hooks_dir = Path('.git/hooks')
    if not hooks_dir.exists():
        print("❌ .git/hooks directory not found")
        return False
    
    # Pre-commit hook
    pre_commit_hook = hooks_dir / 'pre-commit'
    hook_content = '''#!/bin/sh
# Pre-commit hook for enterprise CI/CD workflow

echo "🔍 Running pre-commit checks..."

# Check for Python syntax errors
python_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')
if [ -n "$python_files" ]; then
    for file in $python_files; do
        if [ -f "$file" ]; then
            python -m py_compile "$file"
            if [ $? -ne 0 ]; then
                echo "❌ Python syntax error in $file"
                exit 1
            fi
        fi
    done
fi

# Check for large files (>10MB)
large_files=$(git diff --cached --name-only | xargs -I {} find {} -type f -size +10M 2>/dev/null)
if [ -n "$large_files" ]; then
    echo "❌ Large files detected (>10MB):"
    echo "$large_files"
    echo "Consider using Git LFS for large files"
    exit 1
fi

# Check for secrets (basic patterns)
secrets_found=$(git diff --cached | grep -iE "(password|secret|key|token)\\s*=" | head -5)
if [ -n "$secrets_found" ]; then
    echo "⚠️ Potential secrets detected in commit:"
    echo "$secrets_found"
    echo "Please review and confirm these are not actual secrets"
    read -p "Continue with commit? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Commit cancelled"
        exit 1
    fi
fi

echo "✅ Pre-commit checks passed"
'''
    
    with open(pre_commit_hook, 'w') as f:
        f.write(hook_content)
    
    pre_commit_hook.chmod(0o755)
    print(f"✅ Installed pre-commit hook: {pre_commit_hook}")
    
    return True


def create_alias():
    """Create git alias for the helper"""
    print("\n🔗 Creating Git alias...")
    
    try:
        # Create git alias
        subprocess.run([
            'git', 'config', '--global', 'alias.helper', 
            '!python git-helper.py'
        ], check=True)
        
        print("✅ Created Git alias: git helper")
        print("You can now use: git helper <command>")
        
    except subprocess.CalledProcessError:
        print("⚠️ Could not create Git alias")
        return False
    
    return True


def print_usage_guide():
    """Print usage guide"""
    print("\n" + "=" * 70)
    print("  Setup Complete! 🎉")
    print("=" * 70)
    print()
    print("📖 Quick Start Guide:")
    print()
    print("1. Create a new feature branch:")
    print("   git-helper create-branch --type feature --jira PROJ-123 --description 'add-new-feature'")
    print("   # or: git helper create-branch --type feature --jira PROJ-123 --description 'add-new-feature'")
    print()
    print("2. Commit and push changes:")
    print("   git-helper commit-push --message 'Implement new feature'")
    print()
    print("3. Check CI/CD status:")
    print("   git-helper check-status")
    print()
    print("4. Create pull request:")
    print("   git-helper create-pr --title 'Add new feature'")
    print()
    print("5. Sync with main branch:")
    print("   git-helper sync-main")
    print()
    print("📁 Configuration Files:")
    print("   .git-helper-config.json  - Main configuration")
    print("   devops/consistency_checker/waivers.yml - Centralized waiver management")
    print()
    print("🔗 Useful Links:")
    print("   Documentation: devops/docs/README.md")
    print("   Waiver Guidelines: devops/docs/WAIVERS.md")
    print()
    print("💡 Tips:")
    print("   - Use waiver mechanism sparingly and with proper approval")
    print("   - Monitor CI/CD pipeline status regularly")
    print("   - Keep your branches up to date with main")
    print("   - Review and address lint issues promptly")
    print()


def main():
    """Main setup function"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Setup failed - requirements not met")
        sys.exit(1)
    
    # Create configuration
    config_file = create_config()
    
    # Install git helper
    if not install_git_helper():
        print("\n⚠️ Git helper installation had issues")
    
    # Setup git hooks
    setup_git_hooks()
    
    # Create git alias
    create_alias()
    
    # Print usage guide
    print_usage_guide()
    
    print("Setup completed successfully! 🚀")


if __name__ == '__main__':
    main()
