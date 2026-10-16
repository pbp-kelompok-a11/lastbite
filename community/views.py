from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

from .models import CommunityPost


@require_safe
def home(request):
    posts = CommunityPost.objects.filter(
        post_type=CommunityPost.PostType.FOOD_HACK,
    ).select_related('author')
    return render(request, 'community/home.html', {'posts': posts})


@require_safe
def post_detail(request, pk):
    post = get_object_or_404(
        CommunityPost.objects.select_related('author'),
        pk=pk,
        post_type=CommunityPost.PostType.FOOD_HACK,
    )
    return render(request, 'community/post_detail.html', {'post': post})
