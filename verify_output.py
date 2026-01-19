#!/usr/bin/env python3
import sys

big_line = '*' * 10_000

if __name__ == "__main__":
    with open('output.txt') as fd:
        for lin in fd.readlines():
            lin = lin.strip()
            if lin != big_line:
                print('error')
                sys.exit(1)
    print('output.txt OK')


