#!/usr/bin/env bash

set -euo pipefail

echo "Using python3 located at: $(which python3)"
echo "Version: $(python3 --version)"
python3 -u ./fix.py --producer | python3 -u ./fix.py --consumer
