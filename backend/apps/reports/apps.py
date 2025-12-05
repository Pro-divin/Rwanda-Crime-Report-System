from django.apps import AppConfig

class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reports'   # ✅ Full Python path from project root
    verbose_name = "Reports Management"  # ✅ Human-readable name for the app
    
    def ready(self):
        """Import signals when Django starts"""
        import apps.reports.signals  # noqa
