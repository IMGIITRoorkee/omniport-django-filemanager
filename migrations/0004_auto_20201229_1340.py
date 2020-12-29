# Generated by Django 3.0.3 on 2020-12-29 08:10

import django.core.files.storage
from django.db import migrations, models
import django_filemanager.upload_to
import formula_one.utils.upload_to


class Migration(migrations.Migration):

    dependencies = [
        ('django_filemanager', '0003_auto_20201228_1642'),
    ]

    operations = [
        migrations.AddField(
            model_name='filemanager',
            name='base_public_url',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='upload',
            field=models.FileField(max_length=1000000, storage=django.core.files.storage.FileSystemStorage(location='/personal_files'), upload_to=django_filemanager.upload_to.UploadTo('', '', file_manager=True)),
        ),
        migrations.AlterField(
            model_name='filemanager',
            name='logo',
            field=models.ImageField(null=True, storage=django.core.files.storage.FileSystemStorage(base_url='/api/django_filemanager/media_files/', location='/network_storage'), upload_to=formula_one.utils.upload_to.UploadTo('', 'filemanager_logos', file_manager=False)),
        ),
    ]