#!/usr/bin/env python3
import sys
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import logging
import time

big_line = '*' * 10_000

def current_milli_time():
    return time.time_ns() // 1_000_000

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
    total_lines = 0
    start_time = current_milli_time()
    try:
        print(f'Line length is {len(big_line):_}', flush=True)
        for line in sys.stdin:
            line = line.strip()
            total_lines += 1
            all_stars = '*' * len(line)
            if line == all_stars:
                if len(line) == len(big_line):
                    ok_line_count += 1
                else:
                    bad_line_count += 1
            else:
                print(f'Got unexpected line: {line}', flush=True)
                sys.exit(1)
            if total_lines % 10_000 == 0:
                spent_ms = current_milli_time() - start_time
                spent_ms = spent_ms // 1000
                if spent_ms == 0:
                    spent_ms = 1
                lines_per_ms = total_lines // spent_ms
                msg = f'OK line count: {ok_line_count:_}, garbled line count: {bad_line_count:_}, lines/s: {lines_per_ms:_}'
                print(msg, flush=True)
        print('Stdin closed', flush=True)
    except BrokenPipeError:
        pass
    except KeyboardInterrupt:
        print('Consumer received KeyboardInterrupt', flush=True)
    finally:
        try:
            print('Consumer exiting', flush=True)
            print(f'OK line count: {ok_line_count:_}', flush=True)
            print(f'Bad line count: {bad_line_count:_}', flush=True)
        except BrokenPipeError:
            pass

if __name__ == "__main__":
    mp.set_start_method("forkserver")
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    if '--producer' in sys.argv:
        run_producer()
    elif '--consumer' in sys.argv:
        run_consumer()
    else:
        print('Unknown mode, exiting', flush=True)
        sys.exit(1)
