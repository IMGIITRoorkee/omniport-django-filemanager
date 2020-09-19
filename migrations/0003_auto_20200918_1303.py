# Generated by Django 3.0.3 on 2020-09-18 07:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.KERNEL_PERSON_MODEL),
        ('django_filemanager', '0002_auto_20200918_1134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='folder',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='folder_user', to=settings.KERNEL_PERSON_MODEL),
        ),
    ]