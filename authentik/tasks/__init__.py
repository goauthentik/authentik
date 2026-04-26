
class TaskWorkerFlag:

    _set = False

    def enable(self):
        self._set = True

    def __bool__(self):
        return self._set

TASK_WORKER = TaskWorkerFlag()
