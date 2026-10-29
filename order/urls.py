from django.urls import path
from . import views

app_name = 'order'
urlpatterns = [
    path('', views.order_list, name='list'),
    path('create/<uuid:bag_id>/', views.create_order, name='create'),
    path('api/', views.orders_api, name='orders_api'),
    path('api/<uuid:pk>/<str:action>/', views.update_order_api, name='update_api'),
]
