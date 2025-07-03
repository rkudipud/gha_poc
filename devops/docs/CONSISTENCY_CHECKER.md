# Consistency Checker Documentation

## Overview

The Consistency Checker is a modular framework for running pre-push code quality and consistency checks. It helps developers identify and fix issues locally before they reach the CI/CD pipeline, reducing pipeline failures and improving productivity.

## Features

- **Modular Rule System**: Pluggable rules for different types of checks
- **Auto-Fix Capability**: Automatic fixing for certain types of issues
- **Centralized Waivers**: Support for approved exceptions
- **Detailed Reporting**: Comprehensive violation reports
- **Selective Execution**: Run specific rules or check specific files
- **Pre-Push Integration**: Works as a Git pre-push hook

## Requirements

- Python 3.7+
- Git repository

## Usage

### Basic Usage

Run all enabled checks:
```bash
python consistency_checker/checker.py
```

### Specific Rules

Run only specified rules:
```bash
python consistency_checker/checker.py --rule python_imports --rule naming_conventions
```

### Auto-Fix Mode

Fix issues automatically when possible:
```bash
python consistency_checker/checker.py --fix
```

### Generate Report

Create HTML or JSON reports:
```bash
python consistency_checker/checker.py --report-format html --output-file report.html
```

### List Available Rules

Show all available rules:
```bash
python consistency_checker/checker.py --list-rules
```

### Check Specific Files

Check only specified files:
```bash
python consistency_checker/checker.py --files src/module1.py src/module2.py
```

## Rule System

The checker uses a pluggable rule system with rules stored in `consistency_checker/rules/`.

### Rule Structure

Each rule is a Python module that implements:

1. `check(files, options)`: Performs the check and returns violations
2. `fix(files, violations, options)`: Fixes violations (optional)
3. `get_rule_info()`: Returns rule metadata

### Available Rules

- **python_imports**: Validates Python import order and style
- **naming_conventions**: Enforces consistent naming patterns
- **line_length**: Checks for long lines that exceed limits
- **docstring_format**: Validates docstring formatting
- **file_structure**: Checks file organization and structure
- **unused_code**: Detects unused imports, variables, and functions

## Waiver System

The consistency checker supports a centralized waiver system that allows teams to exclude certain violations from reporting.

### Waiver File

Waivers are defined in `consistency_checker/waivers.yml`:

```yaml
# Rule-based waivers
rule_waivers:
  - file: "src/legacy_module.py"
    rule: "E501"  # Line too long
    reason: "Legacy module with complex algorithms"
    approved_by: "tech-lead@company.com"
    expires: "2023-12-31"

# Line-specific waivers
line_waivers:
  - violation_line: "src/config.py:45:80: E501 line too long (120 > 79 characters)"
    code_content: "DATABASE_URL = 'postgresql://user:password@very-long-hostname'"
    reason: "URL cannot be broken across lines"
    approved_by: "senior-dev@company.com"
    expires: "2023-06-30"

# Bulk waivers
bulk_waivers:
  - pattern: "tests/**/*.py"
    rules: ["E501", "F841"]
    reason: "Test files can have longer lines and unused variables"
    approved_by: "qa-lead@company.com"
```

### Waiver Types

1. **Rule Waivers**: Apply to an entire file for a specific rule
2. **Line Waivers**: Apply to specific violation instances
3. **Bulk Waivers**: Apply to multiple files matching a pattern
4. **Consistency Waivers**: Rule-specific configuration

## Configuration

Configure the checker in `consistency_checker/checker_config.yml`:

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

## Integration with Git

Add as a pre-push hook by adding to `.git/hooks/pre-push`:

```bash
#!/bin/sh
python consistency_checker/checker.py
if [ $? -ne 0 ]; then
  echo "Consistency check failed. Please fix the issues before pushing."
  exit 1
fi
```

## Relationship to CI/CD

The consistency checker runs the same checks as the CI/CD pipeline but locally:

1. **Early Feedback**: Catch issues before pushing
2. **Same Standards**: Enforces the same rules as the pipeline
3. **Shared Waivers**: Uses the same waiver system as CI/CD
4. **Local Auto-Fix**: Automatically fix issues that would fail in CI

## Best Practices

1. **Run Before Committing**: Check code before finalizing changes
2. **Use Auto-Fix**: Let the tool fix simple issues automatically
3. **Keep Waivers Minimal**: Only waive violations when absolutely necessary
4. **Add Expiration Dates**: All waivers should have expiration dates
5. **Document Reasons**: Always include detailed reasons for waivers
