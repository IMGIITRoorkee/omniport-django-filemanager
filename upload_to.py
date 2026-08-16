import os
import re
import uuid

from django.utils.deconstruct import deconstructible

EXTENSION = re.compile(r'\.[a-z0-9]{1,16}')


def storage_path(folder, filename):
    """
    Compute where a file of a folder is stored, relative to the storage root.
    The leaf is an opaque UUID, so that knowing who owns a file and what the
    file is called does not give away where it is kept. File.file_name carries
    the name to display and to download the file under.
    :param folder: the folder the file belongs to
    :param filename: the original name of the file, used for the extension
    :return: the path to store the file at
    """

    filemanager = folder.filemanager
    return os.path.join(
        'public' if filemanager.is_public else 'protected',
        str(filemanager.filemanager_name),
        str(folder.path),
        opaque_name(filename),
    )


def opaque_name(filename):
    """
    Compute the stored name of a file, keeping only its extension
    :param filename: the original name of the file
    :return: a UUID carrying the extension of the original name
    """

    extension = os.path.splitext(filename)[1].lower()
    if not EXTENSION.fullmatch(extension):
        extension = ''
    return f'{uuid.uuid4()}{extension}'


@deconstructible
class UploadTo:
    """
    The upload_to of File.upload. It takes the arguments the field was declared
    with, which the migrations hold, and reads the destination off the folder.
    """

    def __init__(self, app_name, folder_name, file_manager=False,
                 base_location=''):
        """
        Initialise a callable instance of the class with the given parameters
        :param app_name: the name of the app using this utility
        :param folder_name: the name of the folder where to write the file
        :param file_manager: whether the app using this utility is File Manager
        :param base_location: the root the destination is written under
        """

        self.app_name = app_name
        self.folder_name = folder_name
        self.file_manager = file_manager
        self.base_location = base_location

    def __call__(self, instance, filename):
        """
        Compute the location of where to store the file
        :param instance: the instance to which file is being uploaded
        :param filename: the original name of the file, used for the extension
        :return: the path to the uploaded file
        """

        return storage_path(instance.folder, filename)
