"""passbook TOTP Urls"""

from django.urls import path

from passbook.totp import views

urlpatterns = [
    path('', views.index, name='totp-index'),
    path('qr/', views.qr_code, name='totp-qr'),
    path('verify/', views.verify, name='totp-verify'),
    # path('enable/', views.TFASetupView.as_view(), name='totp-enable'),
    path('disable/', views.disable, name='totp-disable'),
    path('user_settings/', views.user_settings, name='totp-user_settings'),
]
