# py-logging

## Hypothesis

Logging from multiple processes in Python can garble the output.

## Proof

`mise run bug` (or `./bug.sh`).

## Fix

The logger should acquire a shared `multiprocessing.RLock()` before writing to and flushing
the underlying the stream.

### Proof of fix

`mise run fix` (or `./fix.sh`).