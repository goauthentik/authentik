from authentik.enterprise.personas.api import PersonaViewSet

api_urlpatterns = [
    ("personas/personas", PersonaViewSet),
]
