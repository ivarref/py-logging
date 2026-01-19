#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import multiprocessing as mp
import sys
import os

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
            lines_per_ms = total_lines / (total_ms / max_workers)
            print(f'{os.path.basename(__file__)}: total lines: {total_lines:_}, total ms: {total_ms:_}, lines/ms: {lines_per_ms:.2f}', flush=True)
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass

from types import GenericAlias

class MultiProcessingStreamHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.
    """

    terminator = "\n"

    def __init__(self, multiprocess_lock, stream=sys.stderr):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        assert isinstance(multiprocess_lock, mp.synchronize.RLock)
        self.multiprocess_lock = multiprocess_lock
        self.stream = stream

    def flush(self):
        """
        Flushes the stream.
        """
        with self.lock:
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()

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
            with self.multiprocess_lock:
                msg = self.format(record)
                stream = self.stream
                # issue 35046: merged two stream.writes into one.
                stream.write(msg + self.terminator)
                self.flush()
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

    def setStream(self, stream):
        """
        Sets the StreamHandler's stream to the specified value,
        if it is different.

        Returns the old stream, if the stream was changed, or None
        if it wasn't.
        """
        if stream is self.stream:
            result = None
        else:
            result = self.stream
            with self.lock:
                self.flush()
                self.stream = stream
        return result

    def __repr__(self):
        level = getLevelName(self.level)
        name = getattr(self.stream, "name", "")
        #  bpo-36015: name can be an int
        name = str(name)
        if name:
            name += " "
        return "<%s %s(%s)>" % (self.__class__.__name__, name, level)

    __class_getitem__ = classmethod(GenericAlias)

def run_main():
    mp.set_start_method('forkserver')
    handler = MultiProcessingStreamHandler(mp.get_context('forkserver').RLock())
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True, handlers=[handler])
    run_producer()

if __name__ == "__main__":
    run_main()
