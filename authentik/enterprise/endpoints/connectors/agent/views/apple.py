from django.views import View
from django.http import HttpRequest, HttpResponseBadRequest

class SSOExtensionView(View):

    def get(self, request: HttpRequest):
       print(request.GET)
       return HttpResponseBadRequest()
