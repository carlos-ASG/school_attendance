from django.db import migrations


READ_ONLY_GROUP = 'Administradores de solo lectura'


def create_read_only_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    group, _ = Group.objects.get_or_create(name=READ_ONLY_GROUP)
    view_permission_ids = Permission.objects.filter(
        content_type__app_label='school', codename__startswith='view_'
    ).values_list('id', flat=True)
    group.permissions.set(view_permission_ids)


def delete_read_only_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=READ_ONLY_GROUP).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0005_alter_classschedule_options_alter_course_options_and_more'),
    ]

    operations = [
        migrations.RunPython(create_read_only_group, delete_read_only_group),
    ]
