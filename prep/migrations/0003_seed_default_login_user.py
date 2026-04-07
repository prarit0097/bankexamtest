from django.db import migrations
from django.contrib.auth.hashers import make_password


DEFAULT_USERNAME = "chahat@gmail.com"
DEFAULT_PASSWORD = "Chahat@123"


def seed_default_login_user(apps, schema_editor):
    User = apps.get_model("auth", "User")
    user, created = User.objects.get_or_create(
        username=DEFAULT_USERNAME,
        defaults={
            "email": DEFAULT_USERNAME,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )
    changed = created
    if user.email != DEFAULT_USERNAME:
        user.email = DEFAULT_USERNAME
        changed = True
    if not user.is_staff:
        user.is_staff = True
        changed = True
    if not user.is_superuser:
        user.is_superuser = True
        changed = True
    if not user.is_active:
        user.is_active = True
        changed = True
    user.password = make_password(DEFAULT_PASSWORD)
    changed = True
    if changed:
        user.save()


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("prep", "0002_uploadbatch_contentasset_upload_batch"),
    ]

    operations = [
        migrations.RunPython(seed_default_login_user, noop_reverse),
    ]
