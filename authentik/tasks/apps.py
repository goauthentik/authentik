from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.lib import ScheduleSpec


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

    @property
    def global_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.tasks.tasks import clean_worker_statuses

        return [
            ScheduleSpec(
                actor=clean_worker_statuses,
                crontab=f"{fqdn_rand('clean_worker_statuses')} {fqdn_rand('clean_worker_statuses', 24)} * * *",  # noqa: E501
            ),
        ]
