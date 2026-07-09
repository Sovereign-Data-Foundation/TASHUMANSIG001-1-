#!/usr/bin/env bash
# Point git at the tracked hooks directory.
# Run once after cloning:  bash setup-hooks.sh
set -e
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
echo "Git hooks installed from .githooks/."
