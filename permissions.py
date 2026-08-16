from rest_framework import permissions
from django_filemanager.expressions import evaluate_access_permission
from django_filemanager.models import Folder, File
from django_filemanager.utils import is_folder_shared
from django.core.exceptions import ValidationError
from kernel.models import Person
from kernel.utils.rights import has_omnipotence_rights


def owner_of(item):
    """
    Return the user a folder or a file belongs to
    :param item: a Folder or a File
    :return: the user who owns it, if any
    """

    person = item.person if isinstance(item, Folder) else item.folder.person
    return person.user


class IsOwner(permissions.IsAuthenticated):
    """
    Object level ownership of a folder or a file, or of an iterable of either.
    Every action defaults to this, so an action that declares no permission of
    its own still cannot reach another person's tree.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if has_omnipotence_rights(user):
            return True
        items = [obj] if isinstance(obj, (Folder, File)) else list(obj)
        return bool(items) and all(owner_of(item) == user for item in items)


class HasItemPermissions(permissions.IsAuthenticated):
    """
    Authorise a shared item. Every branch validates the kind the view goes on
    to serve, item2, so a sharing id for one kind cannot authorise the other.
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
                if is_folder_shared(person, folder):
                    if folder.id == item_id:
                        return True
                    else:
                        dummy_folder = Folder.objects.get(id=item_id)
                        while dummy_folder.parent != None:
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
        elif item == 'file' and not is_folder:
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
                    dummy_folder = File.objects.get(id=item_id).folder
                    while dummy_folder != None:
                        if dummy_folder.id == folder.id:
                            return True
                        dummy_folder = dummy_folder.parent
                    return False
                else:
                    raise Person.DoesNotExist
            except (Folder.DoesNotExist, File.DoesNotExist, ValidationError,
                    Person.DoesNotExist):
                return False
        else:
            return False
        return False


class HasRootFolderPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, filemanager):
        """
            Checks if the user has access_permissions for filemanager
        """
        try:
            return evaluate_access_permission(
                filemanager.filemanager_access_permissions, request.person)
        except Exception:
            return False


class HasParentPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.person == obj.person or is_folder_shared(request.person,obj)
