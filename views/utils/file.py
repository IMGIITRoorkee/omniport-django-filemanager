from fileinput import filename
import os
import subprocess

from django_filemanager.models import File


def file_exists(parent_folder_path, file_name, freq=0):
    """This function checks whether a file with same name exists

    Args:
        parent_folder_path (str): path of parent folder
        file_name (str): name of file
        freq (int, optional): Frequency of files with same name. Defaults to 0.

    Returns:
        str: correct file name
    """
    if os.path.exists(os.path.join(parent_folder_path, file_name)):
        freq = freq + 1
        filename_content = file_name.split('.')
        if freq > 1:
            filename_content[-2] = str(freq).join(
                filename_content[-2].rsplit(filename_content[-2][-1:], 1))
        else:
            filename_content[-2] = filename_content[-2]+str(freq)
        filename_content[-1] = '.' + filename_content[-1]
        new_filename = ''
        for content in filename_content:
            new_filename = new_filename+content
        return file_exists(parent_folder_path, new_filename, freq)
    else:
        return file_name


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
    path = os.path.join(parent_folder.get_path(), file_name)
    new_file = File(file_name=file_name, extension=extension[1:],
                    starred=False, size=file_size, folder=parent_folder)
    if parent_folder.filemanager.is_public:
        base_location = 'public'
    else:
        base_location = 'protected'

    new_file.upload.name = base_location+'/' + \
        str(parent_folder.filemanager.filemanager_name)+'/'+str(path)
    new_file.save()
    return new_file
