# Developer Guide

This comprehensive guide covers all developer tools, workflows, and local development practices for the CI/CD system.

## 🛠️ Developer Tools Overview

### Core Tools
1. **Git Helper** - Git workflow automation and productivity
2. **Setup Tool** - Environment configuration and initialization  
3. **Config Manager** - Test configuration management
4. **Consistency Checker** - Local code quality validation
5. **Pre-commit Hook** - Local validation before commits

### Environment Setup
6. **Virtual Environment Setup** - Python environment management (`make_venv.csh`)
7. **Pre-installation Script** - Project setup automation (`crt.pre.install`)

---

## 🔧 Git Helper (`git_helper.py`)

**Purpose**: Streamlined Git workflow automation with enterprise standards

### Quick Commands
```bash
# Create feature branch
python devops/release_automation/git_helper.py create-branch --type feature --issue 123

# Commit and push with standards
python devops/release_automation/git_helper.py commit-push --message "Add feature"

# Create PR
python devops/release_automation/git_helper.py create-pr --title "New feature"

# Check status
python devops/release_automation/git_helper.py status
```

### Configuration
Creates `.git_helper_config.json` in repo root:
```json
{
  "github": {
    "owner": "your-org",
    "repo": "your-repo"
  },
  "branch_naming": {
    "feature": "feature/{issue}-{description}",
    "bugfix": "bugfix/{issue}-{description}",
    "hotfix": "hotfix/{issue}-{description}"
  },
  "main_branch": "main"
}
```

---

## ⚙️ Setup Tool (`setup.py`)

**Purpose**: Automated environment setup and configuration

### Quick Start
```bash
# Interactive setup
python devops/release_automation/setup.py

# Check current setup
python devops/release_automation/setup.py --check

# Reset to defaults
python devops/release_automation/setup.py --reset
```

### What It Sets Up
- **Git Hooks**: Pre-commit validation hooks
- **Git Configuration**: User name, email, and repository settings
- **GitHub Integration**: Repository owner/name auto-detection
- **Aliases**: Optional command aliases for productivity
- **Environment Variables**: Configuration for tools

---

## 📊 Config Manager (`test_config_manager.py`)

**Purpose**: PR test configuration management and validation

### Quick Commands
```bash
# Validate current config
python devops/release_automation/test_config_manager.py --validate

# Update thresholds
python devops/release_automation/test_config_manager.py --set-threshold auto_merge 90

# Add new test
python devops/release_automation/test_config_manager.py --add-test "custom_security_check:15"
```

---

## 🔍 Consistency Checker (`checker.py`)

**Purpose**: Local code quality validation before CI/CD

### Basic Usage

Run all enabled checks:
```bash
python devops/consistency_checker/checker.py
```

### Advanced Usage

```bash
# Run specific rule
python devops/consistency_checker/checker.py --rule python_imports

# Run with auto-fix
python devops/consistency_checker/checker.py --fix

# Generate HTML report
python devops/consistency_checker/checker.py --report-format html --output-file report.html

# List available rules
python devops/consistency_checker/checker.py --list-rules

# Check specific files
python devops/consistency_checker/checker.py --files src/module1.py src/module2.py
```

### Rule System

The checker uses a pluggable rule system with rules stored in `devops/consistency_checker/rules/`.

#### Available Rules

- **python_imports**: Validates Python import order and style
- **naming_conventions**: Enforces consistent naming patterns
- **line_length**: Checks for long lines that exceed limits
- **docstring_format**: Validates docstring formatting
- **file_structure**: Checks file organization and structure
- **unused_code**: Detects unused imports, variables, and functions

#### Rule Structure

Each rule is a Python module that implements:

1. `check(files, options)`: Performs the check and returns violations
2. `fix(files, violations, options)`: Fixes violations (optional)
3. `get_rule_info()`: Returns rule metadata

### Configuration

Configure the checker in `devops/consistency_checker/checker_config.yml`:

```yaml
# Global settings
settings:
  auto_fix_enabled: true
  report_format: text
  verbose: false

# Rule configuration
rules:
  python_imports:
    enabled: true
    auto_fix: true
    options:
      group_stdlib_first: true
      
  naming_conventions:
    enabled: true
    auto_fix: false
    options:
      enforce_snake_case: true
```

---

## 🔒 Pre-commit Hook

**Purpose**: Local validation before commits reach the remote repository

### Features

- **Python Syntax Checking**: Validates Python syntax errors before commit
- **Large File Detection**: Prevents commits of files larger than 10MB
- **Secret Detection**: Basic pattern matching for potential secrets
- **Configurable**: Can be enabled/disabled via environment variable
- **Smart Python Detection**: Automatically detects available Python interpreter

### Installation

The pre-commit hook is automatically installed by the setup script:

```bash
# Install during setup
python devops/release_automation/setup.py

# Check if hook is installed
ls -la .git/hooks/pre-commit
```

### Configuration

#### Environment Variables

**`DISABLE_PRECOMMIT_HOOK`** - Controls whether the pre-commit hook runs:

```bash
# Disable the hook temporarily
export DISABLE_PRECOMMIT_HOOK=true
git commit -m "Your commit message"

# Disable permanently (add to shell profile)
echo 'export DISABLE_PRECOMMIT_HOOK=true' >> ~/.bashrc

# Re-enable the hook
unset DISABLE_PRECOMMIT_HOOK
```

### What the Hook Checks

