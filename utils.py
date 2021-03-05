from django_filemanager.models import Folder, FileManager
from kernel.managers.get_role import get_all_roles
from kernel.models import Person
from shell.models import Student, FacultyMember
from shell.models.roles.maintainer import Maintainer


def update_root_folders(person):
    for filemanager in FileManager.objects.all():
        try:
            folder = Folder.objects.get(
                person=person, root=None, parent=None, filemanager=filemanager)
        except Folder.DoesNotExist:
            try:
                code = compile(
                    filemanager.filemanager_access_permissions, '<bool>', 'eval')
                filemanager_access_permission = eval(code)
            except:
                return dict({'status': 400, 'message': f'{filemanager} : problem in evaluating access permission'})

            if filemanager_access_permission:
                try:
                    unique_name = eval(filemanager.folder_name_template)
                except:
                    return dict({'status': 400, 'message': f'{filemanager} : problem in evaluating folder name template'})
                try:
                    folder = Folder(filemanager=filemanager,
                                    folder_name=unique_name,
                                    person=person,
                                    max_space=filemanager.max_space,
                                    starred=False,
                                    root=None,
                                    parent=None,
                                    )
                    folder.save()
                except:
                    return dict({'status': 400, 'message': 'Unable to create root folder'})

    return dict({'status': 200, 'message': 'found filemanagers'})


def add_content_size(parent_folder, size):
    while not parent_folder == None:
        updated_size = parent_folder.content_size + size
        parent_folder.content_size = updated_size
        parent_folder.save()
        parent_folder = parent_folder.parent


def reduce_content_size(parent_folder, size):
    while not parent_folder == None:
        updated_size = parent_folder.content_size - size
        parent_folder.content_size = updated_size
        parent_folder.save()
        parent_folder = parent_folder.parent


def is_file_shared(person, file):
    parent_folder = file.folder
    if person in file.shared_users.all() or file.share_with_all:
        return True
    while not parent_folder == None:
        if(person in parent_folder.shared_users.all() or parent_folder.share_with_all):
            return True
        parent_folder = parent_folder.parent
    return False


def is_folder_shared(person, folder):
    parent_folder = folder
    if person in folder.shared_users.all() or folder.share_with_all:
        return True
    while not parent_folder == None:
        if(person in parent_folder.shared_users.all() or parent_folder.share_with_all):
            return True
        parent_folder = parent_folder.parent
    return False
