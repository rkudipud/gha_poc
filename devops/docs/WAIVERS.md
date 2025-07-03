# Waiver Mechanism Documentation

## Overview

The waiver mechanism provides a structured way to manage exceptions to code quality rules and linting requirements. It enables teams to acknowledge certain violations that cannot be fixed immediately while maintaining visibility and accountability.

## Key Concepts

### Single Source of Truth

All waivers are managed in a single file: `consistency_checker/waivers.yml`. This provides:

- **Consistency**: Same waivers apply to local checks and CI/CD
- **Visibility**: Clear view of all exceptions in one place
- **Accountability**: Each waiver requires approval and expiration
- **Traceability**: References to issues and justifications

### Waiver Lifecycle

1. **Creation**: Developer identifies unavoidable violation
2. **Approval**: Technical lead/owner reviews and approves
3. **Implementation**: Waiver added to central file
4. **Expiration**: Waiver automatically expires after set date
5. **Resolution**: Code is eventually refactored to fix the issue

## Waiver File Structure

The `consistency_checker/waivers.yml` file contains these sections:

### 1. Global Settings

```yaml
settings:
  default_expiry_days: 90
  expiry_warning_days: 14
  max_waivers_per_file: 10
  security_critical_rules: ["S101", "S102", "B101"]
```

### 2. Rule-Based Waivers

For entire file/rule combinations:

```yaml
rule_waivers:
  - file: "src/core_module.py"
    rule: "E501"  # Line too long
    reason: "Core module with complex algorithms"
    approved_by: "tech-lead@company.com"
    expires: "2023-12-31"
    issue_reference: "issue-456"
```

### 3. Line-Specific Waivers

For exact violation instances:

```yaml
line_waivers:
  - violation_line: "src/config.py:45:80: E501 line too long (120 > 79 characters)"
    code_content: "DATABASE_URL = 'postgresql://user:password@very-long-hostname.example.com'"
    reason: "Database URL cannot be broken across lines"
    approved_by: "senior-dev@company.com"
    expires: "2023-06-30"
    issue_reference: "issue-789"
```

### 4. Bulk Waivers

Pattern-based waivers for multiple files:

```yaml
bulk_waivers:
  - pattern: "tests/**/*.py"
    rules: ["E501", "F841"]
    reason: "Test files can have longer lines and unused variables"
    approved_by: "qa-lead@company.com"
    expires: "2023-09-30"
```

### 5. Rule-Specific Waivers

Configuration for specific rule types:

```yaml
consistency_waivers:
  python_imports:
    file_waivers:
      - pattern: "src/generated/*.py"
        reason: "Generated code with non-standard imports"
        approved_by: "dev-lead@company.com"
        expires: "2023-10-15"
```

## Required Waiver Fields

Each waiver must include:

- **File/Pattern**: The file or file pattern the waiver applies to
- **Rule/Violation**: The specific rule or exact violation
- **Reason**: Detailed justification for the exception
- **Approved By**: Email/username of the approver
- **Expiration**: Date when the waiver expires
- **Issue Reference** (Optional): Link to issue tracking the permanent fix

## How to Add a Waiver

### Step 1: Identify the Violation

Run the consistency checker to find exact violation details:

```bash
python consistency_checker/checker.py
```

### Step 2: Add to Waiver File

Edit `consistency_checker/waivers.yml` and add the appropriate waiver section.

### Step 3: Get Approval

Have the waiver reviewed by a technical lead or code owner.

### Step 4: Create Issue for Permanent Fix

Create an issue to track the long-term resolution.

### Step 5: Commit and Push

Commit the updated waiver file along with your code changes.

## Waiver Validation

Waivers are validated during checks:

1. **Expiration Check**: Expired waivers are ignored
2. **Format Validation**: Waiver structure is validated
3. **Approval Verification**: Approved by field must be present
4. **Reason Check**: Reason must be non-empty and meaningful
5. **Security Rule Check**: Security-critical rules require special approval

## Best Practices

1. **Use Sparingly**: Waivers should be the exception, not the rule
2. **Be Specific**: Use line-specific waivers when possible
3. **Set Reasonable Expirations**: 3-6 months maximum
4. **Document Thoroughly**: Include detailed reasons and context
5. **Plan for Resolution**: Always create an issue for permanent fixing
6. **Regular Reviews**: Audit waivers periodically for expiration
7. **Limit per File**: Keep waivers per file below the threshold

## Integration with CI/CD

The waiver system integrates with the CI/CD pipeline:

1. **Branch Validation**: Checks respect waivers during branch checks
2. **PR Validation**: Waiver validation during PR processing
3. **Expiration Notifications**: Warnings for soon-to-expire waivers
4. **Reporting**: Waiver usage included in quality reports

## Security Considerations

Security-critical rules have special handling:

1. **Higher Approval**: Require security team approval
2. **Shorter Expiry**: Maximum 30-day expiration
3. **Extra Documentation**: More detailed justification required
4. **Review Process**: Additional review steps
5. **Notification**: Security team notified of all security waivers
