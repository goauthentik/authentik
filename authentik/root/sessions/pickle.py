"""
Module for abstract serializer/unserializer base classes.
"""
import pickle  # nosec


class PickleSerializer:
    """
    Simple wrapper around pickle to be used in signing.dumps()/loads() and
    cache backends.
    """

    def __init__(self, protocol=None):
        self.protocol = pickle.HIGHEST_PROTOCOL if protocol is None else protocol

    def dumps(self, obj):
        """Pickle data to be stored in redis"""
        return pickle.dumps(obj, self.protocol)

    def loads(self, data):
        """Unpickle data to be loaded from redis"""
        return pickle.loads(data)  # nosec
