#!/usr/bin/env python3
from concurrent.futures import ProcessPoolExecutor
import logging
import time
import multiprocessing as mp
import sys
import os

big_line = '*' * 10_000

def current_milli_time():
    return time.time_ns() // 1_000_000

def single_producer(producer_id):
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
                print(f'Producer {producer_id} spent {spent_s} secs', flush=True)
                last_s = spent_s
        return spent_ms, total_lines
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass

def init_logger(log_queue):
    handler = MultiProcessingQueueHandler(log_queue)
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True, handlers=[handler])

log_q = None

def init_reader(log_queue):
    global log_q
    log_q = log_queue

def run_reader():
    global log_q
    assert log_q is not None
    total_lines = 0
    start_time_millis = current_milli_time()
    while True:
        line = log_q.get()
        if line == '__DONE__':
            break
        total_lines += 1
        print(line, file=sys.stderr, flush=True)
    total_ms = current_milli_time() - start_time_millis
    lines_per_ms = total_lines / total_ms
    print(f'{os.path.basename(__file__)}: total lines: {total_lines:_}, total ms: {total_ms:_}, lines/ms: {lines_per_ms:.2f}', flush=True)

def run_producer(log_queue):
    mp_context = mp.get_context("forkserver")
    futures = []
    max_workers = 8
    try:
        with ProcessPoolExecutor(1,
                                 initializer=init_reader,
                                 initargs=(log_queue,),
                                 mp_context=mp_context) as log_consumer:
            reader_fut = log_consumer.submit(run_reader)
            with ProcessPoolExecutor(max_workers,
                                     initializer=init_logger,
                                     initargs=(log_queue,),
                                     mp_context=mp_context) as executor:
                for i in range(max_workers):
                    fut = executor.submit(single_producer, i + 1)
                    futures.append(fut)
                    total_ms = 0
                total_lines = 0
                for fut in futures:
                    spent_ms, line_count = fut.result()
                    total_ms += spent_ms
                    total_lines += line_count
                lines_per_ms = total_lines / (total_ms / max_workers)
                # print(f'{os.path.basename(__file__)}: total lines: {total_lines:_}, total ms: {total_ms:_}, lines/ms: {lines_per_ms:.2f}', flush=True)
            log_queue.put('__DONE__')
            reader_fut.result()
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass

from types import GenericAlias

class MultiProcessingQueueHandler(logging.Handler):
    def __init__(self, log_queue):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        # assert isinstance(log_queue, mp.synchronize.Queue)
        self.log_queue = log_queue

    def flush(self):
        """
        Flushes the stream.
        """
        pass

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

    def __repr__(self):
        return "MPQueueHandler"

    __class_getitem__ = classmethod(GenericAlias)

def run_main():
    mp.set_start_method('forkserver')
    # q = mp.Manager().Queue(-1)
    q = mp.get_context('forkserver').SimpleQueue()
    run_producer(q)

if __name__ == "__main__":
    run_main()
