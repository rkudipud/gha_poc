# Script Usage Guide

## Overview

This document provides a comprehensive guide to the scripts available in this project, detailing when and why to use each one.

## Quick Reference Table

| Script | Purpose | When to Use |
|--------|---------|-------------|
| [`git-helper.py`](#git-helperpy) | Git workflow automation | Daily development workflow |
| [`setup.py`](#setuppy) | Environment setup | Initial setup or environment refresh |
| [`test-config-manager.py`](#test-config-managerpy) | Test config management | When modifying CI/CD test configuration |
| [`consistency_checker/checker.py`](#consistency_checkercheckerpy) | Code quality validation | Before committing or pushing code |

## Script Details

### `git-helper.py`

A comprehensive CLI tool for managing Git operations within the CI/CD workflow.

#### When to Use

- **Creating new branches**: When starting new features or fixes
- **Committing changes**: For standardized commit messages
- **Pushing to remote**: To ensure proper remote tracking
- **Creating PRs**: When your feature is ready for review
- **Checking status**: To monitor pipeline progress
- **Resolving conflicts**: When merging conflicts occur
- **Syncing with main**: To keep branches up-to-date

#### Key Commands

```bash
# Create a new feature branch
python git-helper.py create-branch --type feature --issue 123 --description "add-new-feature"

# Commit and push changes
python git-helper.py commit-push --message "Implement feature X"

# Create a pull request
python git-helper.py create-pr --title "Add new feature"

# Check pipeline status
python git-helper.py check-status

# Sync with main branch
python git-helper.py sync-main

# Resolve merge conflicts
python git-helper.py resolve-conflicts
```

#### Best Practices

- Always create branches with meaningful descriptions
- Use conventional commit message format
- Regularly sync with main to avoid large conflicts
- Check status after pushing to catch issues early

---

### `setup.py`

Interactive setup script for configuring the development environment and tools.

#### When to Use

- **Initial repository setup**: When first cloning the repository
- **Environment updates**: After major tooling changes
- **Configuration changes**: When organization or repo details change
- **New developer onboarding**: For setting up new team members

#### Key Options

```bash
# Interactive setup with prompts
python setup.py

# Non-interactive setup with predefined values
python setup.py --non-interactive --github-owner ORG_NAME --github-repo REPO_NAME

# Skip virtual environment creation
python setup.py --skip-venv

# Skip git hooks installation
python setup.py --skip-hooks
```

#### Best Practices

- Run with default options for first-time setup
- Update configuration when switching between projects
- Re-run after pulling major configuration changes

---

### `test-config-manager.py`

CLI tool for managing the modular test framework configuration used in PR validation.

#### When to Use

- **Adding new tests**: When creating new test types
- **Modifying test weights**: When changing importance of tests
- **Updating thresholds**: When adjusting auto-merge criteria
- **Validating configuration**: After manual edits to config files
- **Generating reports**: For documentation or auditing

#### Key Commands

```bash
# List all configured tests
python test-config-manager.py list-tests

# Add a new test
python test-config-manager.py add-test --id "python_lint" --name "Python Linting" --weight 25 --enforcement "soft"

# Update an existing test
python test-config-manager.py update-test --id "python_lint" --weight 30 --enabled true

# Set scoring thresholds
python test-config-manager.py set-threshold --auto-merge 85 --manual-review 65 --block 64

# Validate configuration
python test-config-manager.py validate
```

#### Best Practices

- Ensure total weights sum to 100% for soft checks
- Keep configuration in sync with actual implemented tests
- Document changes to test weights or thresholds
- Validate after manual edits to configuration files

---

### `consistency_checker/checker.py`

Local validation framework for checking code quality and consistency before pushing.

#### When to Use

- **Before committing**: To catch issues early
- **Before pushing**: To prevent CI pipeline failures
- **After making changes**: To verify code quality
- **When adding new code**: To ensure consistency with standards

#### Key Commands

```bash
# Run all checks
python consistency_checker/checker.py

# Run specific rules
python consistency_checker/checker.py --rule python_imports --rule naming_conventions

# Check with auto-fix
python consistency_checker/checker.py --fix

# Generate HTML report
python consistency_checker/checker.py --report-format html --output-file report.html

# List available rules
python consistency_checker/checker.py --list-rules
```

#### Best Practices

- Run before each commit to catch issues early
- Use auto-fix for simple issues
- Check only modified files for faster results
- Add waivers only for unavoidable violations

## Integration Between Scripts

These scripts work together in a cohesive workflow:

1. **Setup**: `setup.py` configures the environment and tools
2. **Branch Creation**: `git-helper.py` creates properly named branches
3. **Development**: Code changes made by developer
4. **Local Validation**: `consistency_checker/checker.py` verifies quality
5. **Commit/Push**: `git-helper.py` pushes changes triggering CI
6. **PR Creation**: `git-helper.py` creates pull request
7. **CI Configuration**: `test-config-manager.py` manages test framework

## Scenario-Based Guide

### Starting a New Feature

```bash
# 1. Setup environment (if not already done)
python setup.py

# 2. Create feature branch
python git-helper.py create-branch --type feature --issue 123 --description "add-awesome-feature"

# 3. Make code changes
# ...

# 4. Validate changes
python consistency_checker/checker.py

# 5. Commit and push
python git-helper.py commit-push --message "Implement awesome feature"

# 6. Create PR when ready
python git-helper.py create-pr --title "Add awesome feature"
```

### Modifying CI/CD Configuration

```bash
# 1. View current configuration
python test-config-manager.py list-tests

# 2. Update test weight
python test-config-manager.py update-test --id "python_lint" --weight 30

# 3. Validate configuration
python test-config-manager.py validate

# 4. Commit and push changes
python git-helper.py commit-push --message "Update python lint weight"
```

### Handling Lint Issues

```bash
# 1. Run consistency checker
python consistency_checker/checker.py

# 2. Fix automatable issues
python consistency_checker/checker.py --fix

# 3. For unavoidable issues, add waiver to consistency_checker/waivers.yml

# 4. Validate waiver works
python consistency_checker/checker.py

# 5. Commit all changes including waiver
python git-helper.py commit-push --message "Add feature with lint waiver"
```

## Conclusion

The scripts in this repository are designed to work together to provide a smooth, consistent development experience while maintaining high code quality standards. Use them regularly as part of your development workflow to maximize productivity and code quality.
