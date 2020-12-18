from django_filemanager.models import Folder, FileManager


def update_root_folders(person):
    for filemanager in FileManager.objects.all():
        try:
            folder = Folder.objects.get(
                person=person, root=None, parent=None, filemanager=filemanager)
        except Folder.DoesNotExist:
            try:
                unique_name = eval(filemanager.folder_name_template)
            except:
                return dict({'status':400, 'message':"Update your profile to use all filemanagers"})
            try:
                code = compile(
                    filemanager.filemanager_access_permissions, '<bool>', 'eval')
                filemanager_access_permission = eval(code)
            except:
                return dict({'status':400, 'message':"Update your profile to use all filemanagers"})

            if filemanager_access_permission:
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
                    
                    return dict({'status':200,'message':"updated filemanagers"})
                except:
                    return dict({'status':400, 'message':"Unable to create root folder"})

