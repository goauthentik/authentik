from rest_framework.routers import DefaultRouter as UpstreamDefaultRouter
from rest_framework.viewsets import ViewSet
from rest_framework_nested.routers import NestedMixin


class DefaultRouter(UpstreamDefaultRouter):
    include_format_suffixes = False


class NestedRouter(DefaultRouter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nested_routers = []

    class nested:
        def __init__(self, parent: "NestedRouter", prefix: str):
            self.parent = parent
            self.prefix = prefix
            self.inner = None

        def nested(self, lookup: str, prefix: str, viewset: type[ViewSet]):
            if not self.inner:
                self.inner = NestedDefaultRouter(self.parent, self.prefix, lookup=lookup)
            self.inner.register(prefix, viewset)
            return self

        @property
        def urls(self):
            return self.parent.urls

    def register(self, prefix, viewset, basename=None):
        super().register(prefix, viewset, basename)
        nested_router = self.nested(self, prefix)
        self.nested_routers.append(nested_router)
        return nested_router

    def get_urls(self):
        urls = super().get_urls()
        for nested in self.nested_routers:
            if not nested.inner:
                continue
            urls.extend(nested.inner.urls)
        return urls


class NestedDefaultRouter(NestedMixin, DefaultRouter):
    ...
    # def __init__(self, *args, **kwargs):
    #     self.args = args
    #     self.kwargs = kwargs
    #     self.routes = []

    # def register(self, *args, **kwargs):
    #     self.routes.append((args, kwargs))

    # @property
    # def urls(self):
    #     class r(NestedMixin, DefaultRouter):
    #         ...
    #     router = r(*self.args, **self.kwargs)
    #     for route_args, route_kwrags in self.routes:
    #         router.register(*route_args, **route_kwrags)
    #     return router


root_router = DefaultRouter()
