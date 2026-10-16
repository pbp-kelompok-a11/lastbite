from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from .forms import FoodHackForm
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


@login_required(login_url='community:login')
@require_http_methods(['GET', 'POST'])
def create_food_hack(request):
    # Add the Customer role gate once the shared auth module defines roles.
    post = CommunityPost(author=request.user, post_type=CommunityPost.PostType.FOOD_HACK)
    form = FoodHackForm(request.POST if request.method == 'POST' else None, instance=post)
    if request.method == 'POST' and form.is_valid():
        post = form.save()
        return redirect('community:post_detail', pk=post.pk)
    return render(request, 'community/food_hack_form.html', {'form': form})
