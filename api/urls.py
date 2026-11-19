"""Rute API untuk aplikasi Flutter."""

from django.urls import path

from community.api import FoodHackList, VerifiedReviewList
from eco_impact.api import ImpactLogList
from merchant_store.api import MerchantStoreList
from order.api import OrderList
from surprise_bag.api import SurpriseBagList

from .views import LoginView, LogoutView, MeView, RegisterView, api_root

app_name = "api"

urlpatterns = [
    path("", api_root, name="root"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("surprise-bags/", SurpriseBagList.as_view(), name="surprise-bags"),
    path("orders/", OrderList.as_view(), name="orders"),
    path("merchant-stores/", MerchantStoreList.as_view(), name="merchant-stores"),
    path("community/food-hacks/", FoodHackList.as_view(), name="food-hacks"),
    path("community/reviews/", VerifiedReviewList.as_view(), name="verified-reviews"),
    path("eco-impact/logs/", ImpactLogList.as_view(), name="impact-logs"),
]
