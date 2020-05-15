"""Dispatch OAuth views to respective views"""
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views import View

from passbook.channels.in_oauth.models import OAuthInlet
from passbook.channels.in_oauth.types.manager import MANAGER, RequestKind


class DispatcherView(View):
    """Dispatch OAuth Redirect/Callback views to their proper class based on URL parameters"""

    kind = ""

    def dispatch(self, *args, **kwargs):
        """Find Inlet by slug and forward request"""
        slug = kwargs.get("inlet_slug", None)
        if not slug:
            raise Http404
        inlet = get_object_or_404(OAuthInlet, slug=slug)
        view = MANAGER.find(inlet, kind=RequestKind(self.kind))
        return view.as_view()(*args, **kwargs)
