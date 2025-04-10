from django.apps import AppConfig


class ConstanceConfig(AppConfig):
    """
    Custom configuration for the Constance app to rename it to 'Settings' in the admin.
    """
    name = 'constance'
    verbose_name = 'Settings'