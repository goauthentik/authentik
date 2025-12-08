from __future__ import unicode_literals

from .compat import text_type


class Node(object):
    def __str__(self):
        children = []
        for k, v in self.__dict__.items():
            if isinstance(v, (list, tuple)):
                v = '[%s]' % ', '.join([text_type(v) for v in v if v])
            children.append('%s=%s' % (k, v))
        return '<%s%s%s>' % (
            self.__class__.__name__,
            ': ' if children else '',
            ', '.join(children),
        )

    __repr__ = __str__

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        for k, v in self.__dict__.items():
            if getattr(other, k) != v:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


class Expression(Node):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right


class Name(Node):
    def __init__(self, parts):
        if isinstance(parts, list):
            self.parts = parts
        elif isinstance(parts, tuple):
            self.parts = list(parts)
        else:
            self.parts = [parts]

    @property
    def value(self):
        return '.'.join(self.parts)


class Const(Node):
    def __init__(self, value):
        self.value = value


class List(Node):
    def __init__(self, items):
        self.items = items

    @property
    def value(self):
        return [i.value for i in self.items]


class Operator(Node):
    def __init__(self, operator):
        self.operator = operator


class Logical(Operator):
    pass


class Comparison(Operator):
    pass
