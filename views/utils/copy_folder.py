from genericpath import isdir
import os
import re
import shutil
import subprocess

from django.core.files import File as DjangoFile
from django.conf import settings

from django_filemanager.models import Folder
from django_filemanager.views.utils.file import create_file
from django_filemanager.utils import add_content_size


def sanitize_folder_name(parent_folder_path, folder_name, freq=0):
    """This function checks whether a folder with same name exists

    Args:
        parent_folder_path (str): path of parent folder
        folder_name (str): name of folder
        freq (int, optional): Frequency of folders with same name. Defaults to 0.

    Returns:
        str: correct folder name
    """
    if os.path.exists(os.path.join(parent_folder_path, folder_name)):
        freq = freq + 1
        if(freq == 1):
            folder_name = folder_name + '_' + str(freq)
            return sanitize_folder_name(parent_folder_path, folder_name, freq)

        folder_name = re.sub(r".$", str(freq), folder_name)
        return sanitize_folder_name(parent_folder_path, folder_name, freq)

    else:
        return folder_name


def shift_single_folder(folder_path, parent_folder_path, filemanager_path, filemanager, foldername):
    """This function creates a new folder model and loops through its content

    Args:
        folder_path (str): temporary folder path
        parent_folder_path (str): path of parent folder
        filemanager_path (str): path of filemanager
        filemanager (instance): instance of filemanager
        foldername (str): folder name
    """
    os.listdir(folder_path)

    parent_folder = None

    folder_size = os.path.getsize(folder_path)

    for path in parent_folder_path.split('/'):
        if parent_folder == None:
            parent_folder = Folder.objects.get(
                folder_name=path, parent=parent_folder, filemanager=filemanager)
        else:
            parent_folder = Folder.objects.get(
                folder_name=path, parent=parent_folder)

    new_folder = Folder.objects.create(folder_name=foldername, parent=parent_folder,
                                       filemanager=parent_folder.filemanager, root=parent_folder.root, person=parent_folder.person,
                                       path=os.path.join(parent_folder.path, '/', foldername), content_size=folder_size)

    for file_or_dir in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, file_or_dir)) and not os.path.exists(os.path.join(new_folder.path, file_or_dir)):
            extension = os.path.splitext(
                os.path.join(folder_path, file_or_dir))[-1]
            file_size = os.path.getsize(os.path.join(folder_path, file_or_dir))
            add_content_size(new_folder, file_size)
            file_obj = create_file(
                new_folder, file_or_dir, extension, file_size)
        elif os.path.isdir(os.path.join(folder_path, file_or_dir)) and not os.path.exists(os.path.join(new_folder.path, file_or_dir)):
            shift_single_folder(os.path.join(
                folder_path, file_or_dir), new_folder.path, filemanager_path, filemanager, file_or_dir)
