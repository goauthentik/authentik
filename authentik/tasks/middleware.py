from dramatiq.broker import Broker
from dramatiq.message import Message
from dramatiq.middleware import Middleware

from authentik.tasks.models import Task
from authentik.tenants.models import Tenant
from authentik.tenants.utils import get_current_tenant


class TenantMiddleware(Middleware):
    def before_enqueue(self, broker: Broker, message: Message, delay: int):
        message.options["model_defaults"]["tenant"] = get_current_tenant()

    def before_process_message(self, broker: Broker, message: Message):
        task: Task = message.options["task"]
        task.tenant.activate()

    def after_process_message(self, *args, **kwargs):
        Tenant.deactivate()


class RelObjMiddleware(Middleware):
    @property
    def actor_options(self):
        return {"rel_obj"}

    def before_enqueue(self, broker: Broker, message: Message, delay: int):
        if rel_obj := message.options.get("rel_obj"):
            del message.options["rel_obj"]
        message.options["model_defaults"]["rel_obj"] = rel_obj
