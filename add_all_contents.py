import os
import shutil

from django_filemanager.upload_to import UploadTo

from django.conf import settings
from django.core.files import File as DjangoFile
from django_filemanager.models import Folder, File

from django_filemanager.constants import BATCH_SIZE
from django_filemanager.utils import add_content_size

def get_file_name(file, fileName):
    """
    Return Updated file name in case of file already exists
    :param path: path of folder in which the file will be stored
    :param filename: the original name of the file
    :return: updated file name and the path to the uploaded file
    """
    new_file_rel_path = UploadTo(
        "", "", file_manager=True)(file, fileName)
    newname = fileName
    counter = 0
    name, ext = os.path.splitext(fileName)
    while os.path.exists(os.path.join(settings.NETWORK_STORAGE_ROOT, new_file_rel_path)):
        newname = name+'_' + str(counter) + ext
        new_file_rel_path = os.path.dirname(new_file_rel_path)+'/'+newname
        counter = counter + 1

    return newname, new_file_rel_path

def add_all_contents(parent_folder_path, person, root_folder, parent_folder, filemanager):
    """
    Add all files and folders under root_folder_path recursively.
    """
    folderBatch = []
    file_names = []
    folder_names = []

    for (dirpath, dirnames, filenames) in os.walk(parent_folder_path):
        file_names.extend(filenames)
        folder_names.extend(dirnames)
        break
    total_file_size = 0
    for fileName in file_names:
        file = os.path.join(parent_folder_path, fileName)
        total_file_size += os.stat(file).st_size
        new_file = File(
            file_name=fileName,
            extension=fileName.split('.')[-1],
            starred=False,
            size=os.stat(file).st_size,
            folder=parent_folder,
        )

        newFileName, newFilePath = get_file_name(new_file, fileName)

        src_file = os.path.join(
            settings.NETWORK_STORAGE_ROOT, newFilePath)
        os.makedirs(os.path.dirname(src_file), exist_ok=True)

        new_file.file_name = newFileName
        f = DjangoFile(open(file, 'r'))
        new_file.upload.save(newFileName, f)

    add_content_size(parent_folder, total_file_size)

    for folderName in folder_names:
        new_folder = Folder(filemanager=filemanager,
                            folder_name=folderName,
                            person=person,
                            max_space=filemanager.max_space,
                            starred=False,
                            root=root_folder,
                            parent=parent_folder)
        new_folder.path = new_folder.get_path()
        folderBatch.append(new_folder)

    Folder.objects.bulk_create(folderBatch, BATCH_SIZE[0])

    for folder in folderBatch:
        add_all_contents(os.path.join(
            parent_folder_path, folder.folder_name), person, root_folder, folder, filemanager)
