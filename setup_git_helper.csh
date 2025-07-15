#!/bin/tcsh
# Git Helper Setup Script for tcsh users
# Run this script to set up git-helper in your PATH for the current session

set REPO_ROOT = "/nfs/site/disks/ddi_r2g_14/rkudipud/gha_poc"

# Make git-helper executable
chmod +x "$REPO_ROOT/bin/git-helper"

# Add to PATH for current session
setenv PATH "$REPO_ROOT/bin:${PATH}"

# Verify installation
echo "✅ Git helper setup complete!"
echo "📍 Location: $REPO_ROOT/bin/git-helper"
echo "🔍 Testing git-helper command..."

if ( -x "$REPO_ROOT/bin/git-helper" ) then
    echo "✅ git-helper is executable and ready to use"
    echo ""
    echo "Available commands:"
    git-helper --help | grep -A 20 "Commands"
else
    echo "❌ Error: git-helper setup failed"
endif

echo ""
echo "💡 To make this permanent, add this line to your shell config:"
echo "   setenv PATH \"$REPO_ROOT/bin:\${PATH}\""
