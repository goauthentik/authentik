from multiprocessing.connection import Connection, wait
from typing import cast


def watch_logs(pipes: list[Connection]):
    try:
        events = cast(list[Connection], wait(pipes, timeout=1))
        for event in events:
            try:
                while event.poll():
                    try:
                        data = event.recv_bytes()
                    except EOFError:
                        event.close()
                        raise

                    data = data.decode("utf-8", errors="replace")
                    yield data
            except BrokenPipeError:
                event.close()
                raise
    # If one of the worker processes is killed, its handle will be
    # closed so waiting for it is going to fail with this OSError.
    # Additionally, event.recv() raises EOFError when its pipe
    # is closed, and event.poll() raises BrokenPipeError when
    # its pipe is closed.  When any of these events happen, we
    # just take the closed pipes out of the waitlist.
    except (EOFError, OSError):
        pipes = [p for p in pipes if not p.closed]
