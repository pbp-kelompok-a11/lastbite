from django.urls import path

from . import views

app_name = 'community'
urlpatterns = [
    path('', views.home, name='home'),
    path('food-hacks/create/', views.create_food_hack, name='food_hack_create'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),
    path('posts/<int:pk>/upvote/', views.toggle_upvote, name='post_upvote'),
    path('posts/<int:pk>/edit/', views.edit_food_hack, name='post_edit'),
    path('posts/<int:pk>/delete/', views.delete_food_hack, name='post_delete'),
]
