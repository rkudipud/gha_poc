# Consistency Checker Framework

## Overview

The Consistency Checker Framework is a modular, extensible system for enforcing coding standards, conventions, and quality rules across software projects. It provides a pluggable architecture where rules can be easily added, configured, and customized to meet project-specific requirements.

## Architecture

### Core Components

```
devops/consistency_checker/
├── checker.py              # Main framework engine
├── checker_config.yml      # Global configuration
├── waivers.yml             # Centralized waiver management
├── base_rule.py            # Base rule interface (NEW)
├── waiver_manager.py       # Waiver handling (NEW)
├── report_generator.py     # Report generation (NEW)
└── rules/                  # Rule implementations
    ├── rule_template/       # Template for new rules (NEW)
    ├── python_imports/
    │   ├── python_imports.py
    │   └── python_imports_waivers.yml
    ├── naming_conventions/
    │   ├── naming_conventions.py
    │   └── naming_conventions_waivers.yml
    ├── code_complexity/     # NEW
    ├── formatting/          # NEW
    ├── documentation/       # NEW
    └── security/            # NEW
```

### Rule Interface Standard

All rules must implement the standardized `BaseRule` interface:

```python
class BaseRule:
    """Base interface for all consistency rules"""
    
    def check(self, repo_root: Path) -> CheckResult:
        """Execute the rule and return results"""
        pass
    
    def fix(self, repo_root: Path, violations: List[Violation]) -> FixResult:
        """Attempt to auto-fix violations (optional)"""
        pass
    
    def get_metadata(self) -> RuleMetadata:
        """Return rule metadata and configuration"""
        pass
```

## Rule Categories

### 1. Code Quality Rules
- **Complexity Analysis**: Cyclomatic complexity, nesting depth
- **Function Size**: Maximum lines per function/method
- **Class Design**: Maximum methods per class, inheritance depth
- **Dead Code**: Unused functions, variables, imports

### 2. Formatting Rules
- **Indentation**: Consistent tabs/spaces, depth limits
- **Line Length**: Maximum characters per line
- **Whitespace**: Trailing spaces, blank line conventions
- **Bracket Placement**: Consistent brace/bracket style

### 3. Naming Conventions
- **Variable Names**: snake_case, camelCase, etc.
- **Function Names**: Consistent patterns
- **Class Names**: PascalCase, prefixes/suffixes
- **File Names**: Consistent naming patterns

### 4. Import Management
- **Import Order**: Standard library, third-party, local
- **Unused Imports**: Detection and removal
- **Wildcard Imports**: Discourage `from x import *`
- **Relative Imports**: Enforce relative/absolute patterns

### 5. Documentation Rules
- **Docstring Requirements**: Function/class documentation
- **Comment Quality**: TODO detection, outdated comments
- **API Documentation**: Public method documentation
- **Type Hints**: Enforce type annotations

### 6. Security Rules
- **Hardcoded Secrets**: Password, API key detection
- **Dangerous Functions**: eval(), exec(), shell commands
- **SQL Injection**: Dynamic query construction
- **File Permissions**: Secure file handling

### 7. Project Structure
- **Directory Organization**: Enforce folder conventions
- **File Organization**: Module structure rules
- **Dependency Management**: requirements.txt consistency
- **Configuration Files**: Format and location standards

## Waiver System

### Waiver Types

1. **Line-specific Waivers**: Target exact code lines
2. **File-pattern Waivers**: Apply to file patterns
3. **Rule-level Waivers**: Disable rules for specific contexts
4. **Bulk Waivers**: Pattern-based mass exemptions
5. **Temporary Waivers**: Time-limited exemptions

### Waiver Format Standard

