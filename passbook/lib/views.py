"""passbook helper views"""

from django.views.generic import CreateView
from guardian.shortcuts import assign_perm


class CreateAssignPermView(CreateView):
    """Assign permissions to object after creation"""

    permissions = [
        "%s.view_%s",
        "%s.change_%s",
        "%s.delete_%s",
    ]

    def form_valid(self, form):
        response = super().form_valid(form)
        for permission in self.permissions:
            full_permission = permission % (
                self.object._meta.app_label,
                self.object._meta.model_name,
            )
            print(full_permission)
            assign_perm(full_permission, self.request.user, self.object)
        return response
