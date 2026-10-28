from django.urls import path
from . import views

app_name = 'eco_impact'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('logs/', views.log_list, name='log_list'),
    path('logs/create/', views.create_log, name='create_log'),
    path('logs/<uuid:pk>/edit/', views.edit_log, name='edit_log'),
    path('logs/<uuid:pk>/delete/', views.delete_log, name='delete_log'),
    # Alias URL agar routing edit dan delete tetap bekerja dengan atau tanpa prefix logs/
    path('edit/<uuid:pk>/', views.edit_log, name='edit_log_alt'),
    path('delete/<uuid:pk>/', views.delete_log, name='delete_log_alt'),

    # Endpoint AJAX untuk dashboard
    path('api/summary/', views.summary_api, name='summary_api'),
    path('api/logs/', views.logs_api, name='logs_api'),
]
