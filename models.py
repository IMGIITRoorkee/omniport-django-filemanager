import swapper
import os

from django.db import models
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from formula_one.models.base import Model
from formula_one.utils.upload_to import UploadTo

from django_filemanager import constants

BASE_URL = '/api/django_filemanager/media_files/'


personal_storage = FileSystemStorage(
    location=settings.PERSONAL_ROOT,
    base_url=BASE_URL,
)


class Folder(Model):
    """
    This model holds information about a folder owned by a person
    """

    person = models.ForeignKey(
        to=swapper.get_model_name('kernel', 'Person'),
        related_name='folder_user',
        on_delete=models.CASCADE,
    )

    folder_name = models.CharField(
        max_length=255,
        blank=True,
    )

    max_space = models.IntegerField(
        null=True,
    )

    content_size = models.IntegerField(null=True)

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name='folders',
        on_delete=models.CASCADE,
    )

    root = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='all_folders',
        on_delete=models.CASCADE,
    )

    starred = models.BooleanField(default=False)

    permission = models.CharField(
        max_length=10, choices=constants.PERMISSIONS, default="r_o")

    @property
    def available_space(self):
        """Gives available space"""
        if self.root:
            return self.root.max_space - self.root.content_size
        else:
            return self.max_space - self.content_size

    @property
    def path(self):
        if self.root:
            return self.person.user.username
        return os.path.join(self.parent.path, self.folder_name)

    def save(self, *args, **kwargs):
        if not self.folder_name:
            self.folder_name = self.person.user.username
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Return the string representation of the model
        :return: the string representation of the model
        """

        person = self.person
        return f'{person} {self.folder_name}'


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
