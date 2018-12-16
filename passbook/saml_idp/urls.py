"""passbook SAML IDP URLs"""
from django.conf.urls import url

from passbook.saml_idp import views

urlpatterns = [
    url(r'^login/$', views.LoginBeginView.as_view(), name="saml_login_begin"),
    url(r'^login/process/$', views.LoginProcessView.as_view(), name='saml_login_process'),
    url(r'^logout/$', views.LogoutView.as_view(), name="saml_logout"),
    url(r'^metadata/xml/$', views.DescriptorView.as_view(), name='metadata_xml'),
]
