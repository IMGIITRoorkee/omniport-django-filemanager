import swapper
import os

from django.db import models
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.postgres import fields

from formula_one.models.base import Model
from formula_one.utils.upload_to import UploadTo

from django_filemanager import constants

BASE_URL = '/api/django_filemanager/media/'


personal_storage = FileSystemStorage(
    location=settings.PERSONAL_ROOT,
    base_url=BASE_URL,
)


class FileManager(Model):
    """
    This model holds different instances of filemanager
    """

    filemanager_name = models.CharField(
        max_length=50,
        default="undedfined filemanager",
    )

    folder_name_template = models.CharField(
        max_length=200, null=True
    )

    filemanager_access_roles = fields.ArrayField(
        models.CharField(
            max_length=50,
            choices=zip(settings.ROLES, settings.ROLES),
        )
    )

    logo = models.ImageField(
        upload_to=UploadTo('', '', file_manager=False),
        storage=personal_storage,
        null=True
    )

    def __str__(self):
        """
        Return the string representation of the model
        :return: the string representation of the model
        """

        filemanager_name = self.filemanager_name

        return f'{filemanager_name}'


class Folder(Model):
    """
    This model holds information about a folder owned by a person
    """

    filemanager = models.ForeignKey(
        to=FileManager,
        on_delete=models.CASCADE,
    )

    person = models.ForeignKey(
        to=swapper.get_model_name('kernel', 'Person'),
        related_name='folder_user',
        on_delete=models.CASCADE,
    )

    shared_users = models.ManyToManyField(
        to=swapper.get_model_name('kernel', 'Person'),
        related_name='folder_shared_users',
        null=True
    )

    folder_name = models.CharField(
        max_length=255,
        blank=True,
    )

    max_space = models.IntegerField(
        null=True,
    )

    content_size = models.IntegerField(default=0)

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

    request_space_pending = models.BooleanField(default=False)

    additional_space = models.IntegerField(default=0)

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

    def filemanagername(self):
        return self.filemanager.filemanager_name


class File(Model):
    """
    This Model holds information about a file
    """

    file_name = models.CharField(
        max_length=500,
        default="undedfined file",
    )

    size = models.IntegerField(null=False)

    extension = models.CharField(
        max_length=50,
        default="undefined"
    )

    upload = models.FileField(
        upload_to=UploadTo('', '', file_manager=True),
        storage=personal_storage,
    )

    shared_users = models.ManyToManyField(
        to=swapper.get_model_name('kernel', 'Person'),
        related_name='file_shared_users',
        null=True
    )

    folder = models.ForeignKey(
        to=Folder,
        on_delete=models.CASCADE,
    )

    is_public = models.BooleanField(
        default=False,
    )

    permission = models.CharField(
        max_length=10, choices=constants.PERMISSIONS, default="r_o")

    starred = models.BooleanField(default=False)

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
