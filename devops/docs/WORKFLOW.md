# CI/CD Workflow Documentation

## Overview

This document describes the CI/CD workflow used in this project, detailing how code changes move from local development through validation to deployment.

## Workflow Stages

### 1. Local Development

Developers work locally with the following tools:

- **Git Helper**: CLI tool for branch management and workflow operations
- **Consistency Checker**: Local validation to catch issues before pushing
- **Setup Tool**: Environment and configuration management

### 2. Branch Validation

When code is pushed to a feature branch:

1. **Branch Lint Workflow Trigger**: Automatically starts on push (except to main)
2. **Smart Change Detection**: Identifies modified files for efficient processing
3. **Python Lint**: Code style and quality checks
4. **Waiver Validation**: Applies centralized waivers to filter false positives
5. **Issue Creation**: Automatically creates/updates GitHub issues for failures
6. **Notification**: Sends email or other notifications about failures

### 3. Pull Request Validation

When a pull request is created or updated:

1. **PR Validation Workflow Trigger**: Starts on PR events
2. **Config Loading**: Loads test configuration from `pr-test-config.yml`
3. **Hard Checks Execution**: Runs must-pass checks (security, branch protection)
4. **Soft Checks Execution**: Runs weighted quality checks (lint, coverage, etc.)
5. **Score Calculation**: Computes weighted score based on test results
6. **Decision**: Auto-merge, request review, or block based on score thresholds

### 4. Main Branch Protection

The main branch is protected by:

1. **Required Status Checks**: All critical checks must pass
2. **Branch Protection Rules**: No direct pushes allowed
3. **Auto-Merge Criteria**: Score ≥ 85% for automatic merge
4. **Manual Review**: Required for scores between 65-84%
5. **Blocking**: Prevents merging for scores < 65%

## Workflow Diagrams

### Branch Push Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Developer  │     │  Git Helper  │     │   GitHub        │
│  Workspace  │────►│  CLI Tool    │────►│   Repository    │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                │
                                                ▼
                                         ┌─────────────────┐
                                         │  Branch Lint    │
                                         │  Workflow       │
                                         └─────────────────┘
                                                │
                    ┌─────────────────┐        │
                    │  GitHub Issues  │◄───────┘
                    │  (If failures)  │
                    └─────────────────┘
```

### PR Validation Flow

```
┌─────────────┐     ┌────────────────┐     ┌─────────────────┐
│  Developer  │     │  Pull Request  │     │  PR Validation  │
│  Creates PR │────►│  Creation      │────►│  Workflow       │
└─────────────┘     └────────────────┘     └─────────────────┘
                                                │
                                                ▼
┌───────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Auto-Merge    │     │ Score-Based  │     │  Test Suite     │
│ Decision      │◄────┤ Evaluation   │◄────┤  Execution      │
└───────────────┘     └──────────────┘     └─────────────────┘
```

## Key Components

### 1. GitHub Workflows

- **branch-lint-check.yml**: Triggered on push to feature branches
- **pr-validation-modular.yml**: Triggered on PR events

### 2. Reusable Actions

- **python-lint-enhanced**: Enhanced Python linting with waiver support
- **security-scan**: Security vulnerability and secret scanning
- **coverage-check**: Test coverage analysis
- **consistency-check**: Code consistency validation
- **branch-protection-check**: Branch protection compliance
- **test-orchestrator**: Central test coordination

### 3. Configuration Files

- **pr-test-config.yml**: Master test configuration
- **waivers.yml**: Centralized lint and consistency waivers

## Using the Workflow

### For Developers

1. **Setup Environment**: `python devops/release_automation/setup.py` to configure tools
2. **Create Branch**: `python devops/release_automation/git_helper.py create-branch --type feature --issue 123 --description "add-feature"`
3. **Make Changes**: Develop your feature or fix
4. **Local Validation**: `python devops/consistency_checker/checker.py` to catch issues early
5. **Commit Changes**: `python devops/release_automation/git_helper.py commit-push --message "Implement feature"`
6. **Check Status**: `python devops/release_automation/git_helper.py check-status` to monitor branch validation
7. **Create PR**: `python devops/release_automation/git_helper.py create-pr --title "Add feature"`
8. **Monitor PR**: Check GitHub UI for validation progress and results

### For Maintainers

1. **Review Configuration**: Manage test weights in `.github/pr-test-config.yml`
2. **Waiver Management**: Review and approve waivers in `devops/consistency_checker/waivers.yml`
3. **Monitor Metrics**: Track pipeline health and success rates
4. **Workflow Updates**: Modify workflow files for process changes

For detailed information about GitHub Actions implementation and usage, see [GitHub Actions Documentation](GITHUB_ACTIONS.md).

## Troubleshooting

### Branch Validation Issues

- **Lint Failures**: Check exact error and fix or apply waiver if needed
- **Waiver Problems**: Verify waiver format and approval
- **Pipeline Timeouts**: Check for long-running or stuck processes

### PR Validation Issues

- **Hard Check Failures**: Must be fixed before merge
- **Low Score**: Address individual test failures to improve score
- **Configuration Problems**: Verify `pr-test-config.yml` format and values

## Best Practices

1. **Run Local Checks**: Always run consistency checker before pushing
2. **Keep PRs Focused**: Each PR should address a single concern
3. **Regular Syncing**: Keep feature branches updated with main
4. **Proper Commit Messages**: Use clear, descriptive commit messages
5. **Address All Feedback**: Fix all automated feedback before requesting review
6. **Minimal Waivers**: Use waivers only when absolutely necessary
7. **Use Updated Paths**: Always use the new paths in the `devops` directory
