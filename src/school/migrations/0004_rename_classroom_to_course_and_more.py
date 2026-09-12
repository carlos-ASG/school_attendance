from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='attendancesession',
            name='unique_session_classroom_date',
        ),
        migrations.RenameModel(old_name='Classroom', new_name='Course'),
        migrations.RenameField(
            model_name='classschedule',
            old_name='classroom',
            new_name='course',
        ),
        migrations.RenameField(
            model_name='attendancesession',
            old_name='classroom',
            new_name='course',
        ),
        migrations.AlterField(
            model_name='course',
            name='student_group',
            field=models.ForeignKey(
                on_delete=models.PROTECT,
                related_name='courses',
                to='school.studentgroup',
                verbose_name='Grupo de estudiantes',
            ),
        ),
        migrations.AlterField(
            model_name='course',
            name='teacher',
            field=models.ForeignKey(
                on_delete=models.PROTECT,
                related_name='courses',
                to='school.teacher',
                verbose_name='Profesor',
            ),
        ),
        migrations.AlterField(
            model_name='course',
            name='subject',
            field=models.ForeignKey(
                on_delete=models.PROTECT,
                related_name='courses',
                to='school.subject',
                verbose_name='Materia',
            ),
        ),
        migrations.AlterField(
            model_name='classschedule',
            name='course',
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name='schedule_slots',
                to='school.course',
                verbose_name='Curso',
            ),
        ),
        migrations.AlterField(
            model_name='attendancesession',
            name='course',
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name='sessions',
                to='school.course',
                verbose_name='Curso',
            ),
        ),
        migrations.AddField(
            model_name='course',
            name='classroom',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Aula'),
        ),
        migrations.AddField(
            model_name='course',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, blank=True, null=True, verbose_name='Última actualización'
            ),
        ),
        migrations.AddField(
            model_name='attendancesession',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, blank=True, null=True, verbose_name='Última actualización'
            ),
        ),
        migrations.RemoveField(
            model_name='attendancesession',
            name='notes',
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='notes',
            field=models.TextField(blank=True, default='', verbose_name='Notas'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, blank=True, null=True, verbose_name='Última actualización'
            ),
        ),
    ]
