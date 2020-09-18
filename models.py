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

    name = models.CharField(
        max_length = 255,
        default = "undefined folder"
    )

    max_space = models.IntegerField(
        null=True,
        blank=True,
    )

    content_size = models.IntegerField(default=0)


    parent = models.ForeignKey(
        "self",
        null=True,
        default=None,
        blank=True,
        related_name='folders',
        on_delete=models.CASCADE,
    )

    root = models.ForeignKey(
        'self',
        null = True,
        blank=True,
        related_name = 'all_folders',
        on_delete=models.CASCADE,
    )


    starred = models.BooleanField(  default=False)
    
    permission = models.CharField( max_length=10,choices=constants.PERMISSIONS, default = "r_o")

    @property
    def path(self):
        if self.root:
            return self.person.user.username
        return os.path.join(self.parent.path, self.name)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.person.user.username
        super().save(*args, **kwargs)


    def __str__(self):
        """
        Return the string representation of the model
        :return: the string representation of the model
        """

        person = self.person
        return f'{person} {self.name}'


class File(Model):
    """
    This Model holds information about a file
    """

    name = models.CharField(
        max_length=50,
        default="undedfined file",
    )

    size = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    person = models.ForeignKey(
        to=swapper.get_model_name('kernel', 'Person'),
        related_name='file_user',
        on_delete=models.CASCADE,
    )

    upload = models.FileField(
        upload_to=UploadTo('', '', file_manager=True),
        storage=personal_storage,
    )

    parent_folder = models.ForeignKey(
        to=Folder,
        on_delete=models.CASCADE,
    )

    is_public = models.BooleanField(
        default=False,
    )

    permission = models.CharField( max_length=10,choices=constants.PERMISSIONS, default = "r_o")

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
