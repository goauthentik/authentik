import random
import signal
import sys
import time
from types import FrameType

from dramatiq.broker import get_broker
from dramatiq.cli import RET_CONNECT, RET_IMPORT, RET_KILLED
from dramatiq.compat import StreamablePipe
from dramatiq.errors import ConnectionError
from dramatiq.worker import Worker
from structlog.stdlib import get_logger


def worker_process(
    worker_id,
    threads: int,
    stdout_pipe: StreamablePipe,
    stderr_pipe: StreamablePipe,
) -> None:
    running = True

    sys.stdout = stdout_pipe
    sys.stderr = stderr_pipe
    logger = get_logger("dramatiq_worker", worker_id=worker_id)

    def termhandler(signum: int, frame: FrameType | None):
        nonlocal running
        if running:
            logger.info("Stopping worker process...")
            running = False
        else:
            logger.warning("Killing worker process...")
            return sys.exit(RET_KILLED)

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, termhandler)
    signal.signal(signal.SIGHUP, termhandler)

    # Unblock the blocked signals inherited from the parent process
    # before we start any worker threads and trigger middleware hooks.
    signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGINT, signal.SIGTERM, signal.SIGHUP])

    try:
        # Re-seed the random number generator from urandom on
        # supported platforms.  This should make it so that worker
        # processes don't all follow the same sequence.
        random.seed()

        logger.debug("Loading broker...")
        broker = get_broker()
        broker.emit_after("process_boot")

        logger.debug("Starting worker threads...")
        worker = Worker(broker, queues=None, worker_threads=threads)  # TODO: args
        worker.start()
    except ImportError:
        logger.exception("Failed to import module.")
        return sys.exit(RET_IMPORT)
    except ConnectionError:
        logger.exception("Broker connection failed.")
        return sys.exit(RET_CONNECT)

    logger.info("Worker process is ready for action.")

    while running:
        time.sleep(1)

    worker.stop(timeout=600_000)
    broker.close()
    stdout_pipe.close()
    stderr_pipe.close()
