from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe
from django.views.decorators.vary import vary_on_headers

from .forms import FoodHackForm
from .models import CommunityPost
from accounts.permissions import is_customer


@require_safe
@vary_on_headers('X-Requested-With')
def home(request):
    post_type = request.GET.get('post_type', 'all')
    if post_type not in ('all', CommunityPost.PostType.FOOD_HACK):
        post_type = 'all'
    query = request.GET.get('q', '').strip()
    # Only Food Hacks are public until verified Order reviews are integrated.
    posts = CommunityPost.objects.filter(
        post_type=CommunityPost.PostType.FOOD_HACK,
    ).select_related('author')
    if post_type != 'all':
        posts = posts.filter(post_type=post_type)
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    if paginator.num_pages <= 7:
        page_numbers = list(paginator.page_range)
    else:
        visible_pages = {1, paginator.num_pages}
        visible_pages.update(range(max(1, page_obj.number - 2), min(paginator.num_pages, page_obj.number + 2) + 1))
        page_numbers = []
        previous = 0
        for number in sorted(visible_pages):
            if number - previous > 1:
                page_numbers.append(paginator.ELLIPSIS)
            page_numbers.append(number)
            previous = number
    filter_params = {'post_type': post_type}
    if query:
        filter_params['q'] = query
    template = 'community/home.html'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        template = 'community/components/feed_results.html'
    return render(request, template, {
        'posts': page_obj.object_list, 'can_create_food_hack': is_customer(request.user),
        'selected_post_type': post_type, 'query': query,
        'page_obj': page_obj,
        'page_numbers': page_numbers,
        'filter_query': urlencode(filter_params),
    })


@require_safe
def post_detail(request, pk):
    post = get_object_or_404(
        CommunityPost.objects.select_related('author'),
        pk=pk,
        post_type=CommunityPost.PostType.FOOD_HACK,
    )
    return render(request, 'community/post_detail.html', {
        'post': post,
        'can_manage_post': request.user == post.author and is_customer(request.user),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def create_food_hack(request):
    if not is_customer(request.user):
        raise PermissionDenied('Hanya Customer yang dapat membuat Food Hack.')
    post = CommunityPost(author=request.user, post_type=CommunityPost.PostType.FOOD_HACK)
    form = FoodHackForm(request.POST if request.method == 'POST' else None, instance=post)
    if request.method == 'POST' and form.is_valid():
        post = form.save()
        return redirect('community:post_detail', pk=post.pk)
    return render(request, 'community/food_hack_form.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_food_hack(request, pk):
    if not is_customer(request.user):
        raise PermissionDenied('Hanya Customer yang dapat mengedit Food Hack.')
    post = get_object_or_404(
        CommunityPost, pk=pk, author=request.user,
        post_type=CommunityPost.PostType.FOOD_HACK,
    )
    form = FoodHackForm(request.POST if request.method == 'POST' else None, instance=post)
    if request.method == 'POST' and form.is_valid():
        post = form.save()
        return redirect('community:post_detail', pk=post.pk)
    return render(request, 'community/food_hack_form.html', {
        'form': form, 'post': post, 'is_edit': True,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def delete_food_hack(request, pk):
    if not is_customer(request.user):
        raise PermissionDenied('Hanya Customer yang dapat menghapus Food Hack.')
    post = get_object_or_404(
        CommunityPost, pk=pk, author=request.user,
        post_type=CommunityPost.PostType.FOOD_HACK,
    )
    if request.method == 'POST':
        post.delete()
        return redirect('community:home')
    return render(request, 'community/food_hack_confirm_delete.html', {'post': post})
