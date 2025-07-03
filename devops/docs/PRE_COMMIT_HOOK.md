# Pre-commit Hook Guide

The pre-commit hook in this repository helps maintain code quality by automatically checking for:

1. Python syntax errors
2. Large files (>10MB)
3. Potential secrets in the code

## Features

- **Adaptive Python Interpreter Detection**: The hook automatically finds the available Python interpreter (`python3`, `python`, or `python2`).
- **Smart Secret Detection**: Reduces false positives when detecting potential secrets.
- **Graceful Degradation**: If no Python interpreter is available, the hook will skip Python syntax checks.

## Bypassing the Pre-commit Hook

In cases where you need to bypass the pre-commit hook (for example, when you have a false positive for secret detection), you can set the `GIT_SKIP_VERIFY` environment variable:

```bash
# For tcsh shell
setenv GIT_SKIP_VERIFY 1
git commit -m "Your commit message"
unsetenv GIT_SKIP_VERIFY  # Don't forget to unset after use
```

```bash
# For bash/sh
GIT_SKIP_VERIFY=1 git commit -m "Your commit message"
```

## When Secret Detection is Triggered



## Recommendations

- **Never commit actual secrets**: Use environment variables or secure vaults
- **Review carefully**: When the hook flags a potential secret, carefully review if it's actually sensitive
- **Bypass only when necessary**: Only use `GIT_SKIP_VERIFY=1` when you're certain there are no real secrets

## Troubleshooting

If you encounter issues with the pre-commit hook:

1. Check if the correct Python interpreter is available in your environment
2. Ensure the hook is executable (`chmod +x .git/hooks/pre-commit`)
3. For persistent false positives, consider updating the regex pattern in `.git/hooks/pre-commit`
