from django.contrib import admin
from .models import Person, Group, Theme

# Register all models at once
admin.site.register((Person, Group, Theme))