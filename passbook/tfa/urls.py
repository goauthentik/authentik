"""passbook 2FA Urls"""

from django.conf.urls import url

from passbook.tfa import views

urlpatterns = [
    url(r'^$', views.index, name='tfa-index'),
    url(r'qr/$', views.qr_code, name='tfa-qr'),
    url(r'verify/$', views.verify, name='tfa-verify'),
    # url(r'enable/$', views.TFASetupView.as_view(), name='tfa-enable'),
    url(r'disable/$', views.disable, name='tfa-disable'),
    url(r'user_settings/$', views.user_settings, name='tfa-user_settings'),
]
