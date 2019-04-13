"""QueueListener that can be configured from logging.dictConfig"""
from atexit import register
from logging.config import ConvertingList
from logging.handlers import QueueHandler, QueueListener
from queue import Queue


def _resolve_handlers(_list):
    """Evaluates ConvertingList by iterating over it"""
    if not isinstance(_list, ConvertingList):
        return _list

    # Indexing the list performs the evaluation.
    return [_list[i] for i in range(len(_list))]


class QueueListenerHandler(QueueHandler):
    """QueueListener that can be configured from logging.dictConfig"""

    def __init__(self, handlers, auto_run=True, queue=Queue(-1)):
        super().__init__(queue)
        handlers = _resolve_handlers(handlers)
        self._listener = QueueListener(
            self.queue,
            *handlers,
            respect_handler_level=True)
        if auto_run:
            self.start()
            register(self.stop)

    def start(self):
        """start background thread"""
        self._listener.start()

    def stop(self):
        """stop background thread"""
        self._listener.stop()
