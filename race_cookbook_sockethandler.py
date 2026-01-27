#!/usr/bin/env python3

import pickle
import logging
import logging.handlers
import socketserver
import struct
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import time
import os

big_line = '*' * 10_000


def current_milli_time():
    return time.time_ns() // 1_000_000


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True

    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self, event):
        import select
        abort = 0
        while not abort and not event.is_set():
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort

barrier = None
event = None

def init_worker(the_barrier, the_event):
    global barrier
    global event
    barrier = the_barrier
    event = the_event


def watch_workers():
    global barrier
    global event
    barrier.wait()
    print('All workers done', flush=True)
    event.set()


def send_log(thread_id):
    global barrier
    rootLogger = logging.getLogger('')
    rootLogger.setLevel(logging.INFO)
    socketHandler = logging.handlers.SocketHandler('localhost',
                                                   logging.handlers.DEFAULT_TCP_LOGGING_PORT)
    # Don't bother with a formatter, since a socket handler sends the event as
    # an unformatted pickle
    rootLogger.addHandler(socketHandler)
    #logging.log(logging.INFO, 'Hello world')
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
                print(f'Process {thread_id} spent {spent_s} secs', flush=True)
                last_s = spent_s
        print(f'Process {thread_id} exiting', flush=True)
        barrier.wait()
        return spent_ms, total_lines
    except KeyboardInterrupt:
        pass

def show_result(result):
    total_ms = 0
    total_lines = 0
    for res in result:
        spent_ms, line_count = res
        total_ms += spent_ms
        total_lines += line_count
    lines_per_ms = total_lines / (total_ms / len(result))
    print(f'{os.path.basename(__file__)}: total lines: {total_lines:_}, total ms: {total_ms:_}, lines/ms: {lines_per_ms:.2f}', flush=True)


def main():
    mp.set_start_method('forkserver')
    logging.basicConfig(format='%(message)s')
    tcpserver = LogRecordSocketReceiver()
    print('Starting TCP server...', flush=True)
    mp_context = mp.get_context('forkserver')
    try:
        max_workers = 8
        barrier = mp_context.Barrier(max_workers + 1)
        event = mp_context.Event()
        with ProcessPoolExecutor(max_workers + 1,
                                 mp_context=mp_context,
                                 initargs=(barrier, event),
                                 initializer=init_worker) as pool:
            futures = []
            for x in range(max_workers):
                fut = pool.submit(send_log, x + 1)
                futures.append(fut)
            watcher = pool.submit(watch_workers)
            try:
                tcpserver.serve_until_stopped(event)
            finally:
                print('TCP Server exited', flush=True)
            watcher.result()
            res = []
            for worker in futures:
                res.append(worker.result())
            try:
                show_result(res)
            except Exception as e:
                print('show_result failed: ' + str(e), flush=True)
    finally:
        print('Process pool exited', flush=True)
        pass


if __name__ == '__main__':
    main()
