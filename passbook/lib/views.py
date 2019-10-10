"""passbook helper views"""

from django.views.generic import CreateView
from guardian.shortcuts import assign_perm


class CreateAssignPermView(CreateView):
    """Assign permissions to object after creation"""

    permissions = []

    def form_valid(self, form):
        response = super().form_valid(form)
        for permission in self.permissions:
            assign_perm(permission, self.request.user, self.object)
        return response
