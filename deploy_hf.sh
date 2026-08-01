#!/usr/bin/env bash
# deploy_hf.sh — Deploy SB AI Assistant to Hugging Face Spaces.
#
# Product Intent:
#   Hugging Face Spaces rejects binary files (e.g. UI_demo.png) in git
#   history.  This script creates a clean orphan branch that excludes binary
#   files and internal docs, injects HF Spaces YAML metadata into README.md,
#   then force-pushes to the `space` remote's main branch.  The local main
#   branch (with UI_demo.png and a clean README.md for GitHub) is never
#   modified.
#
# Usage:
#   ./deploy_hf.sh
#
# Prerequisites:
#   - Git remote `space` configured:
#       git remote add space https://huggingface.co/spaces/lituokobe/sb-ai-assistant
#   - HF access token stored in git credentials (Settings > Access Tokens).

set -euo pipefail

REMOTE_NAME="space"
REMOTE_BRANCH="main"
ORPHAN_BRANCH="hf-deploy"
BINARY_FILES=("UI_demo.png")

echo "=== HF Space Deployment ==="

# 1. Verify we are on main.
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "FAIL: Must be on 'main' (currently '$CURRENT_BRANCH')."
    exit 1
fi
echo "OK: On main branch."

# 2. Create orphan branch (no ancestry = no binary files in history).
echo "Creating orphan branch '$ORPHAN_BRANCH'..."
git checkout --orphan "$ORPHAN_BRANCH"

# 3. Stage all files (.gitignore excludes AGENTS.md, MOCKING_STRATEGY.md,
#    PROJECT_GUIDE.md automatically).
git add -A

# 4. Remove binary files from staging (HF rejects them).
for file in "${BINARY_FILES[@]}"; do
    if git diff --cached --name-only | grep -q "^${file}$"; then
        git rm --cached "$file"
        echo "OK: Removed binary from staging: $file"
    fi
done

# 5. Verify no binary or internal docs leaked into the staging area.
LEAKED=$(git diff --cached --name-only | grep -iE "UI_demo|AGENTS|MOCKING|PROJECT_GUIDE" || true)
if [ -n "$LEAKED" ]; then
    echo "FAIL: Binary/internal files still staged:"
    echo "$LEAKED"
    git checkout main
    git branch -D "$ORPHAN_BRANCH" 2>/dev/null || true
    exit 1
fi
echo "OK: No binary or internal files staged."

# 6. Inject HF Spaces YAML metadata into README.md.
#    Local README.md starts with "# SB AI Shopping Assistant" for a clean
#    GitHub appearance.  HF Spaces requires YAML front matter to configure
#    the Space (SDK, app_file, python_version).  We prepend it here so it
#    only exists on the HF Space, not on GitHub.
echo "Injecting HF Spaces metadata into README.md..."
cat << 'HFYAML' > /tmp/_hf_yaml_header.txt
---
title: SB AI Assistant
emoji: "\U0001f6cd\ufe0f"
colorFrom: red
colorTo: pink
sdk: gradio
app_file: app.py
python_version: "3.13"
pinned: false
suggested_hardware: cpu-basic
---

HFYAML
cat /tmp/_hf_yaml_header.txt README.md > /tmp/_hf_readme.md
mv /tmp/_hf_readme.md README.md
rm -f /tmp/_hf_yaml_header.txt
git add README.md
echo "OK: HF metadata injected into README.md."

# 7. Commit the clean snapshot.
git commit -m "Deploy SB AI Assistant to Hugging Face Spaces"
echo "OK: Committed."

# 8. Force-push to HF Space.
echo "Pushing to $REMOTE_NAME:$REMOTE_BRANCH ..."
git push "$REMOTE_NAME" "$ORPHAN_BRANCH:$REMOTE_BRANCH" --force
echo "OK: Pushed."

# 9. Switch back and clean up.
# Remove binary files from the working tree so they don't block the
# checkout (main tracks them and will restore them automatically).
for file in "${BINARY_FILES[@]}"; do
    rm -f "$file"
done
git checkout main
git branch -D "$ORPHAN_BRANCH"

echo ""
echo "=== Deployment complete ==="
echo "  Space page: https://huggingface.co/spaces/lituokobe/sb-ai-assistant"
echo "  Live app:   https://lituokobe-sb-ai-assistant.hf.space"
