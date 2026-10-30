from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('', include('main.urls')),              # Landing page
    path('bags/', include('surprise_bag.urls')),  # Surprise Bag module
    path('orders/', include('order.urls')),       # Order module
    path('stores/', include('merchant_store.urls')),  # Merchant Store module
    path('community/', include('community.urls')),    # Community module
    path('eco-impact/', include('eco_impact.urls')),  # Eco Impact module

    # Foto unggahan (profil, toko, Surprise Bag) selalu dilayani, juga saat DEBUG=False
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]