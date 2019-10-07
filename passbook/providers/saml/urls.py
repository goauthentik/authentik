"""passbook SAML IDP URLs"""
from django.urls import path

from passbook.providers.saml import views

urlpatterns = [
    path('<slug:application>/login/',
         views.LoginBeginView.as_view(), name="saml-login"),
    path('<slug:application>/login/initiate/',
         views.InitiateLoginView.as_view(), name="saml-login-initiate"),
    path('<slug:application>/login/process/',
         views.LoginProcessView.as_view(), name='saml-login-process'),
    path('<slug:application>/logout/', views.LogoutView.as_view(), name="saml-logout"),
    path('<slug:application>/logout/slo/', views.SLOLogout.as_view(), name="saml-logout-slo"),
    path('<slug:application>/metadata/',
         views.DescriptorDownloadView.as_view(), name='saml-metadata'),
]
