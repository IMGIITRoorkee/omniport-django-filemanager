import os
import shutil

from add_all_contents import add_all_contents
from django_filemanager.models import Folder, FileManager
from kernel.models import Person


from omniport.settings.base.directories import (
    PARENT_DIR
)

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
