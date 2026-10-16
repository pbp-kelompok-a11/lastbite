from django.contrib import admin

from .models import CommunityPost


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'post_type', 'author', 'rating', 'created_at')
    list_filter = ('post_type', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    list_select_related = ('author',)
    readonly_fields = ('created_at', 'updated_at')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Reviews become available after completed-order validation is integrated.
        form.base_fields['post_type'].choices = [CommunityPost.PostType.choices[0]]
        return form
