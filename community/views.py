from urllib.parse import urlencode
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Exists, F, OuterRef, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST, require_safe
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import never_cache

from .forms import CommunityCommentForm, FoodHackForm, ReviewForm, ReviewReplyForm
from .models import CommunityComment, CommunityPost, MerchantReviewReply
from accounts.permissions import is_customer, is_merchant
from order.models import Order


def can_use_food_hacks(user):
    return is_customer(user) or is_merchant(user)


def posts_for(user):
    votes = CommunityPost.upvotes.through.objects.filter(
        communitypost_id=OuterRef('pk'), user_id=user.pk,
    )
    return CommunityPost.objects.filter(
        Q(post_type=CommunityPost.PostType.FOOD_HACK)
        | Q(post_type=CommunityPost.PostType.REVIEW, related_order__status=Order.Status.COMPLETED,
            related_order__customer_id=F('author_id'))
    ).select_related('author__profile', 'related_order__surprise_bag__merchant').annotate(
        upvote_count=Count('upvotes', distinct=True), has_upvoted=Exists(votes),
        comment_count=Count('comments', distinct=True),
    ).order_by('-created_at', '-pk')


def food_hacks_for(user):
    return posts_for(user).filter(post_type=CommunityPost.PostType.FOOD_HACK)


@require_safe
@vary_on_headers('X-Requested-With')
def home(request):
    post_type = request.GET.get('post_type', 'all')
    if post_type not in ('all', CommunityPost.PostType.FOOD_HACK, CommunityPost.PostType.REVIEW):
        post_type = 'all'
    query = request.GET.get('q', '').strip()
    sort_options = {
        'all': [('newest', 'Newest'), ('oldest', 'Oldest')],
        'food_hack': [('newest', 'Newest'), ('oldest', 'Oldest'), ('likes', 'Most Liked')],
        'review': [('newest', 'Newest'), ('oldest', 'Oldest'),
                   ('rating_highest', 'Highest Rated'), ('rating_lowest', 'Lowest Rated')],
    }
    sort = request.GET.get('sort', 'newest')
    if sort not in dict(sort_options[post_type]):
        sort = 'newest'
    liked_only = post_type == 'food_hack' and request.GET.get('liked') == '1'
    mine_only = post_type == 'all' and request.GET.get('mine') == '1'
    rating = request.GET.get('rating', 'all') if post_type == 'review' else 'all'
    if rating not in ('all', '1', '2', '3', '4', '5'):
        rating = 'all'
    if (liked_only or mine_only) and not request.user.is_authenticated:
        login_url = reverse('accounts:login') + '?' + urlencode({'next': request.get_full_path()})
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'login_url': login_url}, status=401)
        return redirect(login_url)
    posts = posts_for(request.user)
    if mine_only:
        posts = posts.filter(author=request.user)
    if post_type != 'all':
        posts = posts.filter(post_type=post_type)
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    if rating != 'all':
        posts = posts.filter(rating=int(rating))
    if liked_only:
        posts = posts.filter(has_upvoted=True)
    ordering = {
        'newest': ('-created_at', '-pk'),
        'oldest': ('created_at', 'pk'),
        'likes': ('-upvote_count', '-created_at', '-pk'),
        'rating_highest': ('-rating', '-created_at', '-pk'),
        'rating_lowest': ('rating', '-created_at', '-pk'),
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
    if mine_only:
        filter_params['mine'] = '1'
    if sort != 'newest':
        filter_params['sort'] = sort
    if liked_only:
        filter_params['liked'] = '1'
    if rating != 'all':
        filter_params['rating'] = rating
    clear_query = urlencode(filter_params)
    if query:
        filter_params['q'] = query
    tab_queries = {}
    for category in sort_options:
        params = {**filter_params, 'post_type': category}
        if category != post_type:
            params.pop('mine', None)
            params.pop('sort', None)
            params.pop('liked', None)
            params.pop('rating', None)
        tab_queries[category] = urlencode(params)
    heading = 'Hasil pencarian' if query else 'Postingan yang disukai' if liked_only else 'Food Hacks' if post_type == 'food_hack' else 'Reviews' if post_type == 'review' else 'Postingan komunitas'
    if mine_only and not query:
        heading = {'all': 'Postingan milikku', 'food_hack': 'Food Hacks milikku', 'review': 'Reviews milikku'}[post_type]
    search_label, search_placeholder = {
        'all': ('Search Community', 'Search Community...'),
        'food_hack': ('Search Food Hacks', 'Search Food Hacks...'),
        'review': ('Search Reviews', 'Search Reviews...'),
    }[post_type]
    template = 'community/home.html'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        template = 'community/components/feed_results.html'
    return render(request, template, {
        'posts': page_obj.object_list, 'can_create_food_hack': can_use_food_hacks(request.user),
        'can_upvote': can_use_food_hacks(request.user),
        'selected_post_type': post_type, 'query': query,
        'selected_sort': sort, 'liked_only': liked_only, 'mine_only': mine_only, 'feed_heading': heading,
        'sort_options': sort_options[post_type],
        'selected_rating': rating, 'rating_options': ['5', '4', '3', '2', '1'],
        'search_label': search_label, 'search_placeholder': search_placeholder,
        'all_posts_query': tab_queries['all'],
        'food_hacks_query': tab_queries['food_hack'],
        'reviews_query': tab_queries['review'],
        'clear_query': clear_query,
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
    template = 'community/food_hack_detail.html'
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


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def create_review(request):
    if not is_customer(request.user):
        raise PermissionDenied('Hanya Customer yang dapat menulis review.')
    post = CommunityPost(
        author=request.user, post_type=CommunityPost.PostType.REVIEW,
        title='Review pesanan',
    )
    form = ReviewForm(
        request.POST if request.method == 'POST' else None,
        instance=post, user=request.user,
    )
    if request.method == 'GET' and request.GET.get('order'):
        try:
            order_id = UUID(request.GET['order'])
        except ValueError:
            raise Http404
        selected_order = get_object_or_404(
            Order.objects.select_related('surprise_bag__merchant'),
            pk=order_id, customer=request.user, status=Order.Status.COMPLETED,
        )
        existing = CommunityPost.objects.filter(related_order=selected_order, post_type='review').first()
        if existing:
            return redirect('community:review_detail', pk=existing.pk)
        form.initial['related_order'] = selected_order.pk
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                order = get_object_or_404(
                    Order.objects.select_for_update(), pk=form.cleaned_data['related_order'].pk,
                    customer=request.user, status=Order.Status.COMPLETED,
                )
                if CommunityPost.objects.filter(related_order=order, post_type='review').exists():
                    form.add_error('related_order', 'Pesanan ini sudah memiliki review.')
                else:
                    post = form.save()
        except IntegrityError:
            form.add_error('related_order', 'Pesanan ini sudah memiliki review.')
        if not form.errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'detail_url': reverse('community:review_detail', args=[post.pk]),
                                     'message': 'Review berhasil disimpan.'}, status=201)
            return redirect('community:review_detail', pk=post.pk)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return render(request, 'community/review_form.html', {
        'form': form,
        'has_eligible_orders': form.fields['related_order'].queryset.exists(),
    })


def render_review_detail(request, post, reply_form=None, status=200):
    reply = MerchantReviewReply.objects.filter(review=post).select_related('merchant').first()
    can_reply = (
        is_merchant(request.user) and post.is_verified_purchase
        and post.related_order.surprise_bag.merchant_id == request.user.pk
    )
    if can_reply and reply_form is None:
        reply_form = ReviewReplyForm(instance=reply)
    back_url = reverse('community:home')
    feed_query = request.POST.get('feed', '') if request.method == 'POST' else request.GET.get('feed', '')
    if feed_query:
        back_url += '?' + feed_query
    return render(request, 'community/review_detail.html', {
        'post': post, 'back_url': back_url, 'reply': reply, 'can_reply': can_reply,
        'reply_form': reply_form, 'reply_dialog_open': bool(reply_form and reply_form.is_bound),
        'feed_query': feed_query,
    }, status=status)


@require_safe
def review_detail(request, pk):
    post = get_object_or_404(
        CommunityPost.objects.select_related('author', 'related_order__surprise_bag__merchant'),
        pk=pk, post_type=CommunityPost.PostType.REVIEW,
        related_order__status=Order.Status.COMPLETED, related_order__customer_id=F('author_id'),
    )
    return render_review_detail(request, post)


@login_required
@require_POST
def reply_review(request, pk):
    with transaction.atomic():
        post = get_object_or_404(
            CommunityPost.objects.select_for_update(), pk=pk, post_type=CommunityPost.PostType.REVIEW,
        )
        if not (is_merchant(request.user) and post.is_verified_purchase
                and post.related_order.surprise_bag.merchant_id == request.user.pk):
            raise PermissionDenied('Hanya Merchant pemilik pesanan yang dapat membalas Review ini.')
        reply = MerchantReviewReply.objects.filter(review=post).first()
        form = ReviewReplyForm(request.POST, instance=reply or MerchantReviewReply(
            review=post, merchant=request.user,
        ))
        if not form.is_valid():
            return render_review_detail(request, post, reply_form=form, status=400)
        form.save()
    url = reverse('community:review_detail', args=[post.pk])
    if request.POST.get('feed'):
        url += '?' + urlencode({'feed': request.POST['feed']})
    return redirect(url + '#merchant-reply')
