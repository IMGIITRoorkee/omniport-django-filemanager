# Generated by Django 3.0.3 on 2020-12-14 13:02

from django.conf import settings
import django.contrib.postgres.fields
import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import formula_one.utils.upload_to
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.KERNEL_PERSON_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FileManager',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('datetime_modified', models.DateTimeField(auto_now=True)),
                ('filemanager_name', models.CharField(default='undedfined filemanager', max_length=50)),
                ('filemanager_url_path', models.CharField(max_length=50, null=True)),
                ('folder_name_template', models.CharField(max_length=200, null=True)),
                ('filemanager_access_roles', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('Student', 'Student'), ('FacultyMember', 'FacultyMember'), ('Maintainer', 'Maintainer'), ('Guest', 'Guest')], max_length=50), size=None)),
                ('filemanager_extra_space_options', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), null=True, size=None)),
                ('logo', models.ImageField(null=True, storage=django.core.files.storage.FileSystemStorage(base_url='/api/django_filemanager/media_files/', location='/network_storage'), upload_to=formula_one.utils.upload_to.UploadTo('', 'filemanager_logos', file_manager=True))),
                ('max_space', models.BigIntegerField(null=True)),
                ('is_public', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('datetime_modified', models.DateTimeField(auto_now=True)),
                ('sharing_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('folder_name', models.CharField(blank=True, max_length=255)),
                ('max_space', models.BigIntegerField(null=True)),
                ('content_size', models.BigIntegerField(default=0)),
                ('starred', models.BooleanField(default=False)),
                ('data_request_status', models.CharField(choices=[('0', 'NOT_MADE'), ('1', 'PENDING'), ('2', 'ACCEPT'), ('3', 'REJECT')], default='0', max_length=10)),
                ('additional_space', models.BigIntegerField(default=0)),
                ('permission', models.CharField(choices=[('_', 'FORBIDDEN'), ('r_o', 'READ_ONLY'), ('w_o', 'WRITE_ONLY'), ('r_w', 'READ_AND_WRITE')], default='r_o', max_length=10)),
                ('path', models.TextField()),
                ('filemanager', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='folders', to='django_filemanager.FileManager')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='folders', to='django_filemanager.Folder')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='folder_user', to=settings.KERNEL_PERSON_MODEL)),
                ('root', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='all_folders', to='django_filemanager.Folder')),
                ('shared_users', models.ManyToManyField(blank=True, related_name='folder_shared_users', to=settings.KERNEL_PERSON_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('datetime_modified', models.DateTimeField(auto_now=True)),
                ('sharing_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('file_name', models.CharField(default='undedfined file', max_length=500)),
                ('size', models.IntegerField()),
                ('extension', models.CharField(default='undefined', max_length=50)),
                ('upload', models.FileField(max_length=1000000, storage=django.core.files.storage.FileSystemStorage(base_url='/api/django_filemanager/media_files/', location='/network_storage'), upload_to=formula_one.utils.upload_to.UploadTo('', '', file_manager=True))),
                ('is_public', models.BooleanField(default=False)),
                ('permission', models.CharField(choices=[('_', 'FORBIDDEN'), ('r_o', 'READ_ONLY'), ('w_o', 'WRITE_ONLY'), ('r_w', 'READ_AND_WRITE')], default='r_o', max_length=10)),
                ('starred', models.BooleanField(default=False)),
                ('folder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='django_filemanager.Folder')),
                ('shared_users', models.ManyToManyField(blank=True, related_name='file_shared_users', to=settings.KERNEL_PERSON_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
