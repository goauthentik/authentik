from django.test import TestCase
from dramatiq.broker import get_broker


class TestActors(TestCase):
    def test_all_actors_have_description(self):
        broker = get_broker()
        for actor in broker.get_declared_actors():
            self.assertIn("description", actor.options)
