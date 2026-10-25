"""
URL configuration for lastbite project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('', include('main.urls')),              # Landing page
    path('bags/', include('surprise_bag.urls')),  # Surprise Bag module
    path('orders/', include('order.urls')),       # Order module
        path('stores/', include('merchant_store.urls')),  # Merchant Store module
    path('community/', include('community.urls')),    # Community module
    path('eco/', include('eco_impact.urls')),         # Eco Impact module
]
