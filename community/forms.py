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
