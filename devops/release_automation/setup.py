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
import argparse
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
    
    # Auto-detect GitHub info
    print("🔍 Auto-detecting repository information...")
    auto_owner, auto_repo = get_git_remote_info()
    git_user, git_email = get_git_user_info()
    
    if auto_owner and auto_repo:
        print(f"✅ Detected GitHub repository: {auto_owner}/{auto_repo}")
    if git_user:
        print(f"✅ Detected Git user: {git_user} <{git_email}>")
    
    config = {
        "github": {
            "owner": auto_owner or "",
            "repo": auto_repo or "",
            "token": ""
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
        "user_info": {
            "name": git_user or "",
            "email": git_email or ""
        }
    }
    
    # Interactive configuration
    print("\nPlease confirm or update the following information:")
    
    # GitHub configuration
    current_owner = config["github"]["owner"]
    github_owner = input(f"GitHub repository owner [{current_owner}]: ").strip()
    if github_owner:
        config["github"]["owner"] = github_owner
    elif not current_owner:
        print("⚠️ GitHub owner is required for full functionality")
    
    current_repo = config["github"]["repo"]
    github_repo = input(f"GitHub repository name [{current_repo}]: ").strip()
    if github_repo:
        config["github"]["repo"] = github_repo
    elif not current_repo:
        print("⚠️ GitHub repository name is required for full functionality")
    
    print("\nNote: GitHub token can be set later in the config file or as GITHUB_TOKEN environment variable")
    
    # Main branch
    current_main = config["main_branch"]
    main_branch = input(f"Main branch name [{current_main}]: ").strip()
    if main_branch:
        config["main_branch"] = main_branch
    
    # Save configuration
    config_file = Path('.git_helper_config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuration saved to {config_file}")
    return config_file


def install_git_helper():
    """Install git_helper script"""
    print("\n🔧 Installing git_helper...")
    
    # Get current script directory
    script_dir = Path(__file__).parent
    git_helper_path = script_dir / 'git_helper.py'
    
    if not git_helper_path.exists():
        # Try looking in the repo root
        repo_root = _find_repo_root()
        alt_path = repo_root / 'devops' / 'release_automation' / 'git_helper.py'
        if alt_path.exists():
            git_helper_path = alt_path
        else:
            print("❌ git_helper.py not found in current directory or devops/release_automation")
            return False
    
    # Make git_helper executable
    git_helper_path.chmod(0o755)
    
    # Create symlink in user's local bin directory
    local_bin = Path.home() / '.local' / 'bin'
    local_bin.mkdir(parents=True, exist_ok=True)
    
    symlink_path = local_bin / 'git_helper'
    
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

# Check if pre-commit hook is disabled via environment variable
if [ "$DISABLE_PRECOMMIT_HOOK" = "true" ] || [ "$DISABLE_PRECOMMIT_HOOK" = "1" ]; then
    echo "� Pre-commit hook disabled via DISABLE_PRECOMMIT_HOOK environment variable"
    exit 0
fi

echo "�🔍 Running pre-commit checks..."

# Determine the correct Python interpreter
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ No Python interpreter found"
    exit 1
fi

# Check for Python syntax errors
python_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')
if [ -n "$python_files" ]; then
    for file in $python_files; do
        if [ -f "$file" ]; then
            $PYTHON_CMD -m py_compile "$file"
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
    print("💡 To disable: export DISABLE_PRECOMMIT_HOOK=true")
    
    return True


def create_alias():
    """Create git alias for the helper"""
    print("\n🔗 Creating Git alias...")
    
    try:
        # Create git alias
        subprocess.run([
            'git', 'config', '--global', 'alias.helper', 
            '!python git_helper.py'
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
    print("   git_helper create-branch --type feature --issue 123 --description 'add-new-feature'")
    print("   # or: git helper create-branch --type feature --issue 123 --description 'add-new-feature'")
    print()
    print("2. Commit and push changes:")
    print("   git_helper commit-push --message 'Implement new feature'")
    print()
    print("3. Check CI/CD status:")
    print("   git_helper check-status")
    print()
    print("4. Create pull request:")
    print("   git_helper create-pr --title 'Add new feature'")
    print()
    print("5. Sync with main branch:")
    print("   git_helper sync-main")
    print()
    print("📁 Configuration Files:")
    print("   .git_helper_config.json  - Main configuration")
    print("   devops/consistency_checker/waivers.yml - Centralized waiver management")
    print()
    print("🔗 Useful Links:")
    print("   Documentation: devops/docs/README.md")
    print("   Waiver Guidelines: devops/docs/WAIVERS.md")
    print()
    print("🔧 Environment Variables:")
    print("   GITHUB_TOKEN             - GitHub personal access token")
    print("   DISABLE_PRECOMMIT_HOOK   - Set to 'true' to disable pre-commit hook")
    print()
    print("💡 Tips:")
    print("   - Use waiver mechanism sparingly and with proper approval")
    print("   - Monitor CI/CD pipeline status regularly")
    print("   - Keep your branches up to date with main")
    print("   - Review and address lint issues promptly")
    print("   - To disable pre-commit hook: export DISABLE_PRECOMMIT_HOOK=true")
    print()


def get_git_remote_info():
    """Auto-detect GitHub owner and repo from Git remote"""
    try:
        # Get remote origin URL
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True, check=True)
        remote_url = result.stdout.strip()
        
        # Parse GitHub URL patterns
        # SSH: git@github.com:owner/repo.git
        # HTTPS: https://github.com/owner/repo.git
        # Extract owner and repo
        github_pattern = r'github\.com[:/]([^/]+)/([^/.]+)(?:\.git)?'
        match = re.search(github_pattern, remote_url)
        
        if match:
            owner, repo = match.groups()
            return owner, repo
        else:
            print(f"⚠️ Could not parse GitHub info from URL: {remote_url}")
            return None, None
            
    except subprocess.CalledProcessError:
        print("⚠️ Could not get Git remote origin URL")
        return None, None


def get_git_user_info():
    """Get Git user information"""
    try:
        name_result = subprocess.run(['git', 'config', 'user.name'], 
                                   capture_output=True, text=True, check=True)
        email_result = subprocess.run(['git', 'config', 'user.email'], 
                                    capture_output=True, text=True, check=True)
        
        return name_result.stdout.strip(), email_result.stdout.strip()
    except subprocess.CalledProcessError:
        return None, None


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Setup script for Enterprise CI/CD Git Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py                    # Interactive setup
  python setup.py --check            # Check current setup
  python setup.py --auto             # Auto setup with defaults
  python setup.py --no-hooks         # Setup without Git hooks
  python setup.py --reset            # Reset configuration
        """
    )
    
    parser.add_argument('--check', action='store_true',
                       help='Check current setup without making changes')
    parser.add_argument('--auto', action='store_true',
                       help='Automatic setup with detected/default values')
    parser.add_argument('--no-hooks', action='store_true',
                       help='Skip Git hooks installation')
    parser.add_argument('--no-alias', action='store_true',
                       help='Skip Git alias creation')
    parser.add_argument('--reset', action='store_true',
                       help='Reset configuration to defaults')
    parser.add_argument('--force', action='store_true',
                       help='Force overwrite existing configuration')
    
    return parser.parse_args()


def check_current_setup():
    """Check current setup status"""
    print("🔍 Checking current setup status...")
    
    # Check configuration file
    config_file = Path('.git_helper_config.json')
    if config_file.exists():
        print("✅ Configuration file exists")
        try:
            with open(config_file) as f:
                config = json.load(f)
            print(f"   GitHub: {config.get('github', {}).get('owner', 'not set')}/{config.get('github', {}).get('repo', 'not set')}")
            print(f"   Main branch: {config.get('main_branch', 'not set')}")
        except Exception as e:
            print(f"⚠️ Configuration file exists but is invalid: {e}")
    else:
        print("❌ Configuration file not found")
    
    # Check Git hooks
    pre_commit_hook = Path('.git/hooks/pre-commit')
    if pre_commit_hook.exists():
        print("✅ Pre-commit hook installed")
    else:
        print("❌ Pre-commit hook not found")
    
    # Check Git alias
    try:
        result = subprocess.run(['git', 'config', 'alias.helper'], 
                              capture_output=True, text=True, check=True)
        print("✅ Git alias 'helper' configured")
    except subprocess.CalledProcessError:
        print("❌ Git alias 'helper' not found")
    
    # Check symlink
    local_bin = Path.home() / '.local' / 'bin' / 'git_helper'
    if local_bin.exists():
        print("✅ git_helper symlink exists")
    else:
        print("❌ git_helper symlink not found")


def main():
    """Main setup function"""
    args = parse_arguments()
    
    print_banner()
    
    # Check requirements first
    if not check_requirements():
        print("\n❌ Setup failed - requirements not met")
        sys.exit(1)
    
    # Handle check mode
    if args.check:
        check_current_setup()
        return
    
    # Handle reset mode
    if args.reset:
        print("🔄 Resetting configuration...")
        config_file = Path('.git_helper_config.json')
        if config_file.exists():
            config_file.unlink()
            print("✅ Removed configuration file")
    
    # Check if config exists and force flag
    config_file = Path('.git_helper_config.json')
    if config_file.exists() and not args.force and not args.reset:
        print(f"\n⚠️ Configuration file already exists: {config_file}")
        print("Use --force to overwrite or --check to view current settings")
        return
    
    # Create configuration
    if args.auto:
        config_file = create_auto_config()
    else:
        config_file = create_config()
    
    # Install git helper
    if not install_git_helper():
        print("\n⚠️ Git helper installation had issues")
    
    # Setup git hooks
    if not args.no_hooks:
        setup_git_hooks()
    else:
        print("\n⏭️ Skipping Git hooks installation")
    
    # Create git alias
    if not args.no_alias:
        create_alias()
    else:
        print("\n⏭️ Skipping Git alias creation")
    
    # Print usage guide
    print_usage_guide()
    
    print("Setup completed successfully! 🚀")


def create_auto_config():
    """Create configuration automatically with detected values"""
    print("\n📝 Creating configuration file automatically...")
    
    # Auto-detect GitHub info
    auto_owner, auto_repo = get_git_remote_info()
    git_user, git_email = get_git_user_info()
    
    config = {
        "github": {
            "owner": auto_owner or "",
            "repo": auto_repo or "",
            "token": ""
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
        "user_info": {
            "name": git_user or "",
            "email": git_email or ""
        }
    }
    
    if auto_owner and auto_repo:
        print(f"✅ Auto-detected GitHub repository: {auto_owner}/{auto_repo}")
    if git_user:
        print(f"✅ Auto-detected Git user: {git_user} <{git_email}>")
    
    # Save configuration
    config_file = Path('.git_helper_config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuration saved to {config_file}")
    return config_file


if __name__ == '__main__':
    main()
