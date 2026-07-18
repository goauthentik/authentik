from django.test import TestCase
from dramatiq.broker import get_broker


class TestActors(TestCase):
    def test_all_actors_have_description(self):
        broker = get_broker()
        for actor_name in broker.get_declared_actors():
            actor = broker.get_actor(actor_name)
            self.assertIn("description", actor.options)
