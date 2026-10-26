from django import forms

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
        fields = ['rating', 'content']
        labels = {'content': 'Ceritakan pengalamanmu'}
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 6, 'placeholder': 'Bagaimana rasa, porsi, dan kondisi makanan yang kamu terima?',
            }),
        }

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
