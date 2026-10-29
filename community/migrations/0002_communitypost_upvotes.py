from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='communitypost',
            name='upvotes',
            field=models.ManyToManyField(blank=True, related_name='upvoted_community_posts', to=settings.AUTH_USER_MODEL),
        ),
    ]
