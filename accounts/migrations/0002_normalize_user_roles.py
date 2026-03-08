from django.db import migrations, models


def normalize_user_roles(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')

    for user in CustomUser.objects.all():
        normalized_role = (user.role or '').lower()
        if normalized_role in {'admin', 'manager', 'staff'} and user.role != normalized_role:
            user.role = normalized_role
            user.save(update_fields=['role'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(normalize_user_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(
                choices=[('admin', 'Admin'), ('manager', 'Manager'), ('staff', 'Staff')],
                default='staff',
                max_length=20,
            ),
        ),
    ]
