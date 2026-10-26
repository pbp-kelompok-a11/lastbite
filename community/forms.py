from django import forms

from order.models import Order

from .models import CommunityComment, CommunityPost


class FoodHackForm(forms.ModelForm):
    class Meta:
        model = CommunityPost
        fields = ['title', 'content']
        labels = {'title': 'Judul', 'content': 'Konten'}
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Contoh: Cara menyimpan roti surplus'}),
            'content': forms.Textarea(attrs={
                'rows': 8, 'placeholder': 'Ceritakan tips dan langkah-langkahnya di sini.',
            }),
        }


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(number, f'{number} bintang') for number in range(1, 6)],
        coerce=int, widget=forms.RadioSelect, label='Bagaimana pengalamanmu?',
        error_messages={'required': 'Pilih rating bintang terlebih dahulu.'},
    )

    class Meta:
        model = CommunityPost
        fields = ['related_order', 'rating', 'content']
        labels = {'related_order': 'Pesanan yang diulas', 'content': 'Ceritakan pengalamanmu'}
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 6, 'placeholder': 'Bagaimana rasa, porsi, dan kondisi makanan yang kamu terima?',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['related_order'].required = True
        orders = Order.objects.none()
        if user is not None:
            orders = Order.objects.filter(
                customer=user, status=Order.Status.COMPLETED,
            ).exclude(
                community_posts__post_type=CommunityPost.PostType.REVIEW,
            ).select_related('surprise_bag__merchant')
        self.fields['related_order'].queryset = orders
        self.fields['related_order'].label_from_instance = lambda order: (
            f'{order.food_name} | {order.surprise_bag.merchant_name} | '
            f'{order.pickup_date:%d/%m/%Y} | {str(order.pk)[:8]}'
        )

    def clean(self):
        cleaned = super().clean()
        order = cleaned.get('related_order')
        if order:
            self.instance.title = f'Review {order.food_name}'
        return cleaned


class CommunityCommentForm(forms.ModelForm):
    class Meta:
        model = CommunityComment
        fields = ['content']
        labels = {'content': 'Komentar'}
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3, 'maxlength': 2000,
                'placeholder': 'Bagikan pendapat atau pengalamanmu tentang tips ini.',
            }),
        }
