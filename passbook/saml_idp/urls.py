"""passbook SAML IDP URLs"""
from django.urls import path

from passbook.saml_idp import views

urlpatterns = [
    path('login/<slug:application>/',
         views.LoginBeginView.as_view(), name="saml_login_begin"),
    path('login/<slug:application>/initiate/',
         views.InitiateLoginView.as_view(), name="saml_login_init"),
    path('login/<slug:application>/process/',
         views.LoginProcessView.as_view(), name='saml_login_process'),
    path('logout/', views.LogoutView.as_view(), name="saml_logout"),
    path('metadata/<slug:application>/',
         views.DescriptorDownloadView.as_view(), name='metadata_xml'),
]
