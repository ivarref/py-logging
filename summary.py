#!/usr/bin/env python3

def run_main():
    org_ms = 0
    org_lines = 0
    mplock_ms = 0
    mplock_lines = 0
    with open('results.txt') as fd:
        for lin in fd.readlines():
            lin = lin.strip()
            if 'total' not in lin:
                continue
            line_count = int(lin.split('total lines: ')[1].split(',')[0].replace('_', ''))
            spent_ms = int(lin.split('total ms: ')[1].split(',')[0].replace('_', ''))
            if 'original.py' in lin:
                org_ms += spent_ms
                org_lines += line_count
            else:
                mplock_ms += spent_ms
                mplock_lines += line_count
    org_lines_ms = org_lines / org_ms
    mplock_lines_ms = mplock_lines / mplock_ms
    mplock_relative = (100 * mplock_lines_ms) / org_lines_ms
    print(f'Original total lines: {org_lines:_}, total ms: {org_ms:_}, lines/ms: { (org_lines / (org_ms / 8)):.2f}')
    print(f'mp.Rlock total lines: {mplock_lines:_}, total ms: {mplock_ms:_}, lines/ms: { (mplock_lines / (mplock_ms / 8)):.2f}')
    print(f'mp.Rlock performance: {mplock_relative:.2f} %')

if __name__ == "__main__":
    run_main()
