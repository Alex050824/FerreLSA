
from django.urls import path
from . import views

urlpatterns = [
    path(
        "preguntar/",
        views.preguntar_chatbot,
        name="preguntar_chatbot"
    ),
    path(
        "csrf/",
        views.iniciar_csrf,
        name="chatbot_csrf"
    ),
]
