from django.apps import AppConfig

class StagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stages'

    def ready(self):
        # Importer le module signals pour que Django enregistre les signaux
        import stages.signals
