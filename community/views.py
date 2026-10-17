from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST, require_safe
from django.views.decorators.vary import vary_on_headers

from .forms import CommunityCommentForm, FoodHackForm
from .models import CommunityComment, CommunityPost
from accounts.permissions import is_customer, is_merchant


def can_use_food_hacks(user):
    return is_customer(user) or is_merchant(user)


def food_hacks_for(user):
    votes = CommunityPost.upvotes.through.objects.filter(
        communitypost_id=OuterRef('pk'), user_id=user.pk,
    )
    return CommunityPost.objects.filter(
        post_type=CommunityPost.PostType.FOOD_HACK,
    ).select_related('author__profile').annotate(
        upvote_count=Count('upvotes', distinct=True), has_upvoted=Exists(votes),
        comment_count=Count('comments', distinct=True),
    ).order_by('-created_at', '-pk')


@require_safe
@vary_on_headers('X-Requested-With')
def home(request):
    post_type = request.GET.get('post_type', 'all')
    if post_type not in ('all', CommunityPost.PostType.FOOD_HACK):
        post_type = 'all'
    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'newest')
    if sort not in ('newest', 'oldest', 'likes'):
        sort = 'newest'
    liked_only = request.GET.get('liked') == '1'
    if liked_only and not request.user.is_authenticated:
        login_url = reverse('accounts:login') + '?' + urlencode({'next': request.get_full_path()})
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'login_url': login_url}, status=401)
        return redirect(login_url)
    posts = food_hacks_for(request.user)
    if post_type != 'all':
        posts = posts.filter(post_type=post_type)
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    if liked_only:
        posts = posts.filter(has_upvoted=True)
    ordering = {
        'newest': ('-created_at', '-pk'),
        'oldest': ('created_at', 'pk'),
        'likes': ('-upvote_count', '-created_at', '-pk'),
    }
    posts = posts.order_by(*ordering[sort])
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
    if sort != 'newest':
        filter_params['sort'] = sort
    if liked_only:
        filter_params['liked'] = '1'
    clear_query = urlencode(filter_params)
    if query:
        filter_params['q'] = query
    liked_params = dict(filter_params)
    if liked_only:
        liked_params.pop('liked')
    else:
        liked_params['liked'] = '1'
    liked_url = reverse('community:home') + '?' + urlencode(liked_params)
    if not request.user.is_authenticated:
        liked_url = reverse('accounts:login') + '?' + urlencode({'next': liked_url})
    heading = 'Hasil pencarian' if query else 'Postingan yang disukai' if liked_only else 'Food Hacks' if post_type == 'food_hack' else 'Postingan komunitas'
    template = 'community/home.html'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        template = 'community/components/feed_results.html'
    return render(request, template, {
        'posts': page_obj.object_list, 'can_create_food_hack': can_use_food_hacks(request.user),
        'can_upvote': can_use_food_hacks(request.user),
        'selected_post_type': post_type, 'query': query,
        'selected_sort': sort, 'liked_only': liked_only, 'feed_heading': heading,
        'all_posts_query': urlencode({**filter_params, 'post_type': 'all'}),
        'food_hacks_query': urlencode({**filter_params, 'post_type': 'food_hack'}),
        'clear_query': clear_query, 'liked_url': liked_url,
        'page_obj': page_obj,
        'page_numbers': page_numbers,
        'filter_query': urlencode(filter_params),
        'detail_query': urlencode({'feed': urlencode({**filter_params, 'page': page_obj.number})}),
    })


def render_post_detail(request, post, form=None, editing_comment=None, replying_to=None, status=200):
    back_url = reverse('community:home')
    feed_query = request.POST.get('feed', '') if request.method == 'POST' else request.GET.get('feed', '')
    if feed_query:
        back_url += '?' + feed_query
    template = 'community/post_detail.html'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        template = 'community/components/comments.html'
    likes = CommunityComment.likes.through.objects.filter(
        communitycomment_id=OuterRef('pk'), user_id=request.user.pk,
    )
    comments = list(post.comments.select_related('author__profile', 'parent__author').annotate(
        like_count=Count('likes'), has_liked=Exists(likes),
    ).order_by('created_at', 'pk'))
    by_id = {comment.pk: comment for comment in comments}
    root_comments = []
    for comment in comments:
        comment.children_for_display = []
    for comment in comments:
        if comment.parent_id in by_id:
            by_id[comment.parent_id].children_for_display.append(comment)
        else:
            root_comments.append(comment)
    return render(request, template, {
        'post': post,
        'back_url': back_url,
        'can_manage_post': request.user == post.author and can_use_food_hacks(request.user),
        'can_upvote': can_use_food_hacks(request.user),
        'can_comment': can_use_food_hacks(request.user),
        'comments': comments, 'root_comments': root_comments,
        'latest_comment_id': comments[-1].pk if comments else '',
        'comment_form': form if form is not None and editing_comment is None and replying_to is None else CommunityCommentForm(prefix='comment'),
        'editing_comment_id': editing_comment.pk if editing_comment else None,
        'editing_form': form if editing_comment else None,
        'replying_to_id': replying_to.pk if replying_to else None,
        'reply_form': form if replying_to else None,
        'comment_feed_query': feed_query,
    }, status=status)


@require_safe
@vary_on_headers('X-Requested-With')
def post_detail(request, pk):
    post = get_object_or_404(food_hacks_for(request.user), pk=pk)
    return render_post_detail(request, post)


