# CLI Tools Guide

This document provides a comprehensive guide to the CLI tools in the project, which have been upgraded using [Typer](https://typer.tiangolo.com/) and [Rich](https://github.com/Textualize/rich) libraries.

## Introduction

The CLI tools in this project have been redesigned to provide a more intuitive, user-friendly, and visually appealing interface. This makes working with the development workflow more efficient and enjoyable.

## Available Tools

All tools provide extensive help with `--help` flag and support command completion.

## 1. Consistency Checker

**Location:** `devops/consistency_checker/checker.py`

The Consistency Checker helps ensure that your code meets the project's standards and conventions.

### Key Features

- Beautiful progress indicators with precise timing
- Colorful tables for violation reporting
- Rule-specific validation and auto-fixing
- Detailed help text and command suggestions
- Waiver management and visualization

### Commands

#### Run All Rules

```bash
python devops/consistency_checker/checker.py run-all [OPTIONS]
```

Options:
- `--fix` or `-f`: Automatically fix violations where possible
- `--json` or `-j`: Output results in JSON format
- `--verbose` or `-v`: Show more detailed information

#### Run a Specific Rule

```bash
python devops/consistency_checker/checker.py run-rule <rule-name> [OPTIONS]
```

Options:
- `--fix` or `-f`: Automatically fix violations where possible
- `--json` or `-j`: Output results in JSON format
- `--verbose` or `-v`: Show more detailed information

#### List Available Rules

```bash
python devops/consistency_checker/checker.py list-rules [OPTIONS]
```

Options:
- `--verbose` or `-v`: Show more detailed information about each rule

#### Show Waivers

```bash
python devops/consistency_checker/checker.py show-waivers
```

### Available Rules

1. **naming_conventions**: Enforces consistent naming conventions for Python code
2. **python_imports**: Checks Python import consistency and identifies issues

## 2. Git Helper

**Location:** `devops/release_automation/git_helper.py`

The Git Helper provides a streamlined interface for common Git operations in the enterprise CI/CD workflow.

### Key Features

- Interactive branch creation with smart defaults
- Visual commit history representation
- Automated PR management
- Safety checks for protected branches
- Rich formatting for all outputs

### Commands

#### Create Branch

```bash
python devops/release_automation/git_helper.py create-branch <branch-type> [OPTIONS]
```

Branch types:
- `feature`: For new features
- `bugfix`: For bug fixes
- `hotfix`: For urgent fixes
- `chore`: For maintenance tasks
- `docs`: For documentation updates

Options:
- `--issue` or `-i`: Issue/ticket number
- `--description` or `-d`: Brief description
- `--branch-name` or `-b`: Custom branch name
- `--from` or `-f`: Branch to create from (defaults to main branch)

#### Commit and Push

```bash
python devops/release_automation/git_helper.py commit-push [OPTIONS]
```

Options:
- `--message` or `-m`: Commit message (required)
- `--files` or `-f`: Specific files to commit

#### Check Status

```bash
python devops/release_automation/git_helper.py check-status
```

Shows CI/CD pipeline status and branch information.

#### Sync with Main

```bash
python devops/release_automation/git_helper.py sync-main
```

Syncs current branch with the main branch.

#### Create Pull Request

```bash
python devops/release_automation/git_helper.py create-pr [OPTIONS]
```

Options:
- `--title` or `-t`: PR title (required)
- `--description` or `-d`: PR description

#### Cleanup Merged Branches

```bash
python devops/release_automation/git_helper.py cleanup
```

Cleans up local and remote merged branches.

## 3. Setup Tool

**Location:** `devops/release_automation/setup.py`

The Setup Tool configures the development environment and project-specific settings.

### Key Features

- Interactive configuration with smart defaults
- Automated Git hooks installation
- Beautiful configuration previews
- Cross-platform compatibility
- Step-by-step progress tracking

### Commands

#### Complete Setup

```bash
python devops/release_automation/setup.py setup
```

Runs the complete setup process including:
- System requirements check
- Configuration creation
- Git hooks installation
- Shell script creation

#### Install Git Hooks Only

```bash
python devops/release_automation/setup.py install-hooks
```

#### Update Configuration

```bash
python devops/release_automation/setup.py update-config
```

## 4. Test Configuration Manager

**Location:** `devops/release_automation/test_config_manager.py`

Manages the modular test framework configuration for PR validation.

### Key Features

- Interactive test management
- Configuration validation
- Visual configuration display
- Threshold management
- Rich formatting for all outputs

### Commands

#### List Tests

```bash
python devops/release_automation/test_config_manager.py list [OPTIONS]
```

Options:
- `--details` or `-d`: Show detailed information including action paths

#### Add Test

```bash
python devops/release_automation/test_config_manager.py add <name> <display-name> [OPTIONS]
```

Options:
- `--weight` or `-w`: Test weight percentage (0-100)
- `--action-path` or `-a`: Path to GitHub action
- `--required` or `-r`: Mark as required test
- `--category` or `-c`: Test category

#### Update Test

```bash
python devops/release_automation/test_config_manager.py update <name> [OPTIONS]
```

Options:
- `--display-name` or `-n`: New display name
- `--weight` or `-w`: New weight percentage
- `--action-path` or `-a`: New action path
- `--required` or `-r`: Mark as required test
- `--category` or `-c`: New category

#### Remove Test

```bash
python devops/release_automation/test_config_manager.py remove <name> [OPTIONS]
```

Options:
- `--force` or `-f`: Skip confirmation prompt

#### Validate Configuration

```bash
python devops/release_automation/test_config_manager.py validate
```

#### Show Configuration

```bash
python devops/release_automation/test_config_manager.py show
```

#### Set Thresholds

```bash
python devops/release_automation/test_config_manager.py set-thresholds [OPTIONS]
```

Options:
- `--auto-merge` or `-a`: Auto-merge threshold (0-100)
- `--manual-review` or `-m`: Manual review threshold (0-100)
- `--block` or `-b`: Block threshold (0-100)

## 5. Rule-Specific Tools

Each consistency rule can also be run as a standalone script:

### Naming Conventions

```bash
python devops/consistency_checker/rules/naming_conventions/naming_conventions.py <path> [--fix]
```

### Python Imports

```bash
python devops/consistency_checker/rules/python_imports/python_imports.py <path> [--fix]
```

## Common Features Across All Tools

1. **Tab Completion**: Many commands support tab completion for arguments and options.

2. **Rich Help Text**: Add `--help` to any command to see detailed help information with rich formatting.

3. **Verbose Mode**: Use `--verbose` or `-v` to see more detailed information.

4. **JSON Output**: Use `--json` or `-j` to get machine-readable output for integration with other tools.

5. **Interactive Prompts**: Tools use interactive prompts with smart defaults.

6. **Beautiful Output**: All tools use Rich for colorful, well-formatted output.

7. **Progress Indicators**: Long-running operations show progress with spinners and bars.

8. **Error Handling**: Comprehensive error handling with helpful error messages.

## Troubleshooting

### Virtual Environment Issues

If you encounter issues with the Python environment:

```bash
# Recreate the virtual environment
./make_venv.csh
```

### Permission Issues

If you encounter permission issues with the scripts:

```bash
chmod +x make_venv.csh
```

### Import Errors

If you see import errors related to Rich or Typer:

```bash
# Check the requirements are installed
pip install -r requirements.txt
```

### Configuration Issues

If tools can't find configuration files:

```bash
# Run setup to create default configurations
python devops/release_automation/setup.py setup
```
