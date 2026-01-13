#!/usr/bin/env python3
import sys
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import logging

big_line = '*' * 10_000

def single_producer():
    try:
        while True:
            logging.log(logging.INFO, big_line)
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass

def init_logger(log_lock):
    handler = MultiProcessingStreamHandler(log_lock)
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True, handlers=[handler])

def run_producer():
    mp_context = mp.get_context("forkserver")
    futures = []
    max_workers = 8
    try:
        with ProcessPoolExecutor(max_workers,
                                 initializer=init_logger,
                                 initargs=(mp_context.RLock(),),
                                 mp_context=mp_context) as executor:
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
                msg = f'OK line count: {ok_line_count:_}, garbled line count: {bad_line_count:_}'
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
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    if '--producer' in sys.argv:
        run_producer()
    elif '--consumer' in sys.argv:
        run_consumer()
    else:
        print('Unknown mode, exiting', flush=True)
        sys.exit(1)

from types import GenericAlias

class MultiProcessingStreamHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.
    """

    terminator = "\n"

    def __init__(self, multiprocess_lock, stream=sys.stdout):  # no test coverage
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        assert isinstance(multiprocess_lock, mp.synchronize.RLock)
        self.multiprocess_lock = multiprocess_lock
        self.stream = stream

    def flush(self):  # no test coverage
        """
        Flushes the stream.
        """
        with self.multiprocess_lock:
            with self.lock:
                if self.stream and hasattr(self.stream, "flush"):
                    self.stream.flush()

    def emit(self, record):  # no test coverage
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

    def setStream(self, stream):  # no test coverage
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

    def __repr__(self):  # no test coverage
        level = getLevelName(self.level)
        name = getattr(self.stream, "name", "")
        #  bpo-36015: name can be an int
        name = str(name)
        if name:
            name += " "
        return "<%s %s(%s)>" % (self.__class__.__name__, name, level)

    __class_getitem__ = classmethod(GenericAlias)
