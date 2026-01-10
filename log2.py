#!/usr/bin/env python3
import sys
import fileinput
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import os
import logging
from time import sleep
from random import random
from unittest.mock import patch

write = sys.stdout.write
flush = sys.stdout.flush

def slow_write(text):
    # ^^ no lock acquired here!
    write(str(os.getpid()) + ': ')
    for c in text:
        sleep(random())
        write(c)
        flush()
    #_write('>' + str(os.getpid()) + ': ' + text)
    # print('type:' + str(type(text)), file=sys.stderr, flush=True)

def single_producer():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.write = slow_write
        logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
        while True:
            logging.log(logging.INFO, '1234567890')
        # slow_write('1234567890\n')
        #_print('12345678901234567890123456789012345678901234567890123456789012345678901234567890', flush=True)


def run_producer():
    mp_context = mp.get_context("forkserver")
    futures = []
    max_workers = 8
    with ProcessPoolExecutor(max_workers, mp_context=mp_context) as executor:
        for x in range(max_workers):
            fut = executor.submit(single_producer)
            futures.append(fut)

        try:
            print('waiting... main pid is: ' + str(os.getpid()))
            # with patch("sys.stdout") as mock_stdout:
            #     mock_stdout.write = slow_write
            #     logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
            #     while True:
            #         logging.log(logging.INFO, '1234567890')
            for fut in futures:
                fut.result()
        finally:
            print('waiting... Done!')


def run_consumer():
    line_number = 1
    for line in fileinput.input():
        line = line.strip()
        if line != '1234567890':
            print(line)
        line_number += 1
        if line_number % 1_000_000 == 0:
            print(f'OK {line_number:_} lines')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    if '--producer' in sys.argv:
        run_producer()
    elif 'IS_CONSUMER' in os.environ:
        run_consumer()
    else:
        print('unknown mode, exiting')
        sys.exit(1)
