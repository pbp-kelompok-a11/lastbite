from django.urls import path
from . import views

app_name = 'surprise_bag'

urlpatterns = [
    path('', views.catalog, name='catalog'),                        # katalog publik
    path('mine/', views.my_bags, name='my_bags'),                   # inventaris milik merchant
    path('create/', views.create_bag, name='create'),
    path('<uuid:pk>/', views.bag_detail, name='detail'),
    path('<uuid:pk>/edit/', views.edit_bag, name='edit'),
    path('<uuid:pk>/delete/', views.delete_bag, name='delete'),     # POST only

    # endpoint khusus untuk AJAX — dipanggil dari JS, bukan dari browser langsung
    path('api/', views.catalog_api, name='catalog_api'),
    path('api/<uuid:pk>/', views.bag_api, name='bag_api'),
    path('api/<uuid:pk>/stock/', views.update_stock_api, name='update_stock_api'),
    path('api/<uuid:pk>/toggle/', views.toggle_active_api, name='toggle_active_api'),
]
