#!/usr/bin/env bash

set -euo pipefail

SELFPID="$$"

echo "Using python3 located at: $(which python3)"
echo "Version: $(python3 --version)"

python3 -u ./fix.py --producer | \
bash -c "
onEXIT () {
  EXIT_STATUS=\$?
  echo 'Killing children ...'
  pkill -P \"$SELFPID\"
  exit \$EXIT_STATUS
}

trap onEXIT EXIT
python3 -u ./fix.py --consumer"
