#!/usr/bin/env bash

python3 -u ./log2.py --producer | env IS_CONSUMER='true' python3 -u ./log2.py
#
