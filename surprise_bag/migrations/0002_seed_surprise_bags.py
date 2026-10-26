from django.db import migrations


def create_merchant_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    # group ini dipakai is_merchant() di views.py untuk menandai role Merchant
    Group.objects.get_or_create(name='Merchant')


def delete_merchant_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Merchant').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('surprise_bag', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_merchant_group, delete_merchant_group),
    ]
