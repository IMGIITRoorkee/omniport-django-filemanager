from django_filemanager.models import File
from django_filemanager.upload_to import storage_path


def create_file(parent_folder, file_name, extension, file_size):
    """This function creates a model of given file

    Args:
        parent_folder (str): parent folder
        file_name (str): file name
        extension (str): file extension
        file_size (int): size of file

    Returns:
        instance: new file instance
    """
    new_file = File(file_name=file_name, extension=extension[1:],
                    starred=False, size=file_size, folder=parent_folder)
    new_file.upload.name = storage_path(parent_folder, file_name)
    new_file.save()
    return new_file
