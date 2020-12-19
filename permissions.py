from rest_framework import permissions
from django_filemanager.models import Folder, File, FileManager
from django.core.exceptions import ValidationError
from kernel.models import Person
from kernel.utils.rights import has_omnipotence_rights
from kernel.managers.get_role import get_all_roles


class HasItemPermissions(permissions.BasePermission):
    """
    """

    def has_permission(self, request, view):
        is_folder = view.kwargs['item2'] == 'folder'
        item = view.kwargs['item1']
        uu_id = view.kwargs['uuid']
        item_id = view.kwargs['id']
        person = request.person
        if is_folder and item == 'folder':
            try:
                folder = Folder.objects.get(sharing_id=uu_id)
                if folder.shared_users.get(id=person.id):
                    if folder.id == item_id:
                        return True
                    else:
                        dummy_folder = Folder.objects.get(id=item_id)
                        while dummy_folder.parent != None:
                            print("running loop")
                            if dummy_folder.parent.id == folder.id:
                                return True
                            else:
                                dummy_folder = Folder.objects.get(
                                    id=dummy_folder.parent.id)
                        return False
                else:
                    raise Person.DoesNotExist
            except (Folder.DoesNotExist, ValidationError, Person.DoesNotExist):
                return False
        elif item == 'file':
            try:
                file = File.objects.get(sharing_id=uu_id)
                if file.shared_users.get(id=person.id):
                    if file.id == item_id:
                        return True
                    else:
                        return False
                else:
                    raise Person.DoesNotExist
            except (File.DoesNotExist, ValidationError, Person.DoesNotExist):
                return False
        elif item == 'folder' and not is_folder:
            try:
                folder = Folder.objects.get(sharing_id=uu_id)
                if folder.shared_users.get(id=person.id):
                    dummy_file = File.objects.get(id=item_id)
                    dummy_folder = dummy_file.folder
                    while dummy_folder.parent.id != None:
                        if dummy_folder.parent.id == folder.id:
                            return True
                        else:
                            dummy_folder = Folder.objects.get(
                                id=dummy_folder.parent.id)
                    return False
                else:
                    raise Person.DoesNotExist
            except (Folder.DoesNotExist, ValidationError, Person.DoesNotExist):
                return False
        else:
            return False
        return False


class HasFolderOwnerPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
          Checks if the user is the owner of the folder
        """

        user = request.user
        if user is None:
            return False
        if has_omnipotence_rights(user):
            return True

        return (not obj.person.user is None) and obj.person.user == user
            


class HasFoldersOwnerPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, objList):
        """
            Checks if the user is the owner of the folder list
        """
        user = request.user
        if user is None:
            return False
        if has_omnipotence_rights(user):
            return True
        for obj in objList:
            if (not obj.person.user) or obj.person.user != user:
                return False
        return True


class HasFileOwnerPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
          Checks if the user is the owner of the folder
        """

        user = request.user
        if user is None:
            return False
        if has_omnipotence_rights(user):
            return True

        if (not obj.folder.person.user is None) and obj.folder.person == user:
            return True


class HasFilesOwnerPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, objList):
        """
            Checks if the user is the owner of the folder list
        """
        user = request.user
        if user is None:
            return False
        if has_omnipotence_rights(user):
            return True
        for obj in objList:
            if (not obj.folder.person.user) or obj.folder.person.user != user:
                return False
        return True

class HasRootFolderPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, filemanager):
        """
            Checks if the user has access_permissions for filemanager
        """
        person = request.person
        try:
            code = compile(filemanager.filemanager_access_permissions,'<bool>','eval')
            if(eval(code)):
                return True
        except:
            return False
        return False