#!/usr/bin/env bash

set -euo pipefail

which python3
python3 --version
python3 -u ./bug.py --producer | python3 -u ./bug.py --consumer
