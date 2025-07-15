# Validation System

This document covers the complete validation framework including consistency checking, waivers, GitHub Actions, and PR validation.

## Overview

The validation system provides comprehensive code quality and consistency checks across multiple layers:

- **Local Validation**: Consistency checker and pre-commit hooks
- **Branch Validation**: Automated checks on feature branch pushes
- **PR Validation**: Comprehensive scoring and automated decision-making
- **Waiver System**: Centralized exception management

---

## 🔍 Consistency Checker Framework

### Features

- **Modular Rule System**: Pluggable rules for different types of checks
- **Auto-Fix Capability**: Automatic fixing for certain types of issues
- **Centralized Waivers**: Support for approved exceptions
- **Detailed Reporting**: Comprehensive violation reports
- **Selective Execution**: Run specific rules or check specific files
- **Pre-Push Integration**: Works as a Git pre-push hook

### Requirements

- Python 3.7+
- Git repository

### Usage Examples

```bash
# Basic usage - run all enabled checks
python devops/consistency_checker/checker.py

# Run specific rules
python devops/consistency_checker/checker.py --rule python_imports --rule naming_conventions

# Auto-fix mode
python devops/consistency_checker/checker.py --fix

# Generate reports
python devops/consistency_checker/checker.py --report-format html --output-file report.html

# List available rules
python devops/consistency_checker/checker.py --list-rules

# Check specific files
python devops/consistency_checker/checker.py --files src/module1.py src/module2.py
```

### Available Rules

- **python_imports**: Validates Python import order and style
- **naming_conventions**: Enforces consistent naming patterns
- **line_length**: Checks for long lines that exceed limits
- **docstring_format**: Validates docstring formatting
- **file_structure**: Checks file organization and structure
- **unused_code**: Detects unused imports, variables, and functions

---

## 📋 Waiver System

### Overview

The waiver mechanism provides a structured way to manage exceptions to code quality rules and linting requirements. It enables teams to acknowledge certain violations that cannot be fixed immediately while maintaining visibility and accountability.

### Key Concepts

#### Single Source of Truth

All waivers are managed in a single file: `devops/consistency_checker/waivers.yml`. This provides:

- **Consistency**: Same waivers apply to local checks and CI/CD
- **Visibility**: Clear view of all exceptions in one place
- **Accountability**: Each waiver requires approval and expiration
- **Traceability**: References to issues and justifications

#### Waiver Lifecycle

1. **Creation**: Developer identifies unavoidable violation
2. **Approval**: Technical lead/owner reviews and approves
3. **Implementation**: Waiver added to central file
4. **Expiration**: Waiver automatically expires after set date
5. **Resolution**: Code is eventually refactored to fix the issue

### Waiver File Structure

The `devops/consistency_checker/waivers.yml` file contains these sections:

#### 1. Global Settings

```yaml
settings:
  default_expiry_days: 90
  expiry_warning_days: 14
  max_waivers_per_file: 10
  security_critical_rules: ["S101", "S102", "B101"]
```

#### 2. Rule-Based Waivers

For entire file/rule combinations:

```yaml
rule_waivers:
  - file: "src/core_module.py"
    rule: "E501"  # Line too long
    reason: "Core module with complex algorithms"
    approved_by: "tech-lead@company.com"
    expires: "2025-12-31"
    issue_reference: "issue-456"
```

#### 3. Line-Specific Waivers

For exact violation instances:

```yaml
line_waivers:
  - violation_line: "src/config.py:45:80: E501 line too long (120 > 79 characters)"
    code_content: "DATABASE_URL = 'postgresql://user:password@very-long-hostname.example.com'"
    reason: "Database URL cannot be broken across lines"
    approved_by: "senior-dev@company.com"
    expires: "2025-06-30"
    issue_reference: "issue-789"
```

#### 4. Bulk Waivers

Pattern-based waivers for multiple files:

```yaml
bulk_waivers:
  - pattern: "tests/**/*.py"
    rules: ["E501", "F841"]
    reason: "Test files can have longer lines and unused variables"
    approved_by: "qa-lead@company.com"
    expires: "2025-09-30"
```

#### 5. Rule-Specific Waivers

Configuration for specific rule types:

```yaml
consistency_waivers:
  python_imports:
    file_waivers:
      - pattern: "src/generated/*.py"
        reason: "Generated code with non-standard imports"
        approved_by: "dev-lead@company.com"
        expires: "2025-10-15"
```

### Required Waiver Fields

Each waiver must include:

- **File/Pattern**: The file or file pattern the waiver applies to
- **Rule/Violation**: The specific rule or exact violation
- **Reason**: Detailed justification for the exception
- **Approved By**: Email/username of the approver
- **Expiration**: Date when the waiver expires
- **Issue Reference** (Optional): Link to issue tracking the permanent fix

### How to Add a Waiver

#### Step 1: Identify the Violation

Run the consistency checker to find exact violation details:

```bash
python devops/consistency_checker/checker.py
```

#### Step 2: Add to Waiver File

Edit `devops/consistency_checker/waivers.yml` and add the appropriate waiver section.

#### Step 3: Get Approval

