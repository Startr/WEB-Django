from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.AccountDashboardView.as_view(), name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/create/', views.create_profile_view, name='create_profile'),
    path('register/', views.register_view, name='register'),
]