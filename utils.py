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
                return dict({'status': 400, 'message': f"{filemanager} : problem in evaluating access permission"})

            if filemanager_access_permission:
                try:
                    unique_name = eval(filemanager.folder_name_template)
                except:
                    return dict({'status': 400, 'message': f"{filemanager} : problem in evaluating folder name template"})
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

                    folder = Folder.objects.get(
                        person=person, root=None, parent=None)

                except:
                    return dict({'status': 400, 'message': "Unable to create root folder"})

    return dict({'status': 200, 'message': "found filemanagers"})