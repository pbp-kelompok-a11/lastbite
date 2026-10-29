import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0003_communitycomment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='communitycomment',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_community_comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='communitycomment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replies', to='community.communitycomment'),
        ),
    ]
