"""passbook OAuth2 Views"""

# from logging import getLogger

# from django.contrib import messages
# from django.http import Http404, HttpResponseRedirect
# from django.utils.translation import ugettext as _
# from oauth2_provider.models import get_application_model
# from oauth2_provider.views.base import AuthorizationView

# # from passbook.core.models import Event, UserAcquirableRelationship

# LOGGER = getLogger(__name__)


# class PassbookAuthorizationView(AuthorizationView):
#     """Custom OAuth2 Authorization View which checks for invite_only products"""

#     def get(self, request, *args, **kwargs):
#         """Check if request.user has a relationship with product"""
#         full_res = super().get(request, *args, **kwargs)
#         # If application cannot be found, oauth2_data is {}
#         if self.oauth2_data == {}:
#             return full_res
#         # self.oauth2_data['application'] should be set, if not an error occured
#         # if 'application' in self.oauth2_data:
#         #     app = self.oauth2_data['application']
#         #     if app.productextensionoauth2_set.exists() and \
#         #             app.productextensionoauth2_set.first().product_set.exists():
#         #         # Only check if there is a connection from OAuth2 Application to product
#         #         product = app.productextensionoauth2_set.first().product_set.first()
#         #         relationship = UserAcquirableRelationship.objects.filter(user=request.user,
#         #                                                                  model=product)
#         #         # Product is invite_only = True and no relation with user exists
#         #         if product.invite_only and not relationship.exists():
#         #             LOGGER.warning("User '%s' has no invitation to '%s'", request.user, product)
#         #             messages.error(request, "You have no access to '%s'" % product.name)
#         #             raise Http404
#         #     if isinstance(full_res, HttpResponseRedirect):
#         #         # Application has skip authorization on
#         #         Event.create(
#         #             user=request.user,
#         #             message=_('You authenticated %s (via OAuth) (skipped Authz)' % app.name),
#         #             request=request,
#         #             current=False,
#         #             hidden=True)
#         return full_res

#     def post(self, request, *args, **kwargs):
#         """Add event on confirmation"""
#         app = get_application_model().objects.get(client_id=request.GET["client_id"])
#         # Event.create(
#         #     user=request.user,
#         #     message=_('You authenticated %s (via OAuth)' % app.name),
#         #     request=request,
#         #     current=False,
#         #     hidden=True)
#         return super().post(request, *args, **kwargs)
