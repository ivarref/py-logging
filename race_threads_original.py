#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor
import logging
import time

big_line = '*' * 10_000

def current_milli_time():
    return time.time_ns() // 1_000_000

def single_producer(thread_id):
    try:
        start_time_millis = current_milli_time()
        spent_s = 0
        last_s = 0
        total_lines = 0
        spent_ms = 0
        while spent_s < 60:
            for x in range(10_000):
                logging.log(logging.INFO, big_line)
            total_lines += 10_000
            spent_ms = current_milli_time() - start_time_millis
            spent_s = spent_ms // 1000
            if last_s != spent_s:
                print(f'Thread {thread_id} spent {spent_s} secs', flush=True)
                last_s = spent_s
        return spent_ms, total_lines
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass

def run_producer():
    futures = []
    max_workers = 8
    try:
        with ThreadPoolExecutor(max_workers) as executor:
            for thread_id in range(max_workers):
                fut = executor.submit(single_producer, 1 + thread_id)
                futures.append(fut)
            total_ms = 0
            total_lines = 0
            for fut in futures:
                spent_ms, line_count = fut.result()
                total_ms += spent_ms
                total_lines += line_count
            lines_per_ms = total_lines // total_ms
            print(f'Total lines: {total_lines:_}, lines/ms: {lines_per_ms:_}', flush=True)
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_producer()
