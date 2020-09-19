# Generated by Django 3.0.3 on 2020-09-19 19:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_filemanager', '0003_auto_20200918_1303'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='folder',
            name='name',
        ),
        migrations.AddField(
            model_name='folder',
            name='folder_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='folder',
            name='content_size',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='folder',
            name='max_space',
            field=models.IntegerField(blank=True, default=1024),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='folder',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='folders', to='django_filemanager.Folder'),
        ),
    ]
