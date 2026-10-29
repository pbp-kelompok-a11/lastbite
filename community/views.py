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


FEED_SORT_OPTIONS = {
    'all': [('newest', 'Newest'), ('oldest', 'Oldest')],
    'food_hack': [('newest', 'Newest'), ('oldest', 'Oldest'), ('likes', 'Most Liked')],
    'review': [('newest', 'Newest'), ('oldest', 'Oldest'),
               ('rating_highest', 'Highest Rated'), ('rating_lowest', 'Lowest Rated')],
}

FEED_ORDERING = {
    'newest': ('-created_at', '-pk'),
    'oldest': ('created_at', 'pk'),
    'likes': ('-upvote_count', '-created_at', '-pk'),
    'rating_highest': ('-rating', '-created_at', '-pk'),
    'rating_lowest': ('rating', '-created_at', '-pk'),
}

POSTS_PER_PAGE = 10


# Bantuan request dan akses data


def is_ajax_request(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def get_feed_query(request):
    # Simpan filter untuk tombol kembali ke feed.
    if request.method == 'POST':
        return request.POST.get('feed', '')
    return request.GET.get('feed', '')


def can_use_food_hacks(user):
    return is_customer(user) or is_merchant(user)


def get_visible_posts_with_counts(user):
    # Food Hack selalu masuk feed; Review harus berasal dari pesanan yang valid.
    food_hack_filter = Q(post_type=CommunityPost.PostType.FOOD_HACK)
    verified_review_filter = Q(
        post_type=CommunityPost.PostType.REVIEW,
        related_order__status=Order.Status.COMPLETED,
        related_order__customer_id=F('author_id'),
    )

    # OuterRef menghubungkan pengecekan like ke setiap postingan pada query utama.
    user_votes = CommunityPost.upvotes.through.objects.filter(
        communitypost_id=OuterRef('pk'),
        user_id=user.pk,
    )

    return (
        CommunityPost.objects.filter(food_hack_filter | verified_review_filter)
        .select_related('author__profile', 'related_order__surprise_bag__merchant')
        .annotate(
            upvote_count=Count('upvotes', distinct=True),
            has_upvoted=Exists(user_votes),
            comment_count=Count('comments', distinct=True),
        )
        .order_by('-created_at', '-pk')
    )


def get_food_hacks_with_counts(user):
    return get_visible_posts_with_counts(user).filter(post_type=CommunityPost.PostType.FOOD_HACK)


# Feed


def read_feed_filters(request):
    # Gunakan default jika filter dari URL tidak valid.
    post_type = request.GET.get('post_type', 'all')
    if post_type not in ('all', CommunityPost.PostType.FOOD_HACK, CommunityPost.PostType.REVIEW):
        post_type = 'all'
    query = request.GET.get('q', '').strip()
    sort_options = FEED_SORT_OPTIONS
    sort = request.GET.get('sort', 'newest')
    if sort not in dict(sort_options[post_type]):
        sort = 'newest'
    liked_only = post_type == 'food_hack' and request.GET.get('liked') == '1'
    mine_only = post_type == 'all' and request.GET.get('mine') == '1'
    rating = 'all'
    if post_type == 'review':
        rating = request.GET.get('rating', 'all')
    if rating not in ('all', '1', '2', '3', '4', '5'):
        rating = 'all'
    return {
        'post_type': post_type,
        'query': query,
        'sort': sort,
        'liked_only': liked_only,
        'mine_only': mine_only,
        'rating': rating,
        'sort_options': sort_options,
    }


def filter_posts(posts, user, filters):
    post_type = filters['post_type']
    query = filters['query']
    liked_only = filters['liked_only']
    mine_only = filters['mine_only']
    rating = filters['rating']
    if mine_only:
        posts = posts.filter(author=user)
    if post_type != 'all':
        posts = posts.filter(post_type=post_type)
    # Cari di judul dan isi postingan.
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    if rating != 'all':
        posts = posts.filter(rating=int(rating))
    if liked_only:
        posts = posts.filter(has_upvoted=True)
    return posts


def sort_posts(posts, sort):
    # Awalan '-' untuk urutan menurun.
    # pk menjaga urutan saat nilai utama sama.
    return posts.order_by(*FEED_ORDERING[sort])


def get_page_numbers(page_obj):
    # Tampilkan halaman awal, akhir, dan sekitar halaman aktif.
    paginator = page_obj.paginator
    if paginator.num_pages <= 7:
        page_numbers = list(paginator.page_range)
    else:
        visible_pages = {1, paginator.num_pages}
        first_neighbor = max(1, page_obj.number - 2)
        last_neighbor = min(paginator.num_pages, page_obj.number + 2)
        visible_pages.update(range(first_neighbor, last_neighbor + 1))
        page_numbers = []
        previous = 0
        for number in sorted(visible_pages):
            if number - previous > 1:
                page_numbers.append(paginator.ELLIPSIS)
            page_numbers.append(number)
            previous = number
    return page_numbers


def build_feed_context(user, filters, page_obj):
    post_type = filters['post_type']
    query = filters['query']
    sort = filters['sort']
    liked_only = filters['liked_only']
    mine_only = filters['mine_only']
    rating = filters['rating']
    sort_options = filters['sort_options']

    # Bawa filter saat pindah halaman atau membuka detail.
    filter_params = {'post_type': post_type}
    if mine_only:
        filter_params['mine'] = '1'
    if sort != 'newest':
        filter_params['sort'] = sort
    if liked_only:
        filter_params['liked'] = '1'
    if rating != 'all':
        filter_params['rating'] = rating

    # Hapus kata kunci tanpa menghilangkan filter lain.
    clear_query = urlencode(filter_params)
    if query:
        filter_params['q'] = query

    # Saat pindah tab, reset filter yang khusus untuk kategori sebelumnya.
    tab_queries = {}
    for category in sort_options:
        params = {**filter_params, 'post_type': category}
        if category != post_type:
            params.pop('mine', None)
            params.pop('sort', None)
            params.pop('liked', None)
            params.pop('rating', None)
        tab_queries[category] = urlencode(params)

    # Tentukan judul sesuai pencarian atau filter yang sedang digunakan.
    if query:
        heading = 'Hasil pencarian'
    elif mine_only:
        heading = 'Postingan milikku'
    elif liked_only:
        heading = 'Postingan yang disukai'
    elif post_type == 'food_hack':
        heading = 'Food Hacks'
    elif post_type == 'review':
        heading = 'Reviews'
    else:
        heading = 'Postingan komunitas'

    search_label, search_placeholder = {
        'all': ('Search Community', 'Search Community...'),
        'food_hack': ('Search Food Hacks', 'Search Food Hacks...'),
        'review': ('Search Reviews', 'Search Reviews...'),
    }[post_type]

    # URL detail menyimpan filter dan halaman agar tombol kembali tidak kehilangan posisi.
    feed_params = {**filter_params, 'page': page_obj.number}
    detail_query = urlencode({'feed': urlencode(feed_params)})

    return {
        # Data postingan dan izin aksi.
        'posts': page_obj.object_list,
        'can_create_food_hack': can_use_food_hacks(user),
        'can_upvote': can_use_food_hacks(user),

        # Nilai kontrol yang ditampilkan pada halaman.
        'selected_post_type': post_type,
        'query': query,
        'selected_sort': sort,
        'liked_only': liked_only,
        'mine_only': mine_only,
        'feed_heading': heading,
        'sort_options': sort_options[post_type],
        'selected_rating': rating,
        'rating_options': ['5', '4', '3', '2', '1'],
        'search_label': search_label,
        'search_placeholder': search_placeholder,

        # Tautan tab dan navigasi halaman.
        'all_posts_query': tab_queries['all'],
        'food_hacks_query': tab_queries['food_hack'],
        'reviews_query': tab_queries['review'],
        'clear_query': clear_query,
        'page_obj': page_obj,
        'page_numbers': get_page_numbers(page_obj),
        'filter_query': urlencode(filter_params),
        'detail_query': detail_query,
    }


@require_safe
@vary_on_headers('X-Requested-With')
def home(request):
    filters = read_feed_filters(request)

    # Filter milik sendiri dan disukai memerlukan login.
    needs_login = filters['liked_only'] or filters['mine_only']
    if needs_login and not request.user.is_authenticated:
        login_url = reverse('accounts:login') + '?' + urlencode({'next': request.get_full_path()})
        if is_ajax_request(request):
            return JsonResponse({'login_url': login_url}, status=401)
        return redirect(login_url)

    posts = get_visible_posts_with_counts(request.user)
    posts = filter_posts(posts, request.user, filters)
    posts = sort_posts(posts, filters['sort'])
    page_obj = Paginator(posts, POSTS_PER_PAGE).get_page(request.GET.get('page'))
    context = build_feed_context(request.user, filters, page_obj)

    # Untuk AJAX, kirim bagian feed saja.
    template = 'community/home.html'
    if is_ajax_request(request):
        template = 'community/components/feed_results.html'
    return render(request, template, context)


# Detail Food Hack dan komentar bertingkat


def get_comments_with_replies(post, user):
    # Ambil komentar sekaligus, lalu susun balasannya.
    likes = CommunityComment.likes.through.objects.filter(
        communitycomment_id=OuterRef('pk'), user_id=user.pk,
    )
    comments = list(
        post.comments.select_related('author__profile', 'parent__author')
        .annotate(
            like_count=Count('likes'),
            has_liked=Exists(likes),
        )
        .order_by('created_at', 'pk')
    )
    # Susun relasi induk dan balasan dari data yang sudah diambil.
    comments_by_id = {comment.pk: comment for comment in comments}
    root_comments = []

    for comment in comments:
        comment.children_for_display = []

    for comment in comments:
        if comment.parent_id in comments_by_id:
            comments_by_id[comment.parent_id].children_for_display.append(comment)
        else:
            root_comments.append(comment)

    return comments, root_comments


def render_post_detail(request, post, form=None, editing_comment=None, replying_to=None, status=200):
    back_url = reverse('community:home')
    feed_query = get_feed_query(request)
    if feed_query:
        back_url += '?' + feed_query
    template = 'community/food_hack_detail.html'
    if is_ajax_request(request):
        template = 'community/components/comments.html'
    comments, root_comments = get_comments_with_replies(post, request.user)
    comment_form = CommunityCommentForm(prefix='comment')
    if form is not None and editing_comment is None and replying_to is None:
        comment_form = form
    return render(request, template, {
        'post': post,
        'back_url': back_url,
        'can_manage_post': request.user == post.author and can_use_food_hacks(request.user),
        'can_upvote': can_use_food_hacks(request.user),
        'can_comment': can_use_food_hacks(request.user),
        'comments': comments,
        'root_comments': root_comments,
        'latest_comment_id': comments[-1].pk if comments else '',
        'comment_form': comment_form,
        'editing_comment_id': editing_comment.pk if editing_comment else None,
        'editing_form': form if editing_comment else None,
        'replying_to_id': replying_to.pk if replying_to else None,
        'reply_form': form if replying_to else None,
        'comment_feed_query': feed_query,
    }, status=status)


@require_safe
@vary_on_headers('X-Requested-With')
def post_detail(request, pk):
    post = get_object_or_404(get_food_hacks_with_counts(request.user), pk=pk)
    return render_post_detail(request, post)


def comment_access_response(request, pk):
    # None berarti user boleh melanjutkan.
    if not request.user.is_authenticated:
        next_url = reverse('community:post_detail', args=[pk])
        if request.POST.get('feed'):
            next_url += '?' + urlencode({'feed': request.POST['feed']})
        login_url = reverse('accounts:login') + '?' + urlencode({'next': next_url + '#comments'})
        if is_ajax_request(request):
            return JsonResponse({'login_url': login_url}, status=401)
        return redirect(login_url)
    if not can_use_food_hacks(request.user):
        raise PermissionDenied('Hanya Customer dan Merchant yang dapat berkomentar.')
    return None


def comment_success_response(request, post):
    # AJAX menerima komentar terbaru; request biasa diarahkan ke detail.
    if is_ajax_request(request):
        return render_post_detail(request, post)
    url = reverse('community:post_detail', args=[post.pk])
    if request.POST.get('feed'):
        url += '?' + urlencode({'feed': request.POST['feed']})
    return redirect(url + '#comments')


@require_POST
def create_comment(request, pk, parent_pk=None):
    # parent_pk terisi jika komentar ini adalah balasan.
    denied = comment_access_response(request, pk)
    if denied is not None:
        return denied
    post = get_object_or_404(get_food_hacks_with_counts(request.user), pk=pk)
    parent = None
    if parent_pk is not None:
        parent = get_object_or_404(CommunityComment, pk=parent_pk, post=post)
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
    post = get_object_or_404(get_food_hacks_with_counts(request.user), pk=pk)
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
    post = get_object_or_404(get_food_hacks_with_counts(request.user), pk=pk)
    comment = get_object_or_404(CommunityComment, pk=comment_pk, post=post, author=request.user)
    comment.delete()
    return comment_success_response(request, post)


@require_POST
def toggle_comment_like(request, pk, comment_pk):
    denied = comment_access_response(request, pk)
    if denied is not None:
        return denied
    post = get_object_or_404(get_food_hacks_with_counts(request.user), pk=pk)
    with transaction.atomic():
        comment = get_object_or_404(
            CommunityComment.objects.select_for_update(), pk=comment_pk, post=post,
        )
        if comment.likes.filter(pk=request.user.pk).exists():
            comment.likes.remove(request.user)
        else:
            comment.likes.add(request.user)
    return comment_success_response(request, post)


# Like postingan


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
    if not is_ajax_request(request):
        return redirect('community:post_detail', pk=pk)
    return JsonResponse({'post_id': pk, 'has_upvoted': not has_upvoted, 'upvote_count': count})


# Food Hack: tambah, edit, hapus


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
    # Hanya ambil postingan milik user.
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
        'form': form,
        'post': post,
        'is_edit': True,
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


# Review pesanan dan balasan Merchant


def save_review_for_completed_order(form, user):
    # Kunci pesanan agar request bersamaan tidak membuat review ganda.
    # Tangani juga duplikasi yang ditolak database.
    try:
        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(), pk=form.cleaned_data['related_order'].pk,
                customer=user, status=Order.Status.COMPLETED,
            )
            if CommunityPost.objects.filter(related_order=order, post_type='review').exists():
                form.add_error('related_order', 'Pesanan ini sudah memiliki review.')
            else:
                form.save()
    except IntegrityError:
        form.add_error('related_order', 'Pesanan ini sudah memiliki review.')


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
        save_review_for_completed_order(form, request.user)
        post = form.instance
        if not form.errors:
            if is_ajax_request(request):
                return JsonResponse({'detail_url': reverse('community:review_detail', args=[post.pk]),
                                     'message': 'Review berhasil disimpan.'}, status=201)
            return redirect('community:review_detail', pk=post.pk)
    if request.method == 'POST' and is_ajax_request(request):
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return render(request, 'community/review_form.html', {
        'form': form,
        'has_eligible_orders': form.fields['related_order'].queryset.exists(),
    })


def can_reply_to_review(user, post):
    return (
        is_merchant(user)
        and post.is_verified_purchase
        and post.related_order.surprise_bag.merchant_id == user.pk
    )


def render_review_detail(request, post, reply_form=None, status=200):
    reply = MerchantReviewReply.objects.filter(review=post).select_related('merchant').first()
    can_reply = can_reply_to_review(request.user, post)
    if can_reply and reply_form is None:
        reply_form = ReviewReplyForm(instance=reply)
    back_url = reverse('community:home')
    feed_query = get_feed_query(request)
    if feed_query:
        back_url += '?' + feed_query
    return render(request, 'community/review_detail.html', {
        'post': post,
        'back_url': back_url,
        'reply': reply,
        'can_reply': can_reply,
        'reply_form': reply_form,
        'reply_dialog_open': bool(reply_form and reply_form.is_bound),
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
    # Perbarui balasan jika sudah ada.
    with transaction.atomic():
        post = get_object_or_404(
            CommunityPost.objects.select_for_update(), pk=pk, post_type=CommunityPost.PostType.REVIEW,
        )
        if not can_reply_to_review(request.user, post):
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
