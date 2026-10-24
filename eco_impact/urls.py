from django.urls import path
from . import views

app_name = 'eco_impact'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),           # halaman utama dashboard
    path('logs/', views.log_list, name='log_list'),        # list semua log (opsional)
    path('logs/create/', views.create_log, name='create_log'),         # form tambah log manual
    path('logs/<uuid:pk>/edit/', views.edit_log, name='edit_log'),     # edit log manual
    path('logs/<uuid:pk>/delete/', views.delete_log, name='delete_log'), # hapus log manual

    # endpoint khusus untuk AJAX — dipanggil dari JS, bukan dari browser langsung
    path('api/summary/', views.summary_api, name='summary_api'),
    path('api/logs/', views.logs_api, name='logs_api'),
]