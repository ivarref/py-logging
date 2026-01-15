#!/usr/bin/env bash

set -euo pipefail

SELFPID="$$"
PYTHON_EXECUTEABLE="${PYTHON_EXECUTEABLE:-python3}"

echo "Using python3 located at: $(which "${PYTHON_EXECUTEABLE}")"
echo "Version: $("${PYTHON_EXECUTEABLE}" --version)"

"${PYTHON_EXECUTEABLE}" -u ./fix.py --producer | \
bash -c "
onEXIT () {
  EXIT_STATUS=\$?
#  echo 'Killing children ...'
  pkill -P \"$SELFPID\"
  exit \$EXIT_STATUS
}

trap onEXIT EXIT
\"${PYTHON_EXECUTEABLE}\" -u ./fix.py --consumer"