def comment_access_response(request, pk):
    if not request.user.is_authenticated:
        next_url = reverse('community:post_detail', args=[pk])
        if request.POST.get('feed'):
            next_url += '?' + urlencode({'feed': request.POST['feed']})
        login_url = reverse('accounts:login') + '?' + urlencode({'next': next_url + '#comments'})
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'login_url': login_url}, status=401)
        return redirect(login_url)
    if not can_use_food_hacks(request.user):
        raise PermissionDenied('Hanya Customer dan Merchant yang dapat berkomentar.')
    return None


def comment_success_response(request, post):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_post_detail(request, post)
    url = reverse('community:post_detail', args=[post.pk])
    if request.POST.get('feed'):
        url += '?' + urlencode({'feed': request.POST['feed']})
    return redirect(url + '#comments')


@require_POST
def create_comment(request, pk, parent_pk=None):
    denied = comment_access_response(request, pk)
    if denied is not None:
        return denied
    post = get_object_or_404(food_hacks_for(request.user), pk=pk)
    parent = get_object_or_404(CommunityComment, pk=parent_pk, post=post) if parent_pk is not None else None
    comment = CommunityComment(post=post, author=request.user, parent=parent)
    prefix = f'reply-{parent.pk}' if parent else 'comment'
    form = CommunityCommentForm(request.POST, instance=comment, prefix=prefix)
    if form.is_valid():
        form.save()
        return comment_success_response(request, post)
    return render_post_detail(request, post, form=form, replying_to=parent, status=400)


@require_POST
def edit_comment(request, pk, comment_pk):
    denied = comment_access_response(request, pk)
    if denied is not None:
        return denied
    post = get_object_or_404(food_hacks_for(request.user), pk=pk)
    comment = get_object_or_404(CommunityComment, pk=comment_pk, post=post, author=request.user)
    form = CommunityCommentForm(request.POST, instance=comment, prefix=f'edit-{comment.pk}')
    if form.is_valid():
        form.save()
        return comment_success_response(request, post)
    return render_post_detail(request, post, form=form, editing_comment=comment, status=400)


@require_POST
def delete_comment(request, pk, comment_pk):
    denied = comment_access_response(request, pk)
    if denied is not None:
        return denied
    post = get_object_or_404(food_hacks_for(request.user), pk=pk)
    comment = get_object_or_404(CommunityComment, pk=comment_pk, post=post, author=request.user)
    comment.delete()
    return comment_success_response(request, post)


@require_POST
def toggle_comment_like(request, pk, comment_pk):
    denied = comment_access_response(request, pk)
    if denied is not None:
        return denied
    post = get_object_or_404(food_hacks_for(request.user), pk=pk)
    with transaction.atomic():
        comment = get_object_or_404(
            CommunityComment.objects.select_for_update(), pk=comment_pk, post=post,
        )
        if comment.likes.filter(pk=request.user.pk).exists():
            comment.likes.remove(request.user)
        else:
            comment.likes.add(request.user)
    return comment_success_response(request, post)


@require_POST
def toggle_upvote(request, pk):
    if not request.user.is_authenticated:
        login_url = reverse('accounts:login') + '?' + urlencode({
            'next': reverse('community:post_detail', args=[pk]),
        })
        return JsonResponse({'error': 'Silakan login untuk memberi like.', 'login_url': login_url}, status=401)
    if not can_use_food_hacks(request.user):
        return JsonResponse({'error': 'Hanya Customer dan Merchant yang dapat memberi like.'}, status=403)
    with transaction.atomic():
        post = get_object_or_404(
            CommunityPost.objects.select_for_update(),
            pk=pk, post_type=CommunityPost.PostType.FOOD_HACK,
        )
        has_upvoted = post.upvotes.filter(pk=request.user.pk).exists()
        if has_upvoted:
            post.upvotes.remove(request.user)
        else:
            post.upvotes.add(request.user)
        count = post.upvotes.count()
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return redirect('community:post_detail', pk=pk)
    return JsonResponse({'post_id': pk, 'has_upvoted': not has_upvoted, 'upvote_count': count})


@login_required
@require_http_methods(['GET', 'POST'])
def create_food_hack(request):
    if not can_use_food_hacks(request.user):
        raise PermissionDenied('Hanya Customer dan Merchant yang dapat membuat Food Hack.')
    post = CommunityPost(author=request.user, post_type=CommunityPost.PostType.FOOD_HACK)
    form = FoodHackForm(request.POST if request.method == 'POST' else None, instance=post)
    if request.method == 'POST' and form.is_valid():
        post = form.save()
        return redirect('community:post_detail', pk=post.pk)
    return render(request, 'community/food_hack_form.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_food_hack(request, pk):
    if not can_use_food_hacks(request.user):
        raise PermissionDenied('Hanya Customer dan Merchant yang dapat mengedit Food Hack.')
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
    if not can_use_food_hacks(request.user):
        raise PermissionDenied('Hanya Customer dan Merchant yang dapat menghapus Food Hack.')
    post = get_object_or_404(
        CommunityPost, pk=pk, author=request.user,
        post_type=CommunityPost.PostType.FOOD_HACK,
    )
    if request.method == 'POST':
        post.delete()
        return redirect('community:home')
    return render(request, 'community/food_hack_confirm_delete.html', {'post': post})
