"""passbook 2FA Urls"""

from django.urls import path

from passbook.tfa import views

urlpatterns = [
    path('', views.index, name='tfa-index'),
    path('qr/', views.qr_code, name='tfa-qr'),
    path('verify/', views.verify, name='tfa-verify'),
    # path('enable/', views.TFASetupView.as_view(), name='tfa-enable'),
    path('disable/', views.disable, name='tfa-disable'),
    path('user_settings/', views.user_settings, name='tfa-user_settings'),
]
