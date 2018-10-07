import swapper
import os

from django.db import models
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from kernel.models.root import Model
from kernel.utils.upload_to import UploadTo


BASE_URL = '/api/django_filemanager/media_files/'

personal_storage = FileSystemStorage(
    location=settings.PERSONAL_FILES_ROOT,
    base_url=BASE_URL,
)


class Folder(Model):
    """
    This model holds information about a folder owned by a person
    """

    person =  models.OneToOneField(
        to=swapper.get_model_name('kernel', 'Person'),
        related_name='folder_user',
        on_delete=models.CASCADE,
    )

    space = models.IntegerField(
        default=1024,
    )

    def folder_name(self):
        return self.person.id

    def __str__(self):
        """
        Return the string representation of the model
        :return: the string representation of the model
        """

        person = self.person
        return f'{person}'


class File(Model):
    """
    This Model holds information about a file
    """

    upload = models.FileField(
        upload_to=UploadTo('', '', file_manager=True),
        storage=personal_storage,
    )

    folder = models.ForeignKey(
        to=Folder,
        on_delete=models.CASCADE,
    )

    is_public = models.BooleanField(
        default=False,
    )

    file_name = models.CharField(
        max_length=255,
    )


    def belongs_to(self):
        return self.folder.person

    def file_relative_path(self):
        return self.upload.name

    def __str__(self):
        """
        Return the string representation of the model
        :return: the string representation of the model
        """

        person = self.folder.person
        file_name = self.file_name

        return f'{file_name}: {person}'
