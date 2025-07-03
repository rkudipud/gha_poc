# DevOps Tools and CI/CD System

This directory contains enterprise-grade CI/CD tooling with 3 core components:

## 🎯 System Components

### 1. 🤖 GitHub Actions CI/CD
- **PR Validation**: Automated testing, security scans, quality gates
- **Branch Protection**: Lint checks on every push
- **Auto-Merge**: Intelligent merge decisions based on quality scores

### 2. 🔍 Local Consistency Checks  
- **Code Quality**: Python linting, style checks, complexity analysis
- **Security**: Local security scanning and secret detection
- **Waivers**: Managed exceptions for special cases

### 3. 🛠️ Developer Helper Scripts
- **Git Helper**: Streamlined branch creation, commits, PR management
- **Setup Tool**: Automated environment configuration
- **Config Manager**: Test configuration and validation management

## 🚀 Quick Start

```bash
# 1. Setup environment
python devops/release_automation/setup.py

# 2. Run local checks before Git operations
python devops/consistency_checker/checker.py

# 3. Use Git helper for workflow
python devops/release_automation/git_helper.py create-branch --type feature --issue 123
```

## 📁 Directory Structure

```
devops/
├── docs/                     # 📚 Complete documentation
│   └── README.md             # Main documentation hub
├── consistency_checker/      # 🔍 Local validation framework
│   ├── checker.py            # Main checker tool
│   ├── checker_config.yml    # Rules configuration
│   ├── waivers.yml           # Exception management
│   └── rules/                # Pluggable validation rules
└── release_automation/       # 🛠️ Developer productivity tools
    ├── git_helper.py         # Git workflow automation
    ├── setup.py              # Environment setup
    └── test_config_manager.py # Configuration management
```

## 📚 Documentation

**Main Documentation**: [`docs/README.md`](docs/README.md) - Complete system guide

### Quick Links
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and data flow
- **[Script Usage](docs/SCRIPT_USAGE.md)** - All helper scripts and commands  
- **[PR Validation](docs/pr-validation.md)** - PR validation system guide
- **[Consistency Checker](docs/CONSISTENCY_CHECKER.md)** - Local validation framework
- **[GitHub Actions](docs/GITHUB_ACTIONS.md)** - CI/CD configuration
- **[Waivers System](docs/WAIVERS.md)** - Exception management

## 🔗 Configuration Files

- **PR Validation**: `.github/pr-test-config.yml` - Main CI/CD configuration
- **Consistency Rules**: `devops/consistency_checker/checker_config.yml`
- **Waivers**: `devops/consistency_checker/waivers.yml`
- **Git Helper**: `.git_helper_config.json` (auto-created in repo root)

---

**📖 For complete documentation**: See [`docs/README.md`](docs/README.md)  
**🆘 For help**: Run any script with `--help` flag
