# DevOps Tools and CI/CD Documentation

This directory contains the CI/CD tooling, consistency checking, and release automation components for the project.

## Directory Structure

```
devops/
├── consistency_checker/      # Code consistency validation framework
│   ├── checker.py            # Main checker framework
│   ├── checker_config.yml    # Configuration
│   ├── waivers.yml           # Centralized waivers
│   └── rules/                # Pluggable rules
│
├── release_automation/       # Release and workflow automation tools
│   ├── git-helper.py         # Git workflow CLI tool
│   ├── setup.py              # Environment setup
│   └── test-config-manager.py # Test configuration manager
│
└── docs/                     # Documentation
    ├── ARCHITECTURE.md       # System architecture
    ├── CONSISTENCY_CHECKER.md # Consistency checker guide
    ├── GITHUB_ACTIONS.md     # GitHub Actions documentation
    ├── git-helper.md         # Git helper documentation
    ├── PRE_COMMIT_HOOK.md    # Pre-commit hook guide
    ├── QUICK_START.md        # Quick start guide
    ├── setup.md              # Setup script documentation
    ├── SCRIPT_USAGE.md       # Script usage guide
    ├── test-config-manager.md # Test config manager documentation
    ├── WAIVERS.md            # Waiver system documentation
    └── WORKFLOW.md           # CI/CD workflow guide
```

## Quick Links

- [Architecture Documentation](docs/ARCHITECTURE.md)
- [CI/CD Workflow Guide](docs/WORKFLOW.md)
- [Script Usage Guide](docs/SCRIPT_USAGE.md)
- [Waiver Management](docs/WAIVERS.md)
- [Consistency Checker](docs/CONSISTENCY_CHECKER.md)

## Usage

### Consistency Checker

Run the consistency checker from the repository root:

```bash
python devops/consistency_checker/checker.py
```

### Git Helper

Run the Git helper from the repository root:

```bash
python devops/release_automation/git-helper.py <command>
```

### Setup

Run the setup script from the repository root:

```bash
python devops/release_automation/setup.py
```

### Test Configuration Manager

Manage test configurations:

```bash
python devops/release_automation/test-config-manager.py <command>
```

## Configuration

- Consistency checker configuration: `devops/consistency_checker/checker_config.yml`
- Waiver configuration: `devops/consistency_checker/waivers.yml`
- Git helper configuration: `.git-helper-config.json` (in repo root)
- PR test configuration: `.github/pr-test-config.yml`
