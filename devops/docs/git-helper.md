# Git Helper Documentation

## Overview

The `git-helper.py` script provides a simplified interface for developers to work with the enterprise CI/CD pipeline without needing deep Git knowledge. It streamlines common Git operations with best practices baked in, ensuring consistent branch naming, proper commit messages, and adherence to workflow standards.

## Features

- **Branch Management**: Create, switch, and sync branches following naming conventions
- **Commit Workflow**: Stage, commit, and push changes with standardized messages
- **PR Operations**: Create, update, and monitor pull requests
- **Status Checking**: Verify pipeline status and get feedback on failures
- **Conflict Resolution**: Tools to handle merge conflicts efficiently

## Requirements

- Python 3.7+
- Git client installed and configured
- Repository with proper `.git-helper-config.json` configuration

## Configuration

Git Helper uses a configuration file `.git-helper-config.json` in the repository root with the following structure:

```json
{
  "github": {
    "owner": "organization-name",
    "repo": "repository-name",
    "token": "" // Can be set via GITHUB_TOKEN environment variable
  },
  "issue_tracking": {
    "use_github_issues": true,
    "issue_prefix": "GH"
  },
  "branch_naming": {
    "feature": "feature/{issue}-{description}",
    "bugfix": "bugfix/{issue}-{description}",
    "hotfix": "hotfix/{issue}-{description}"
  },
  "main_branch": "main",
  "protected_branches": ["main", "develop", "release/*"]
}
```

## Command Reference

### Branch Management

#### Create Branch
```bash
python git-helper.py create-branch --type feature --issue 123 --description "add-new-feature"
```

- **Options**:
  - `--type`: Branch type (feature, bugfix, hotfix)
  - `--issue`: Issue tracker ID (optional)
  - `--description`: Brief description for branch name

#### Sync with Main
```bash
python git-helper.py sync-main
```
Updates current branch with latest changes from main branch

### Commit Operations

#### Commit and Push
```bash
python git-helper.py commit-push --message "Implement awesome feature"
```

- **Options**:
  - `--message`: Commit message
  - `--files`: Specific files to commit (optional, commits all changes by default)

#### Amend Commit
```bash
python git-helper.py amend-commit --message "Updated implementation"
```

### Pull Request Operations

#### Create PR
```bash
python git-helper.py create-pr --title "Add awesome feature" --body "Implements feature X for project Y"
```

- **Options**:
  - `--title`: PR title
  - `--body`: PR description (optional)
  - `--draft`: Create as draft PR (optional)

#### Check PR Status
```bash
python git-helper.py check-pr-status
```

### Troubleshooting

#### Check Status
```bash
python git-helper.py check-status
```
Shows current status of branch and any pipeline failures

#### Resolve Conflicts
```bash
python git-helper.py resolve-conflicts
```
Interactive conflict resolution helper

## Best Practices

1. **Always create branches** using git-helper to ensure naming conventions
2. **Run consistency checks** before committing with `python consistency_checker/checker.py`
3. **Use descriptive commit messages** that explain the "why" not just "what"
4. **Keep PRs focused** on single issues or features
5. **Sync with main** regularly to avoid large merge conflicts

## Integration with CI/CD

Git Helper integrates seamlessly with the CI/CD pipeline:

1. Creates branches with proper naming conventions
2. Pushes changes triggering branch validation workflows
3. Creates PRs initiating the PR validation process
4. Provides status checking to monitor pipeline progress

## Troubleshooting

- **Config File Issues**: Ensure `.git-helper-config.json` exists and is valid JSON
- **GitHub API Errors**: Check if GitHub token has proper permissions
- **Branch Creation Fails**: Ensure working tree is clean before creating branches
- **Push Fails**: Make sure remote is accessible and you have push permissions
