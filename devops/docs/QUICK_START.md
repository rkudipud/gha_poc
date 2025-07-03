# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

This enterprise CI/CD solution provides automated code quality checks, security scanning, and intelligent PR validation for large development teams.

### Prerequisites
- Git repository on GitHub
- Python 3.11+ installed
- Basic familiarity with Git workflows

### Step 1: Setup
```bash
# Clone your repository
git clone <your-repo-url>
cd <your-repo>

# Run interactive setup
python devops/release_automation/setup.py

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Waivers (Optional)
Edit `devops/consistency_checker/waivers.yml` to add any lint exceptions:

```yaml
rule_waivers:
  - file: "special_module.py"
    rule: "E501"  # Line too long
    reason: "Module with long configuration strings"
    approved_by: "tech-lead@company.com"
    expires: "2025-12-31"
```

### Step 3: Your First Feature
```bash
# Create a feature branch
python devops/release_automation/git-helper.py create-branch --type feature --issue 123 --description "add-new-feature"

# Make your changes
# Edit files...

# Run local checks before committing (recommended)
python devops/consistency_checker/checker.py

# Commit and push
python devops/release_automation/git-helper.py commit-push --message "Add new feature"

# Create PR when ready
python devops/release_automation/git-helper.py create-pr --title "Add new feature"
```

### Step 4: Monitor & Merge
- CI automatically runs lint checks on your branch
- Issues are created/updated automatically if problems found
- **NEW**: Modular PR validation runs configurable test suites with scoring
- Hard checks must pass (security, compliance) - failure blocks PR
- Soft checks contribute to overall score (linting, coverage, docs)
- Auto-merge happens if score ≥ threshold (default 85%)

## 📋 Daily Commands

### Local Development
```bash
# Check all consistency rules
python devops/consistency_checker/checker.py

# Check specific rule with auto-fix
python devops/consistency_checker/checker.py --rule python_imports --fix

# Generate detailed report
python devops/consistency_checker/checker.py --report-format html --output-file report.html

# List available rules
python devops/consistency_checker/checker.py --list-rules
```

### Git Operations (via helper)
```bash
# Create branch
python devops/release_automation/git-helper.py create-branch --type feature --issue 456 --description "fix-bug"

# Check CI status
python devops/release_automation/git-helper.py check-status

# Sync with main branch
python devops/release_automation/git-helper.py sync-main

# Create PR
python devops/release_automation/git-helper.py create-pr --title "Fix critical bug"
```

### Traditional Git (also works)
```bash
git checkout -b feature/issue-789-improvement
git add .
git commit -m "Improve performance"
git push origin feature/issue-789-improvement
# CI runs automatically
```

### Modular Test Management
```bash
# List all configured tests
python devops/release_automation/test-config-manager.py list

# Validate configuration
python devops/release_automation/test-config-manager.py validate

# Add a new soft check test
python devops/release_automation/test-config-manager.py add-test my_test "My Custom Test" --weight 15 --action-path .github/actions/my-test

# Add a new hard check test  
python devops/release_automation/test-config-manager.py add-test security_audit "Security Audit" --enforcement hard --action-path .github/actions/security-audit

# Set scoring thresholds
python devops/release_automation/test-config-manager.py set-thresholds --auto-merge 90 --manual-review 70

# Remove a test
python devops/release_automation/test-config-manager.py remove-test old_test
```

## 🔧 Configuration Files

### Main Files
- `devops/consistency_checker/waivers.yml` - All lint exceptions and waivers
- `devops/consistency_checker/checker_config.yml` - Local checker configuration
- `.github/pr-test-config.yml` - Modular test suite configuration
- `requirements.txt` - Python dependencies
- `.github/workflows/` - CI/CD pipeline definitions

### Key Settings
- **Waiver Management**: All in `devops/consistency_checker/waivers.yml`
- **Test Configuration**: Hard/soft checks, weights, and thresholds in `.github/pr-test-config.yml`
- **Branch Protection**: Configured in GitHub repository settings
- **Issue Tracking**: Uses GitHub Issues (no external tools needed)

## ⚙️ Modular Test Configuration

### Understanding Test Types
The new modular framework supports two types of checks:

**Hard Checks** (Must Pass):
- Security critical vulnerabilities
- License compliance
- Branch protection compliance
- Failure blocks PR regardless of other scores

**Soft Checks** (Contribute to Score):
- Python linting (25% weight)
- Code coverage (20% weight)  
- Security scan non-critical (15% weight)
- Documentation quality (15% weight)
- Performance tests (10% weight)
- Consistency rules (10% weight)
- Integration tests (5% weight)

### Configuring Test Thresholds
Edit `.github/pr-test-config.yml`:

```yaml
global_config:
  auto_merge_threshold: 85    # Score >= 85% = Auto-merge
  manual_review_threshold: 65 # Score 65-84% = Manual review
  block_threshold: 64         # Score <= 64% = Block merge
```

### Adding New Tests
```yaml
test_suite:
  - id: "my_custom_test"
    name: "Custom Quality Check"
    weight: 15                # Percentage weight for scoring
    enforcement: "soft"       # "hard" or "soft"
    action_path: ".github/actions/my-custom-test"
    timeout_minutes: 10
    inputs:
      custom_param: "value"
    outputs_required:
      - test_score
```

### Environment-Specific Settings
```yaml
environment_overrides:
  production:
    global_config:
      auto_merge_threshold: 90  # Stricter for production
  development:
    global_config:
      auto_merge_threshold: 75  # More lenient for dev
```

## 🛠️ Troubleshooting

### Common Issues

**1. Lint failures on push:**
```bash
# Run local checks first
python devops/consistency_checker/checker.py --rule python_imports --fix
# Address any remaining issues or add waivers
```

**2. CI not running:**
- Ensure `.github/workflows/` files are in main branch
- Check GitHub Actions is enabled in repository settings

**3. Permission issues:**
- Ensure branch protection rules are configured
- Verify GitHub token has necessary permissions

**4. Need to add waiver:**
```bash
# Run linting to get exact error
python devops/consistency_checker/checker.py --rule python_imports

# Copy the violation line and add to devops/consistency_checker/waivers.yml
```

**5. Test suite configuration issues:**
```bash
# Validate test configuration
python -c "import yaml; yaml.safe_load(open('.github/pr-test-config.yml'))"

# Check test weights sum to 100%
grep -A 20 "test_suite:" .github/pr-test-config.yml | grep "weight:" | awk '{sum+=$2} END {print "Total weight:", sum"%"}'
```

### Getting Help
1. Check the documentation in `devops/docs/` for detailed architecture
2. Review `README.md` for complete feature list
3. Check GitHub Issues for known problems
4. Run `python devops/release_automation/git-helper.py --help` for command options

## 🎯 Best Practices

### Development Workflow
1. **Always run local checks before committing**
2. **Use descriptive branch names with issue numbers**
3. **Add waivers only when necessary with proper justification**
4. **Keep commits small and focused**
5. **Review CI feedback and fix issues promptly**

### Waiver Management
1. **Use specific waivers instead of blanket exemptions**
2. **Always include expiration dates**
3. **Get proper approval from tech leads**
4. **Document clear reasons for exceptions**
5. **Regularly review and clean up expired waivers**

### Team Collaboration
1. **Use GitHub Issues for tracking**
2. **Link PRs to issues for traceability**
3. **Review waiver requests in team meetings**
4. **Share CI/CD improvements with the team**

---

**Need more details?** See the complete documentation in the `devops/docs/` directory