1. **Python Syntax Validation**
   - Compiles all staged Python files (`*.py`)
   - Prevents commits with syntax errors
   - Uses the available Python interpreter (`python3` or `python`)

2. **Large File Detection**
   - Scans for files larger than 10MB
   - Suggests using Git LFS for large files
   - Prevents accidental commits of binary/large files

3. **Secret Detection**
   - Basic pattern matching for common secret patterns
   - Interactive prompt to confirm if patterns are detected
   - Case-insensitive matching

### Usage Examples

```bash
# Normal commit (Hook Enabled)
git add my_file.py
git commit -m "Add new feature"
# Output: ✅ Pre-commit checks passed

# Commit with Issues
git add broken_file.py
git commit -m "Add broken code"
# Output: ❌ Python syntax error in broken_file.py (commit blocked)

# Temporarily Disable Hook
export DISABLE_PRECOMMIT_HOOK=true
git commit -m "Emergency fix"
# Output: 💡 Pre-commit hook disabled via DISABLE_PRECOMMIT_HOOK
```

### Troubleshooting

```bash
# Check if hook file exists and is executable
ls -la .git/hooks/pre-commit

# Reinstall the hook
python devops/release_automation/setup.py --force

# Check if disabled via environment
echo $DISABLE_PRECOMMIT_HOOK

# Manual hook test
.git/hooks/pre-commit
```

---

## 🐍 Environment Setup Scripts

### Virtual Environment Setup (`make_venv.csh`)

**Purpose**: Creates and configures Python virtual environment with all dependencies

### Usage
```bash
# Create virtual environment and install dependencies
./make_venv.csh

# Activate the environment
source venv/bin/activate.csh
```

### Features
- **Proxy Configuration**: Automatically sets up Intel proxy settings
- **Dependency Installation**: Installs all required packages from `requirements.txt`
- **Cache Management**: Uses temporary cache directory to avoid disk space issues
- **Python 3.11.1**: Uses specific Python version for consistency

### Pre-installation Script (`crt.pre.install`)

**Purpose**: Automated project setup and environment preparation

### Usage
```bash
# Run complete project setup
./crt.pre.install
```

### What It Does
1. **Environment Creation**: Calls `make_venv.csh` to create virtual environment
2. **Cleanup**: Removes test directories and temporary files
3. **Project Preparation**: Sets up project structure for development

### Project Dependencies (`requirements.txt`)

Contains all Python package dependencies for the project. Generated using `pigar` for minimal dependency set.

---

## 🔄 Daily Development Workflow

### Complete Workflow

```bash
# 1. Setup (once)
python devops/release_automation/setup.py

# 2. Create feature branch
python devops/release_automation/git_helper.py create-branch --type feature --issue 123

# 3. Make changes, then check locally
python devops/consistency_checker/checker.py

# 4. Commit and push
python devops/release_automation/git_helper.py commit-push --message "Add feature"

# 5. Create PR when ready
python devops/release_automation/git_helper.py create-pr --title "New feature"
```

### Integration with CI/CD

The local tools work seamlessly with the CI/CD pipeline:

1. **Local Hook** → **Branch CI** → **PR Validation**
2. Catches issues early in the development cycle
3. Reduces CI/CD failures and iteration time
4. Maintains consistent code quality standards
5. Uses the same consistency checker as the CI pipeline

### Multi-Layer Validation

1. **Pre-commit**: Basic syntax and file checks before commit
2. **Consistency Checker**: Comprehensive code quality validation 
3. **Branch CI**: Automated validation on push via branch-lint-check.yml
4. **PR Validation**: Final comprehensive checks via pr-validation.yml

---

## 💡 Best Practices

### For Daily Development

1. **Run Local Checks**: Always run consistency checker before pushing
2. **Use Pre-commit Hook**: Keep the hook enabled for early feedback
3. **Fix Issues Locally**: Address problems before committing
4. **Use Auto-Fix**: Let tools fix simple issues automatically
5. **Regular Setup**: Reinstall tools when configuration changes

### Tool Usage

1. **Git Helper**: Use for all Git operations to maintain consistency
2. **Consistency Checker**: Run before every commit and push
3. **Config Manager**: Validate configuration changes before deployment
4. **Setup Tool**: Run periodically to ensure environment is up-to-date

### Performance Tips

```bash
# For large repositories, disable hook for bulk commits
DISABLE_PRECOMMIT_HOOK=true git commit -m "Large refactor"

# Or commit in smaller chunks
git add file1.py file2.py
git commit -m "Part 1: Add feature"
```

---

## 🔧 Advanced Configuration

### Custom Hook Behavior

To modify pre-commit hook behavior:

1. **Edit hook template** in `setup.py` (in the `setup_git_hooks()` function)
2. **Reinstall the hook**:
   ```bash
   python devops/release_automation/setup.py --force
   ```

### Auto-Detection Features

The setup script includes intelligent auto-detection:

- **GitHub Repository**: Automatically detects owner/repo from Git remote
- **User Information**: Gets name and email from Git config
- **Python Interpreter**: Finds the best available Python command

### Integration Points

All tools integrate with the broader system:

- **Shared Configuration**: Uses same waiver system as CI/CD
- **Consistent Standards**: Enforces same rules as pipeline
- **Early Feedback**: Provides immediate feedback on issues
- **Transparent Process**: Clear feedback on validation decisions

---

**For detailed usage**: Run any script with `--help` for complete options and examples.
