# Test Configuration Manager Documentation

## Overview

The `test-config-manager.py` script provides a command-line interface for managing the modular test framework configuration. It allows developers and CI administrators to add, modify, and validate test configurations for the PR validation pipeline.

## Features

- **Configuration Management**: Add, remove, and modify test configurations
- **Weight Management**: Adjust test weights and scoring thresholds
- **Validation**: Ensure configuration correctness and total weight consistency
- **Reporting**: Generate configuration reports and validation summaries
- **Schema Enforcement**: Validate configuration against schema requirements

## Requirements

- Python 3.7+
- Write access to `.github/pr-test-config.yml`

## Usage

```bash
python test-config-manager.py <command> [options]
```

## Commands

### List Tests

```bash
python test-config-manager.py list-tests
```

Displays all configured tests with their weights, enforcement levels, and status.

### Add Test

```bash
python test-config-manager.py add-test --id "python_lint" --name "Python Linting" --weight 25 --enforcement "soft"
```

- **Options**:
  - `--id`: Unique test identifier
  - `--name`: Human-readable test name
  - `--weight`: Percentage weight (for soft checks)
  - `--enforcement`: "hard" or "soft"
  - `--action-path`: Path to GitHub Action
  - `--enabled`: Whether test is enabled (true/false)

### Remove Test

```bash
python test-config-manager.py remove-test --id "python_lint"
```

Removes a test from the configuration.

### Update Test

```bash
python test-config-manager.py update-test --id "python_lint" --weight 30 --enabled true
```

Updates an existing test configuration.

### Set Threshold

```bash
python test-config-manager.py set-threshold --auto-merge 85 --manual-review 65 --block 64
```

Sets scoring thresholds for PR decision making.

### Validate Config

```bash
python test-config-manager.py validate
```

Validates the entire configuration for correctness.

### Generate Report

```bash
python test-config-manager.py generate-report [--format json|yaml|md]
```

Generates a detailed report of the test configuration.

## Configuration Structure

The configuration is stored in `.github/pr-test-config.yml` with the following structure:

```yaml
global_config:
  auto_merge_threshold: 85
  manual_review_threshold: 65
  block_threshold: 64
  max_test_timeout: 30
  parallel_execution: true

test_suite:
  - id: "python_lint_enhanced"
    name: "Python Linting"
    description: "Code style and quality check"
    weight: 25
    enforcement: "soft"
    action_path: ".github/actions/python-lint-enhanced"
    enabled: true
    
  - id: "security_critical"
    name: "Security Scan"
    description: "Critical vulnerability detection"
    weight: 0
    enforcement: "hard"
    action_path: ".github/actions/security-scan"
    enabled: true
```

## Test Types

### Hard Checks

Hard checks must pass for a PR to be mergeable. They have no weight contribution.

Example configuration:
```yaml
- id: "security_critical"
  name: "Security Scan"
  enforcement: "hard"
  weight: 0
  enabled: true
```

### Soft Checks

Soft checks contribute to the overall score based on their weight.

Example configuration:
```yaml
- id: "python_lint_enhanced"
  name: "Python Linting"
  enforcement: "soft"
  weight: 25
  enabled: true
```

## Validation Rules

The manager enforces these validation rules:

1. Total weights must sum to 100% (for enabled soft checks)
2. Test IDs must be unique
3. Hard checks must have 0 weight
4. Soft checks must have positive weights
5. Thresholds must be in the range 0-100

## Integration with PR Workflow

The configuration is used by:

1. **PR Validation Workflow**: Determines which tests to run
2. **Test Orchestrator**: Calculates scores and makes decisions
3. **GitHub Status Checks**: Reports individual test results

## Best Practices

1. **Balance Weights**: Distribute weights according to test importance
2. **Set Realistic Thresholds**: Consider team maturity and code quality goals
3. **Start with Fewer Hard Checks**: Use soft checks until team adjusts
4. **Review Regularly**: Update weights and thresholds based on team feedback
5. **Document Changes**: Keep a changelog of configuration updates
