#!/usr/bin/env python3

import logging
import logging.handlers
import multiprocessing
import os

import time

big_line = '*' * 10_000

def current_milli_time():
    return time.time_ns() // 1_000_000

#
# Because you'll want to define the logging configurations for listener and workers, the
# listener and worker process functions take a configurer parameter which is a callable
# for configuring logging for that process. These functions are also passed the queue,
# which they use for communication.
#
# In practice, you can configure the listener however you want, but note that in this
# simple example, the listener does not apply level or filter logic to received records.
# In practice, you would probably want to do this logic in the worker processes, to avoid
# sending events which would be filtered out between processes.
def listener_configurer():
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
        h.close()

    h = logging.handlers.RotatingFileHandler('output.txt', 'w', 100 * 1024 * 1024 * 1024, 10)
    f = logging.Formatter('%(message)s')
    h.setFormatter(f)
    root.addHandler(h)

# This is the listener process top-level loop: wait for logging events
# (LogRecords)on the queue and handle them, quit when you get a None for a
# LogRecord.
def listener_process(queue, configurer):
    configurer()
    start_time_millis = current_milli_time()
    total_lines = 0
    while True:
        try:
            record = queue.get()
            if record is None:  # We send this as a sentinel to tell the listener to quit.
                break
            total_lines += 1
            logger = logging.getLogger(record.name)
            logger.handle(record)  # No level or filter logic applied - just do it!
        except Exception:
            import sys, traceback
            print('Whoops! Problem:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    total_ms = current_milli_time() - start_time_millis
    lines_per_ms = total_lines / total_ms
    print(f'{os.path.basename(__file__)}: total lines: {total_lines:_}, total ms: {total_ms:_}, lines/ms: {lines_per_ms:.2f}', flush=True)

# The worker configuration is done at the start of the worker process run.
# Note that on Windows you can't rely on fork semantics, so each process
# will run the logging configuration code when it starts.
def worker_configurer(queue):
    h = logging.handlers.QueueHandler(queue)  # Just the one handler needed
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
        h.close()
    root.addHandler(h)
    # send all messages, for demo; no other level or filter logic applied.
    root.setLevel(logging.INFO)

def worker_process(producer_id, queue, configurer):
    configurer(queue)
    name = multiprocessing.current_process().name
    print('Worker started: %s' % name)
    last_s = 0
    total_lines = 0
    spent_s = 0
    start_time_millis = current_milli_time()
    while spent_s < 10:
        for x in range(10_000):
            logging.log(logging.INFO, big_line)
        total_lines += 10_000
        spent_ms = current_milli_time() - start_time_millis
        spent_s = spent_ms // 1000
        if last_s != spent_s:
            print(f'Producer {producer_id} spent {spent_s} secs', flush=True)
            last_s = spent_s
    print('Worker finished: %s' % name)

# Here's where the demo gets orchestrated. Create the queue, create and start
# the listener, create ten workers and start them, wait for them to finish,
# then send a None to the queue to tell the listener to finish.
def main():
    multiprocessing.set_start_method("forkserver")
    if os.path.exists('./output.txt'):
        os.remove('./output.txt')
        print('Removed ./output.txt', flush=True)
    queue = multiprocessing.Queue(-1)
    listener = multiprocessing.Process(target=listener_process,
                                       args=(queue, listener_configurer))
    listener.start()
    workers = []
    for i in range(8):
        worker = multiprocessing.Process(target=worker_process,
                                         args=(1 + i, queue, worker_configurer))
        workers.append(worker)
        worker.start()
    for w in workers:
        w.join()
    queue.put_nowait(None)
    listener.join()

# race_cookbook_1.py: total lines: 310_793, total ms: 11_118, lines/ms: 27.95
# + many, many errors due to full queue:
# cat errors.txt | grep 'queue.Full' | wc -l
# 89207

if __name__ == '__main__':
    main()