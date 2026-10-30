from django.urls import path

from . import views

app_name = 'merchant_store'

urlpatterns = [
    # Direktori publik + API asinkron
    path('', views.store_list, name='list'),
    path('api/search/', views.store_search_api, name='api_search'),
    path('api/geocode/', views.geocode_api, name='api_geocode'),

    # Kelola toko (Merchant)
    path('my/', views.my_store, name='my_store'),
    path('my/create/', views.store_create, name='create'),
    path('my/edit/', views.store_edit, name='edit'),
    path('my/toggle-active/', views.store_toggle_active, name='toggle_active'),
    path('my/delete/', views.store_delete, name='delete'),

    # Wishlist (Customer)
    path('wishlist/', views.wishlist_list, name='wishlist'),
    path('wishlist/reminder/toggle/', views.reminder_toggle, name='reminder_toggle'),
    path('<int:pk>/wishlist/toggle/', views.wishlist_toggle, name='wishlist_toggle'),

    # Rating toko (khusus Customer)
    path('<int:pk>/rate/', views.store_rate, name='rate'),

    # Detail toko (publik)
    path('<int:pk>/', views.store_detail, name='detail'),

]
