# Project Repository

This repository contains the main project code and an advanced DevOps automation system with a modular PR validation framework.

## Project Components

- `pandora_tc_ext_fm.py` - Main project script
- `golden/` - Golden data for the project (preserved)
- `working/` - Working directory for project data (preserved)
- `crt.pre.install` - Critical pre-installation script for the project
- `make_venv.csh` - Script for setting up the virtual environment

## DevOps and CI/CD

This repository features a state-of-the-art DevOps automation system with 3 core components:

### 🤖 1. GitHub Actions CI/CD
- **PR Validation**: Automated testing, security scans, and quality gates
- **Branch Protection**: Automated lint checks on every push  
- **Auto-Merge**: Intelligent merge decisions based on quality scores

### 🔍 2. Local Consistency Checks
- **Code Quality**: Python linting, style checks, and complexity analysis
- **Security**: Local security scanning and secret detection
- **Waivers**: Managed exceptions for special cases

### 🛠️ 3. Developer Helper Scripts  
- **Git Helper**: Streamlined branch creation, commits, and PR management
- **Setup Tool**: Automated environment configuration
- **Config Manager**: Test configuration and validation management

**📖 Complete Documentation**: [`DEVOPS_README.md`](DEVOPS_README.md) *(→ `devops/docs/README.md`)*

### Quick Start

```bash
# 1. Setup environment
python devops/release_automation/setup.py

# 2. Run local checks before Git operations  
python devops/consistency_checker/checker.py

# 3. Use Git helper for streamlined workflow
python devops/release_automation/git_helper.py create-branch --type feature --issue 123
```

## PR Validation System

The repository uses an advanced modular PR validation system:

### Scoring Thresholds
- **≥85%**: Auto-merge approved ✅
- **65-84%**: Manual review required ⚠️
- **≤64%**: Merge blocked ❌

### Validation Categories
1. **Hard Checks** (Must Pass):
   - Critical security vulnerabilities
   - Python syntax validation
   - Dependency security

2. **Soft Checks** (Scoring):
   - Code Quality (25%): Linting, complexity, coverage
   - Security Scan (20%): Medium/low security issues  
   - Testing (25%): Unit, integration, smoke tests
   - Documentation (15%): Docstring coverage, README updates
   - Compliance (15%): License headers, file structure

For detailed information, see the **[Complete DevOps Documentation](DEVOPS_README.md)**.

## Quick Start

### Setting Up PR Validation

1. **Setup and customize**:
   ```bash
   # Interactive setup with all components
   python devops/release_automation/setup.py
   
   # The configuration is all-in-one: .github/pr-test-config.yml
   # Edit to customize thresholds, tests, and validation rules
   ```

2. **Customize for your project**:
   - Adjust scoring thresholds
   - Enable/disable specific checks
   - Configure notification settings

3. **Test with a sample PR**:
   - Create a feature branch
   - Make some changes
   - Open a PR to see validation in action

### Using Development Tools

**Quick Commands**:

#### Consistency Checker
```bash
# Run all checks before committing
python devops/consistency_checker/checker.py

# Run specific rule
python devops/consistency_checker/checker.py --rule python_imports

# List available rules
python devops/consistency_checker/checker.py --list-rules
```

#### Git Helper
```bash
# Create feature branch
python devops/release_automation/git_helper.py create-branch --type feature --issue 123 --description "add-new-feature"

# Commit and push
python devops/release_automation/git_helper.py commit-push --message "Implement feature"

# Create PR
python devops/release_automation/git_helper.py create-pr --title "Add new feature"
```

#### Setup and Configuration
```bash
# Interactive setup
python devops/release_automation/setup.py

# Test config management
python devops/release_automation/test_config_manager.py --validate
```

**📖 Complete tool documentation**: [`DEVOPS_README.md`](DEVOPS_README.md)

## Getting Started

**📖 Complete Guide**: [`DEVOPS_README.md`](DEVOPS_README.md) - Full documentation and setup instructions

For a quick start with the project itself, the main files are preserved at the repository root.

## Directory Structure

The repository has been reorganized to separate the main project code from the DevOps and CI/CD tools:

- `pandora_tc_ext_fm.py` and other project files remain at the root
- `golden/` and `working/` directories are preserved for project data
- All CI/CD and DevOps tools have been moved to the `devops/` directory
- All documentation has been moved to the `devops/docs/` directory

## Need Help?

**📖 DevOps Documentation**: [`DEVOPS_README.md`](DEVOPS_README.md) - Complete system guide  
**🔧 Script Help**: Run any script with `--help` flag for detailed usage  
**🆘 Troubleshooting**: Check the troubleshooting section in the main documentation

## Important Project Files

The following files are part of the main project and not part of the CI/CD workflow:

- `pandora_tc_ext_fm.py` - Main project script
- `golden/` directory - Contains golden data for the project
- `working/` directory - Working directory for project data
- `crt.pre.install` - Critical pre-installation script
- `make_venv.csh` - Virtual environment setup script

These files should be preserved and not modified as part of any CI/CD reorganization.
