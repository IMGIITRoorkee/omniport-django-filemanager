import os
import shutil

from django_filemanager.models import Folder, FileManager, File
from kernel.managers.get_role import get_all_roles
from kernel.models import Person
from shell.models import Student, FacultyMember
from shell.models.roles.maintainer import Maintainer


from omniport.settings.base.directories import (
    PARENT_DIR
)

from django_filemanager.constants import BATCH_SIZE


def add_all_contents(root_folder_path, person, root_folder, parent_folder, filemanager):
    """
    Add all files and folders under root_folder_path recursively.
    """
    fileBatch = []
    folderBatch = []
    file_names = []
    folder_names = []
    for (dirpath, dirnames, filenames) in os.walk(root_folder_path):
        file_names.extend(filenames)
        folder_names.extend(dirnames)
        break

    for fileName in file_names:
        file = os.path.join(root_folder_path, fileName)
        f = File(open(file, 'r'))
        new_file = File(upload=f,
                        file_name=fileName,
                        extension=fileName.split('.')[-1],
                        starred=False,
                        size=os.stat(file).st_size,
                        folder=root_folder,
                        )
        fileBatch.append(new_file)

    for folderName in folder_names:
        new_folder = Folder(filemanager=filemanager,
                            folder_name=folderName,
                            person=person,
                            max_space=filemanager.max_space,
                            starred=False,
                            root=root_folder,
                            parent=root_folder,)
        folderBatch.append(new_folder)

    # File.objects.bulk_create(fileBatch, BATCH_SIZE[0])
    # Folder.objects.bulk_create(folderBatch, BATCH_SIZE[0])


def add_new_user(person_unique_key, person_unique_value, filemanager_name, root_folder_location):
    filters = {
        person_unique_key: person_unique_value
    }
    person = Person.objects.get(**filters)
    filemanager = FileManager.objects.get(filemanager_name=filemanager_name)

    code = compile(
        filemanager.filemanager_access_permissions, '<bool>', 'eval')
    filemanager_access_permission = eval(code)
    if filemanager_access_permission:
        unique_name = eval(filemanager.folder_name_template)
        folder = Folder(filemanager=filemanager,
                        folder_name=unique_name,
                        person=person,
                        max_space=filemanager.max_space,
                        starred=False,
                        root=None,
                        parent=None,
                        )
    path = os.path.join(PARENT_DIR, root_folder_location)
    add_all_contents(path, person, folder, folder, filemanager)


add_new_user("full_name", "ayush bansal", "mango",
             "/omniport/services/django_filemanager/test_root_folder")