```yaml
# Global waiver configuration
settings:
  default_expiry_days: 90
  require_approval_for: ["security", "critical"]
  max_waivers_per_file: 10

# Line-specific waivers
line_waivers:
  - violation_id: "python_imports:F401:src/module.py:15"
    code_content: "import logging  # Used in debug mode"
    reason: "Conditional import for debugging"
    approved_by: "senior-dev@company.com"
    expires: "2025-12-31"
    issue_reference: "TICKET-123"

# Pattern-based waivers
pattern_waivers:
  - pattern: "tests/**/*.py"
    rules: ["line_length", "unused_variables"]
    reason: "Test files have relaxed standards"
    approved_by: "qa-lead@company.com"
    
# Rule-specific waivers
rule_waivers:
  - rule: "complexity"
    scope: "legacy/**/*.py"
    threshold_override: 20  # Instead of default 10
    reason: "Legacy code refactoring in progress"
    approved_by: "tech-lead@company.com"
    expires: "2025-06-30"
```

## Configuration System

### Rule Configuration

```yaml
# checker_config.yml
settings:
  parallel_execution: true
  max_violations_per_file: 100
  output_format: "table"  # table, json, xml, html
  
rules:
  enabled: ["python_imports", "naming_conventions", "complexity"]
  disabled: ["experimental_rule"]
  
  # Rule-specific configuration
  rule_config:
    complexity:
      max_cyclomatic: 10
      max_nesting: 4
      max_function_lines: 50
      
    naming_conventions:
      variable_style: "snake_case"
      class_style: "PascalCase"
      constant_style: "UPPER_SNAKE_CASE"
      
    line_length:
      max_length: 88
      ignore_comments: true
      ignore_imports: true
```

## Usage Patterns

### Command Line Interface

```bash
# List all available rules with their status
./checker.py list-rules --verbose

# Run all enabled rules
./checker.py run-all --report-format html

# Run specific rules
./checker.py run-rule python_imports --fix

# Generate detailed report
./checker.py run-all --report-file consistency_report.html

# Waiver management
./checker.py show-waivers --expired
./checker.py validate-waivers
```

### Integration Points

1. **Pre-commit Hooks**: Run subset of fast rules
2. **CI/CD Pipeline**: Full rule execution with reporting
3. **IDE Integration**: Real-time rule execution
4. **Git Hooks**: Prevent commits with critical violations

## Rule Development Guide

### Creating a New Rule

1. **Create Rule Directory**:
   ```bash
   mkdir devops/consistency_checker/rules/my_new_rule
   ```

2. **Implement Rule Class**:
   ```python
   # my_new_rule.py
   from ..base_rule import BaseRule, CheckResult, Violation
   
   class MyNewRule(BaseRule):
       DESCRIPTION = "Checks for custom coding standards"
       VERSION = "1.0.0"
       CATEGORY = "code_quality"
       
       def check(self, repo_root: Path) -> CheckResult:
           violations = []
           # Implementation here
           return CheckResult(violations=violations)
           
       def fix(self, repo_root: Path, violations: List[Violation]) -> FixResult:
           # Optional auto-fix implementation
           pass
   ```

3. **Add Configuration**:
   ```yaml
   # my_new_rule_config.yml
   enabled: true
   severity: "error"  # error, warning, info
   auto_fix: true
   parameters:
     threshold: 10
     ignore_patterns: ["test_*.py"]
   ```

4. **Add Waiver Support**:
   ```yaml
   # my_new_rule_waivers.yml
   rule_specific_waivers:
     - pattern: "legacy/**"
       reason: "Legacy code exception"
   ```

### Rule Testing

```python
# test_my_new_rule.py
import pytest
from pathlib import Path
from ..rules.my_new_rule.my_new_rule import MyNewRule

class TestMyNewRule:
    def test_detects_violations(self):
        rule = MyNewRule()
        test_repo = Path("test_fixtures/sample_repo")
        result = rule.check(test_repo)
        assert len(result.violations) > 0
        
    def test_auto_fix_works(self):
        rule = MyNewRule()
        # Test auto-fix functionality
```

## Reporting System

### Report Formats

1. **Console Output**: Rich-formatted terminal display
2. **HTML Report**: Interactive web-based report
3. **JSON Report**: Machine-readable format
4. **XML Report**: JUnit-compatible format
5. **CSV Report**: Spreadsheet-compatible format

