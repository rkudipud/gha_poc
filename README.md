# Project Repository

This repository contains the main project code and associated DevOps tools for CI/CD.

## Project Components

- `pandora_tc_ext_fm.py` - Main project script
- `golden/` - Golden data for the project (preserved)
- `working/` - Working directory for project data (preserved)
- `crt.pre.install` - Critical pre-installation script for the project
- `make_venv.csh` - Script for setting up the virtual environment

## DevOps and CI/CD

The CI/CD and DevOps tools have been moved to a dedicated directory to separate them from the main project code:

```
devops/
├── consistency_checker/      # Code consistency validation framework
├── release_automation/       # Release and workflow automation tools
└── docs/                     # Documentation
```

For more information about the CI/CD components, see the [DevOps README](devops/README.md).

## Documentation

All CI/CD and tooling documentation has been moved to the `devops/docs/` directory:

- [Architecture Documentation](devops/docs/ARCHITECTURE.md)
- [CI/CD Workflow Guide](devops/docs/WORKFLOW.md)
- [Script Usage Guide](devops/docs/SCRIPT_USAGE.md)
- [Consistency Checker Documentation](devops/docs/CONSISTENCY_CHECKER.md)
- [Waivers Documentation](devops/docs/WAIVERS.md)
- [GitHub Actions Documentation](devops/docs/GITHUB_ACTIONS.md)
- [Quick Start Guide](devops/docs/QUICK_START.md)

## Using the Tools

All tools are now located in the `devops` directory and should be run from there:

### Consistency Checker
```
python devops/consistency_checker/checker.py --all
python devops/consistency_checker/checker.py --rule python_imports
python devops/consistency_checker/checker.py --list-rules
```

### Git Helper
```
python devops/release_automation/git-helper.py create-branch --type feature --issue 123 --description "add-new-feature"
python devops/release_automation/git-helper.py commit-push --message "Implement feature"
python devops/release_automation/git-helper.py create-pr --title "Add new feature"
```

### Setup Tool
```
python devops/release_automation/setup.py
```

### Test Config Manager
```
python devops/release_automation/test-config-manager.py --update pr-test-config.yml --add-test "security_scan:90"
```

## Getting Started

For a quick start guide on how to use this project, see the [Quick Start Guide](devops/docs/QUICK_START.md).

## Directory Structure

The repository has been reorganized to separate the main project code from the DevOps and CI/CD tools:

- `pandora_tc_ext_fm.py` and other project files remain at the root
- `golden/` and `working/` directories are preserved for project data
- All CI/CD and DevOps tools have been moved to the `devops/` directory
- All documentation has been moved to the `devops/docs/` directory

## Need Help?

If you need help with the CI/CD tools, check the documentation in the `devops/docs/` directory or run the specific tool with the `--help` flag.

## Important Project Files

The following files are part of the main project and not part of the CI/CD workflow:

- `pandora_tc_ext_fm.py` - Main project script
- `golden/` directory - Contains golden data for the project
- `working/` directory - Working directory for project data
- `crt.pre.install` - Critical pre-installation script
- `make_venv.csh` - Virtual environment setup script

These files should be preserved and not modified as part of any CI/CD reorganization.
