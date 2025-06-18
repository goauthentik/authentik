from authentik.blueprints.apps import ManagedAppConfig


class AuthentikTasksConfig(ManagedAppConfig):
    name = "authentik.tasks"
    label = "authentik_tasks"
    verbose_name = "authentik Tasks"
    default = True

    # def use_test_broker(self) -> None:
    #     from authentik.tasks.test import TestBroker
    #
    #     old_broker = get_broker()
    #     broker = TestBroker(middleware=[])
    #     self._set_dramatiq_middlewares(broker, max_retries=0)
    #     dramatiq.set_broker(broker)
    #     for actor_name in old_broker.get_declared_actors():
    #         actor = old_broker.get_actor(actor_name)
    #         actor.broker = broker
    #         actor.broker.declare_actor(actor)