Have the waiver reviewed by a technical lead or code owner.

#### Step 4: Create Issue for Permanent Fix

Create an issue to track the long-term resolution.

#### Step 5: Commit and Push

Commit the updated waiver file along with your code changes.

### Waiver Validation

Waivers are validated during checks:

1. **Expiration Check**: Expired waivers are ignored
2. **Format Validation**: Waiver structure is validated
3. **Approval Verification**: Approved by field must be present
4. **Reason Check**: Reason must be non-empty and meaningful
5. **Security Rule Check**: Security-critical rules require special approval

### Security Considerations

Security-critical rules have special handling:

1. **Higher Approval**: Require security team approval
2. **Shorter Expiry**: Maximum 30-day expiration
3. **Extra Documentation**: More detailed justification required
4. **Review Process**: Additional review steps
5. **Notification**: Security team notified of all security waivers

---

## 🚀 GitHub Actions Integration

### Workflow Structure

The GitHub Actions are organized into workflows, reusable actions, and configuration:

#### Workflows (`.github/workflows/`)
- **branch-lint-check.yml**: Triggered on push to feature branches
- **pr-validation.yml**: Triggered on PR creation and updates

#### Reusable Actions (`.github/actions/`)
- **python-lint/**: Python linting with waiver support
- **consistency-check/**: Code consistency validation
- **security-scan/**: Security vulnerability and secret scanning
- **coverage-check/**: Test coverage analysis and reporting
- **docs-check/**: Documentation quality validation
- **branch-protection-check/**: Branch protection compliance verification
- **test-orchestrator/**: Centralized test execution coordination
- **email-notification/**: Result notification system

#### Configuration (`.github/`)
- **pr-test-config.yml**: Master test configuration for PR validation

### Workflow Flows

#### Branch Lint Check Flow

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

#### PR Validation Flow

```
PR Creation/Update → pr-validation.yml → Config Loading → Hard Checks → Soft Checks → Score Calculation → Decision
```

1. **Trigger**: Activated on PR creation, updates, or review submissions
2. **Process**:
   - Loads test configuration from `.github/pr-test-config.yml`
   - Runs hard (must-pass) checks first
   - Runs soft (scored) checks
   - Calculates overall score
   - Makes decision: auto-merge, request review, or block

### Configuration Files

#### PR Test Configuration

Located at `.github/pr-test-config.yml`, this file configures:
- Which tests to run and their enforcement type (hard vs soft)
- Weight of each test in the overall score
- Thresholds for auto-merge, review, and blocking
- Environment-specific overrides
- Test timeouts and execution parameters

Example:
```yaml
global_config:
  auto_merge_threshold: 85
  manual_review_threshold: 65
  block_threshold: 64
  parallel_execution: true

test_suite:
  - id: "security_critical"
    name: "Critical Security Scan"
    enforcement: "hard"
    weight: 0
    enabled: true
    timeout_minutes: 15
  
  - id: "python_lint"
    name: "Python Code Quality"
    enforcement: "soft"
    weight: 25
    enabled: true
    timeout_minutes: 10
```

#### Waiver Configuration

Located at `devops/consistency_checker/waivers.yml`, this file defines:
- Which lint or consistency rules can be waived
- Specific files or patterns to waive
- Justification and expiration for waivers

### Using GitHub Actions

#### For Developers

1. **Local Validation Before Push**:
   ```bash
   python devops/consistency_checker/checker.py --all
   ```

2. **After Push**:
   - Check GitHub Actions tab for build status
   - Address any issues created by the branch-lint-check workflow

3. **When Creating a PR**:
   - Use descriptive title and link to issue
   - Monitor PR validation workflow progress
   - Address feedback from validation checks

#### For Maintainers

1. **Modifying Workflows**:
   - Edit workflow files in `.github/workflows/`
   - Test changes in a feature branch before merging to main

2. **Managing Test Configuration**:
   - Update `.github/pr-test-config.yml` to adjust test weights or thresholds
   - Use `python devops/release_automation/test_config_manager.py` to validate configuration

3. **Managing Waivers**:
   - Review and approve waiver requests in `devops/consistency_checker/waivers.yml`
   - Ensure all waivers have proper justification and expiration dates

---

## 🎯 PR Validation System

### Overview

The Modular PR Validation System is a comprehensive, configuration-driven approach to validating pull requests. It provides automated scoring, intelligent decision-making, and flexible test execution based on configurable rules.

### Key Features

- **Configuration-Driven**: All tests and thresholds defined in `pr-test-config.yml`
- **Hard vs Soft Checks**: Critical checks that must pass vs scoring-based checks
- **Auto-Merge Decision**: Intelligent merge decisions based on configurable thresholds
- **Modular Architecture**: Reusable components and easy maintenance
- **Parallel Execution**: Optimized performance where possible
- **Comprehensive Reporting**: Detailed feedback with actionable insights

### Architecture

#### 1. Configuration Validation
- Loads and validates `pr-test-config.yml`
- Detects test environment based on PR characteristics
- Separates hard checks from soft checks

#### 2. Hard Checks (Must Pass)
These checks must pass for the PR to be mergeable:
- **Security Critical**: High-severity security vulnerabilities
- **Syntax Validation**: Python syntax errors
- **Custom Hard Checks**: Environment-specific requirements

#### 3. Soft Checks (Scoring)
These checks contribute to the overall score:
- **Code Quality**: Linting, complexity, coverage
- **Security Scan**: Medium/low security issues
- **Testing**: Unit, integration, smoke tests
- **Documentation**: Docstring coverage, README updates
- **Compliance**: License headers, naming conventions

#### 4. Decision Making
Based on the final score:
- **≥85%**: Auto-merge approved
- **65-84%**: Manual review required
- **≤64%**: Merge blocked

### Naming Convention Standards

To ensure consistency across the codebase, follow these naming conventions:

#### Python Code
- **Variables and Functions**: `snake_case`
  ```python
  user_name = "john_doe"
  def calculate_total_score():
      pass
  ```

- **Classes**: `PascalCase`
  ```python
  class UserManager:
      pass
  ```

- **Constants**: `UPPER_SNAKE_CASE`
  ```python
  MAX_RETRY_COUNT = 3
  DEFAULT_TIMEOUT = 30
  ```

#### GitHub Actions
- **Job Names**: `snake_case`
  ```yaml
  validate_configuration:
  execute_hard_checks:
  ```

- **Step Names**: Descriptive sentences
  ```yaml
  - name: Checkout repository
  - name: Execute hard checks
  ```

- **Environment Variables**: `snake_case`
  ```yaml
  env:
    pr_number: ${{ github.event.pull_request.number }}
    base_branch: ${{ github.event.pull_request.base.ref }}
  ```

### Current Implementation

**pr-validation.yml** - Main validation workflow using modular approach
- **Purpose**: Primary PR validation workflow for the repository
- **Features**: Configuration-driven, hard/soft checks, auto-merge decisions
- **Location**: `.github/workflows/pr-validation.yml`
- **Configuration**: Uses `.github/pr-test-config.yml` for test definitions and scoring
- **Use Case**: Standard PR validation for all pull requests

This workflow integrates with:
- **branch-lint-check.yml**: Pre-PR validation on feature branches
- **devops/consistency_checker**: Local and CI code quality validation
- **devops/release_automation**: Git workflow automation tools

### Usage

#### Enabling PR Validation

1. Ensure `pr-test-config.yml` exists in `.github/`
2. Configure thresholds and test suite
3. The workflow automatically triggers on PR events

#### Customizing Checks

Add new checks to `pr-test-config.yml`:

```yaml
- id: "custom_check"
  name: "Custom Validation"
  description: "Project-specific validation"
  weight: 10
  enforcement: "soft"
  timeout_minutes: 5
```

#### Environment-Specific Configuration

The system detects environments based on:
- PR title keywords (`hotfix`, `emergency`)
- PR labels (`performance`, `security`)
- Branch patterns

---

## 🔧 Troubleshooting

### Common Issues

1. **Consistency Check Failures**
   - Run local checker to see exact violations
   - Check if waiver is properly formatted and not expired
   - Verify file paths match the waiver patterns

2. **GitHub Actions Failures**
   - Check workflow logs for detailed error messages
   - Verify configuration file syntax
   - Ensure all required secrets are set

3. **PR Validation Issues**
   - **Hard Check Failures**: Must be fixed before merge
   - **Low Scores**: Address individual test failures to improve score
   - **Configuration Problems**: Verify `pr-test-config.yml` format and values

4. **Waiver Issues**
   - Ensure waiver format is correct
   - Check that file patterns match the intended files
   - Verify that waiver hasn't expired
   - Confirm approval is present

### Getting Help

1. Review workflow logs for detailed error messages
2. Check the PR comment for specific failure details
3. Consult team documentation or reach out to DevOps

---

## 💡 Best Practices

### For Developers

1. **Before Creating PR**:
   - Run local linting and tests
   - Ensure proper naming conventions
   - Add tests for new features
   - Update documentation as needed

2. **PR Description**:
   - Include clear description of changes
   - Add appropriate labels
   - Link to related issues

3. **Addressing Failures**:
   - Fix hard check failures first
   - Improve scores systematically
   - Don't bypass checks without justification

### For Maintainers

1. **Configuration Updates**:
   - Test changes in feature branch first
   - Document threshold modifications
   - Communicate changes to team

2. **Adding New Checks**:
   - Start with soft checks for feedback
   - Gradually increase weights
   - Monitor impact on development velocity

3. **Waiver Management**:
   - Review waiver requests carefully
   - Ensure proper justification and expiration
   - Track waiver resolution progress

### Integration Best Practices

1. **Run Local Checks**: Always run consistency checker before pushing
2. **Keep Waivers Minimal**: Only waive violations when absolutely necessary
3. **Add Expiration Dates**: All waivers should have expiration dates
4. **Document Reasons**: Always include detailed reasons for waivers
5. **Use Updated Paths**: Always use the correct paths in the `devops` directory

---

**Integration Points**: This validation system integrates seamlessly with the broader CI/CD pipeline, providing comprehensive quality assurance from local development through production deployment.
