#!/usr/bin/env bash

python3 -u ./bug.py --producer | python3 -u ./bug.py --consumer
