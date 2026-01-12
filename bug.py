#!/usr/bin/env python3
import sys
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import logging

big_line = '*' * 1000

def single_producer():
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    try:
        while True:
            logging.log(logging.INFO, big_line)
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass

def run_producer():
    mp_context = mp.get_context("forkserver")
    futures = []
    max_workers = 8
    try:
        with ProcessPoolExecutor(max_workers, mp_context=mp_context) as executor:
            for _ in range(max_workers):
                fut = executor.submit(single_producer)
                futures.append(fut)
            for fut in futures:
                fut.result()
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass

def run_consumer():
    bad_line_count = 0
    ok_line_count = 0
    try:
        for line in sys.stdin:
            line = line.strip()
            all_stars = '*' * len(line)
            if line == all_stars:
                if len(line) == len(big_line):
                    ok_line_count += 1
                else:
                    bad_line_count += 1
                    print(f'Got garbled star line with length {len(line):_}')
            else:
                print(f'Got unexpected line: {line}', flush=True)
                sys.exit(1)
    except BrokenPipeError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        try:
            print('Consumer exiting', flush=True)
            print(f'OK line count: {ok_line_count:_}', flush=True)
            print(f'Bad line count: {bad_line_count:_}', flush=True)
        except BrokenPipeError:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    if '--producer' in sys.argv:
        run_producer()
    elif '--consumer' in sys.argv:
        run_consumer()
    else:
        print('Unknown mode, exiting', flush=True)
        sys.exit(1)
