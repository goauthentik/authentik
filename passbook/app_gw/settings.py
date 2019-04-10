"""Application Security Gateway settings"""
INSTALLED_APPS = [
    'channels'
]
ASGI_APPLICATION = "passbook.app_gw.websocket.routing.application"
