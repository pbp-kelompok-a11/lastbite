from django.shortcuts import render
from django.views.decorators.http import require_safe

from .models import CommunityPost


@require_safe
def home(request):
    posts = CommunityPost.objects.filter(
        post_type=CommunityPost.PostType.FOOD_HACK,
    ).select_related('author')
    return render(request, 'community/home.html', {'posts': posts})