### Report Sections

1. **Executive Summary**: High-level statistics
2. **Rule Status**: Enabled/disabled rules and results
3. **Violation Details**: File-by-file breakdown
4. **Waiver Summary**: Applied waivers and effectiveness
5. **Trends**: Historical comparison (if available)
6. **Recommendations**: Suggested improvements

## Performance Considerations

### Optimization Strategies

1. **Parallel Execution**: Multi-threaded rule execution
2. **Incremental Checking**: Only check modified files
3. **Caching**: Cache rule results for unchanged files
4. **File Filtering**: Skip irrelevant files early
5. **Rule Prioritization**: Run fast rules first

### Scalability Features

1. **Distributed Execution**: Split rules across machines
2. **Database Storage**: Store results for large projects
3. **Incremental Reporting**: Delta reports for CI/CD
4. **Resource Management**: Memory and CPU limits

## Extension Points

### Custom Violation Types

```python
@dataclass
class SecurityViolation(Violation):
    severity_level: str  # critical, high, medium, low
    cve_reference: Optional[str]
    remediation_guide: str
```

### Custom Waiver Logic

```python
class ConditionalWaiver(WaiverRule):
    def applies(self, violation: Violation, context: dict) -> bool:
        # Custom logic for when waiver applies
        return custom_condition(violation, context)
```

### Plugin System

```python
# External rule plugins
class ExternalRulePlugin:
    def register_rules(self) -> List[BaseRule]:
        return [CustomRule1(), CustomRule2()]
```

## Best Practices

### Rule Implementation

1. **Single Responsibility**: Each rule checks one specific aspect
2. **Performance**: Minimize file system access
3. **Error Handling**: Graceful degradation on parse errors
4. **Documentation**: Clear descriptions and examples
5. **Testing**: Comprehensive test coverage

### Waiver Management

1. **Justification Required**: Every waiver needs a reason
2. **Time Limits**: Use expiration dates for temporary waivers
3. **Approval Process**: Require approval for critical rules
4. **Regular Review**: Audit waivers periodically
5. **Documentation**: Link to tickets/issues

### Configuration

1. **Environment-specific**: Different configs for dev/prod
2. **Team Standards**: Align with team coding standards
3. **Gradual Adoption**: Enable rules incrementally
4. **Version Control**: Track configuration changes
5. **Documentation**: Document configuration decisions

## Troubleshooting

### Common Issues

1. **Rule Loading Failures**: Check Python path and imports
2. **Configuration Errors**: Validate YAML syntax
3. **Performance Problems**: Profile rule execution times
4. **False Positives**: Refine rule logic or add waivers
5. **Integration Issues**: Check file permissions and paths

### Debug Mode

```bash
# Enable debug output
./checker.py run-all --debug --verbose

# Check rule loading
./checker.py list-rules --debug

# Validate configuration
./checker.py validate-config
```

## Migration Guide

### From Legacy Systems

1. **Export Existing Rules**: Convert to new format
2. **Migrate Waivers**: Update waiver syntax
3. **Update CI/CD**: Modify pipeline integration
4. **Train Team**: Document new processes
5. **Gradual Rollout**: Phase in new system

### Version Compatibility

- **Rule API**: Backward compatibility for 2 major versions
- **Configuration**: Automatic migration of old formats
- **Reports**: Support legacy report consumers
- **Waivers**: Import from various formats

## Future Enhancements

### Planned Features

1. **Machine Learning**: AI-powered rule suggestions
2. **IDE Integration**: Real-time checking in editors
3. **Cloud Integration**: Remote rule execution
4. **Metrics Dashboard**: Web-based analytics
5. **Rule Marketplace**: Community-contributed rules

### Extensibility

1. **Language Support**: Beyond Python (JavaScript, Java, etc.)
2. **Custom Outputs**: Pluggable report generators
3. **External APIs**: Integration with code quality services
4. **Webhook Support**: Real-time notifications
5. **Database Integration**: Enterprise data storage
