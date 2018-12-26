"""passbook SAML IDP URLs"""
from django.urls import path

from passbook.saml_idp import views

urlpatterns = [
    path('login/', views.LoginBeginView.as_view(), name="saml_login_begin"),
    path('login/process/', views.LoginProcessView.as_view(), name='saml_login_process'),
    path('logout/', views.LogoutView.as_view(), name="saml_logout"),
    path('metadata/<int:application_id>/',
         views.DescriptorDownloadView.as_view(), name='metadata_xml'),
]
