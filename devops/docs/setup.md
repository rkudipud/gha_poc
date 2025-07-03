# Setup Script Documentation

## Overview

The `setup.py` script provides an interactive setup process for the Enterprise CI/CD Git Helper tool. It configures the local environment, installs dependencies, and initializes the configuration required for working with the CI/CD pipeline.

## Features

- **System Requirement Validation**: Checks for required dependencies and tools
- **Configuration Generation**: Creates and populates configuration files
- **Environment Setup**: Sets up Python virtual environment and dependencies
- **Git Configuration**: Configures Git hooks and repository settings
- **Tool Installation**: Installs the git-helper as a system-wide or user command

## Requirements

- Python 3.7+
- Git client installed and configured
- Internet connection for dependency installation

## Usage

Run the script from the repository root:

```bash
python setup.py
```

For non-interactive mode:

```bash
python setup.py --non-interactive --github-owner ORG_NAME --github-repo REPO_NAME
```

## Setup Process

The script performs the following steps:

1. **System Checks**:
   - Validates Python version (3.7+)
   - Confirms Git installation
   - Verifies repository structure

2. **Configuration Creation**:
   - Generates `.git-helper-config.json` with user-provided values
   - Sets up default branch naming conventions
   - Configures main branch and protected branches

3. **Environment Setup**:
   - Creates virtual environment (if requested)
   - Installs required dependencies from `requirements.txt`
   - Configures Git hooks for pre-push validation

4. **Tool Installation**:
   - Installs git-helper as a command (optional)
   - Adds necessary shell completions

## Configuration Options

During setup, you will be prompted for:

- **GitHub Repository Information**:
  - Repository owner/organization
  - Repository name
  - GitHub token (optional, can be set as environment variable)

- **Branch Configuration**:
  - Main branch name (default: `main`)
  - Branch naming conventions

- **Environment Options**:
  - Virtual environment creation
  - Git hooks installation

## Command Line Arguments

For automated or CI setup:

- `--non-interactive`: Run without prompting for input
- `--github-owner`: GitHub organization or user
- `--github-repo`: GitHub repository name
- `--main-branch`: Main branch name
- `--skip-venv`: Skip virtual environment creation
- `--skip-hooks`: Skip Git hooks installation
- `--install-globally`: Install git-helper as a global command

## Exit Codes

- `0`: Setup completed successfully
- `1`: System requirements not met
- `2`: Configuration creation failed
- `3`: Environment setup failed
- `4`: Tool installation failed

## Post-Setup

After running setup:

1. The `.git-helper-config.json` file will be created in the repository root
2. Git hooks will be installed (if not skipped)
3. Required dependencies will be installed
4. Configuration guidance will be displayed

## Troubleshooting

- **Permission Issues**: Ensure you have write permissions to the repository
- **Dependency Failures**: Check internet connection and PyPI access
- **Git Hook Errors**: Verify Git version and hooks directory permissions
