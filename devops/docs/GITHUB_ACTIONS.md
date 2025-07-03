# GitHub Actions Documentation

## Overview

This document provides detailed information about the GitHub Actions implemented in this repository, their structure, flow, and how to use them effectively with the reorganized project structure.

## GitHub Actions Structure

The GitHub Actions are organized into two main components:

1. **Workflows** (located in `.github/workflows/`):
   - **branch-lint-check.yml**: Triggered on push to feature branches
   - **pr-validation-modular.yml**: Triggered on PR creation and updates
   - **pr-validation-simple.yml**: A simplified PR validation for quick checks
   - **pr-validation.yml**: Legacy PR validation workflow

2. **Reusable Actions** (located in `.github/actions/`):
   - **python-lint-enhanced/**: Enhanced Python linting with waiver support
   - **consistency-check/**: Code consistency validation
   - **security-scan/**: Security vulnerability and secret scanning
   - **coverage-check/**: Test coverage analysis
   - **branch-protection-check/**: Branch protection compliance
   - **test-orchestrator/**: Central test coordination
   - **email-notification/**: Notification system for workflow results
   - **docs-check/**: Documentation validation

## Workflow Flow

### Branch Lint Check Flow

```
Developer Push → branch-lint-check.yml → Change Detection → Python Lint → Waiver Application → Issue Creation/Update
```

1. **Trigger**: Activated on push to any branch except main
2. **Process**:
   - Detects changed files
   - Runs linting only on changed files (or all files if configured)
   - Applies waivers from `devops/consistency_checker/waivers.yml`
   - Creates or updates issues for failures
   - Notifies relevant parties

### PR Validation Flow

```
PR Creation/Update → pr-validation-modular.yml → Config Loading → Hard Checks → Soft Checks → Score Calculation → Decision
```

1. **Trigger**: Activated on PR creation, updates, or review submissions
2. **Process**:
   - Loads test configuration from `.github/pr-test-config.yml`
   - Runs hard (must-pass) checks first
   - Runs soft (scored) checks
   - Calculates overall score
   - Makes decision: auto-merge, request review, or block

## Configuration Files

### PR Test Configuration

Located at `.github/pr-test-config.yml`, this file configures:
- Which tests to run
- Weight of each test in the overall score
- Thresholds for auto-merge, review, and blocking
- Environment-specific overrides

Example:
```yaml
tests:
  security_scan:
    weight: 25
    category: hard
  python_lint:
    weight: 20
    category: soft
  consistency_check:
    weight: 15
    category: soft
thresholds:
  auto_merge: 85
  review_required: 65
  block: 50
```

### Waiver Configuration

Located at `devops/consistency_checker/waivers.yml`, this file defines:
- Which lint or consistency rules can be waived
- Specific files or patterns to waive
- Justification and expiration for waivers

Example:
```yaml
waivers:
  python_lint:
    - rule: E501  # Line too long
      files:
        - "legacy/*.py"
      justification: "Legacy code, will be refactored in Q3"
      expires: "2025-09-30"
```

## Using GitHub Actions

### For Developers

1. **Local Validation Before Push**:
   ```
   python devops/consistency_checker/checker.py --all
   ```

2. **After Push**:
   - Check GitHub Actions tab for build status
   - Address any issues created by the branch-lint-check workflow

3. **When Creating a PR**:
   - Use descriptive title and link to issue
   - Monitor PR validation workflow progress
   - Address feedback from validation checks

### For Maintainers

1. **Modifying Workflows**:
   - Edit workflow files in `.github/workflows/`
   - Test changes in a feature branch before merging to main

2. **Managing Test Configuration**:
   - Update `.github/pr-test-config.yml` to adjust test weights or thresholds
   - Use `python devops/release_automation/test-config-manager.py` to validate configuration

3. **Managing Waivers**:
   - Review and approve waiver requests in `devops/consistency_checker/waivers.yml`
   - Ensure all waivers have proper justification and expiration dates

## Troubleshooting GitHub Actions

### Common Issues

1. **Workflow Failures**:
   - Check specific step that failed
   - Review logs for detailed error messages
   - Verify that all dependencies are properly installed

2. **Configuration Problems**:
   - Validate YAML syntax in configuration files
   - Check for correct indentation and structure
   - Use the test-config-manager to validate PR test configuration

3. **Waiver Issues**:
   - Ensure waiver format is correct
   - Check that file patterns match the intended files
   - Verify that waiver hasn't expired

### Getting Help

For assistance with GitHub Actions:
1. Check this documentation first
2. Review workflow and action YAML files for inline comments
3. Contact the DevOps team if issues persist

## Best Practices

1. **Keep Actions Up to Date**: Regularly update action versions
2. **Use Composite Actions**: Create reusable components for common tasks
3. **Optimize Workflow Speed**: Use caching and selective testing
4. **Secure Secrets**: Never hardcode secrets in workflow files
5. **Document Changes**: Update this documentation when modifying workflows

## Reference

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [GitHub Actions Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
