from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('todos/', views.todos, name='todos'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('mainhub/', views.mainhub, name='mainhub'),
    path('challenge/<str:folder_name>/', views.challenge_detail, name='challenge_detail'),
    path('challenge/<str:folder_name>/download/<path:file_path>/', views.download_file, name='download_file'),
]