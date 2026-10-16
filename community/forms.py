from django import forms

from .models import CommunityPost


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
