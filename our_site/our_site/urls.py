"""
URL configuration for our_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, re_path, include
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django_startr.views import debug_index, debug_permission_denied
from accounts.views import register_view

# Custom view for the root URL
from django.shortcuts import render

def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'home.html')
    else:
        # Use the login template with a welcome message
        return LoginView.as_view(template_name='registration/login.html', 
                                extra_context={
                                    'title': 'Particip8',
                                    'welcome_message': 'Where participation becomes portfolio'
                                    })(request)

urlpatterns = [
    path('', home_view, name='home'),
    path("experiences/", include("experiences.urls")),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('auth/', include('django.contrib.auth.urls')),
    path("admin/", admin.site.urls),
    path('register/', register_view, name='register'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'django_startr.views.debug_index'
handler403 = 'django_startr.views.debug_permission_denied'

if settings.DEBUG:
    urlpatterns += [
        # Only allow the home page and authentication URLs to be accessed without login
        re_path(r'^$', home_view),
        re_path(r'^auth/.*$', include('django.contrib.auth.urls')),
        re_path(r'^register/$', register_view),  # Allow access to registration
        re_path(r'^admin/.*$', admin.site.urls),
        # All other paths require login
        re_path(r'^.*$', login_required(debug_index)),
    ]

admin.site.site_header = "Startr Admin"
admin.site.site_title = "Startr Education Admin Portal"
admin.site.index_title = "Welcome to your Startr Education admin panel"