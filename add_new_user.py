import os
import shutil

from django_filemanager.upload_to import UploadTo

from django.conf import settings
from django.core.files import File as DjangoFile
from django_filemanager.models import Folder, FileManager, File
from kernel.managers.get_role import get_all_roles
from kernel.models import Person
from shell.models import Student, FacultyMember
from shell.models.roles.maintainer import Maintainer


from omniport.settings.base.directories import (
    PARENT_DIR
)

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


def add_new_user(person_unique_key, person_unique_value, filemanager_name, root_folder_location):
    filters = {
        person_unique_key: person_unique_value
    }
    try:
        person = Person.objects.get(**filters)
    except Person.DoesNotExist:
        print("person with following credentials doesnot exists")
        return
    filemanager = FileManager.objects.get(filemanager_name=filemanager_name)
    try:
        folder = Folder.objects.get(
            person=person, root=None, parent=None, filemanager=filemanager)
    except Folder.DoesNotExist:
        code = compile(
            filemanager.filemanager_access_permissions, '<bool>', 'eval')
        filemanager_access_permission = eval(code)
        if not filemanager_access_permission:
            print("user does not have permission to this filmanager")
            return
        else:
            unique_name = eval(filemanager.folder_name_template)
            folder = Folder(filemanager=filemanager,
                            folder_name=unique_name,
                            person=person,
                            max_space=filemanager.max_space,
                            starred=False,
                            root=None,
                            parent=None,
                            )
            folder.path = folder.get_path()
            folder.save()

    path = os.path.join(PARENT_DIR, root_folder_location)
    add_all_contents(path, person, folder, folder, filemanager)


person_unique_key = input(
    "enter unique key for the person model(eg: full_name): ")
person_unique_value = input("enter value for the correnponding value: ")
filemanager_name = input("enter filemanager name you want to add the person: ")
root_folder_location = input(
    "enter parent folder location relative to the PARENT_DIR: ")

add_new_user(person_unique_key, person_unique_value,
             filemanager_name, root_folder_location)
