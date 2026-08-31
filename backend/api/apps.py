import threading
from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        def prewarm_model():
            try:
                from .services.notes_analyzer import get_sentence_transformer_model
                get_sentence_transformer_model()
            except Exception:
                pass

        threading.Thread(target=prewarm_model, daemon=True).start()
