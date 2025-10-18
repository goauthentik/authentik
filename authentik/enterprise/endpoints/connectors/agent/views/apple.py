from django.http import HttpRequest, HttpResponseBadRequest
from django.views import View


class SSOExtensionView(View):

    def get(self, request: HttpRequest):
        print(request.GET)
        return HttpResponseBadRequest()
