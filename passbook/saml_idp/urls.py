"""passbook SAML IDP URLs"""
from django.conf.urls import url

from passbook.saml_idp import views

urlpatterns = [
    url(r'^login/$', views.login_begin, name="saml_login_begin"),
    url(r'^login/process/$', views.login_process, name='saml_login_process'),
    url(r'^logout/$', views.logout, name="saml_logout"),
    url(r'^metadata/xml/$', views.descriptor, name='metadata_xml'),
    # url(r'^settings/$', views.IDPSettingsView.as_view(), name='admin_settings'),
]
