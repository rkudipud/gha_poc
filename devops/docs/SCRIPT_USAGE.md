# Helper Scripts Guide

This guide covers all developer productivity scripts in the DevOps system, organized by the 3-component structure.

## 🛠️ Script Overview

### Core Scripts
1. **Git Helper** - Git workflow automation and productivity
2. **Setup Tool** - Environment configuration and initialization  
3. **Config Manager** - Test configuration management
4. **Consistency Checker** - Local code quality validation

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

### Quick Commands
```bash
# Run all checks
python devops/consistency_checker/checker.py

# Run specific rule
python devops/consistency_checker/checker.py --rule python_imports

# Run with auto-fix
python devops/consistency_checker/checker.py --fix

# List available rules
python devops/consistency_checker/checker.py --list-rules
```

---

## 🔄 Daily Development Workflow

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

---

**For detailed usage**: Run any script with `--help` for complete options
