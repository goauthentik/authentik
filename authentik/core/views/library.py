"""authentik library view"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from authentik.core.models import Application
from authentik.policies.engine import PolicyEngine


class LibraryView(LoginRequiredMixin, TemplateView):
    """Overview for logged in user, incase user opens authentik directly
    and is not being forwarded"""

    template_name = "library.html"

    def get_context_data(self, **kwargs):
        kwargs["applications"] = []
        for application in Application.objects.all().order_by("name"):
            engine = PolicyEngine(application, self.request.user, self.request)
            engine.build()
            if engine.passing:
                kwargs["applications"].append(application)
        return super().get_context_data(**kwargs)
