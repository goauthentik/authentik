"""SignalMiddleware tests"""

from unittest.mock import patch

from django.dispatch import Signal
from django.test import RequestFactory, SimpleTestCase

from authentik.lib.middleware import SignalMiddleware


class TestSignalMiddleware(SimpleTestCase):
    """SignalMiddleware tests"""

    def setUp(self):
        self.signal = Signal()
        self.calls = []
        calls = self.calls

        class Parent(SignalMiddleware):
            signal_handlers = {self.signal: "handler"}

            def handler(self, request, sender, **kwargs):
                calls.append((self, request, sender, kwargs))

        class Child(Parent):
            pass

        self.parent_class = Parent
        self.child_class = Child

    def test_dispatch_to_current_request(self):
        """Signals are only handled during a request, by the middleware handling it"""
        request = RequestFactory().get("/")
        self.signal.send(sender=object)
        self.assertEqual(self.calls, [])

        middleware = self.parent_class(lambda req: self.signal.send(sender=object, foo="bar"))
        middleware(request)
        self.assertEqual(
            self.calls, [(middleware, request, object, {"signal": self.signal, "foo": "bar"})]
        )
        self.assertIsNone(self.parent_class.current_request())

    def test_subclass_shares_parent_signals(self):
        """A subclass handles the signals its parent declared"""
        request = RequestFactory().get("/")
        middleware = self.child_class(lambda req: self.signal.send(sender=object))
        middleware(request)
        self.assertEqual(self.calls, [(middleware, request, object, {"signal": self.signal})])

    def test_connect_once(self):
        """Connecting again doesn't call Signal.connect(), which clears the receiver cache"""
        other = Signal()
        with patch.object(other, "connect") as connect:
            self.parent_class.connect(other, "handler")
            self.child_class.connect(other, "handler")
            connect.assert_called_once()

    def test_missing_handler(self):
        """Handlers a middleware doesn't implement are skipped"""
        other = Signal()
        self.child_class.connect(other, "missing")
        middleware = self.parent_class(lambda req: other.send(sender=object))
        middleware(RequestFactory().get("/"))
        self.assertEqual(self.calls, [])
