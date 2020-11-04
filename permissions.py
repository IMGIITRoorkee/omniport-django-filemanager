from rest_framework import permissions
from django_filemanager.models import Folder, File, FileManager
from django.core.exceptions import ValidationError
from kernel.models import Person

class HasItemPermissions(permissions.BasePermission):
    """
    """
    
    def has_permission(self, request,view):
      is_folder = view.kwargs['item2']=='folder'
      item = view.kwargs['item1']
      uu_id = view.kwargs['uuid']
      item_id = view.kwargs['id']
      print(view.kwargs)
      person = request.person
      if is_folder and item=='folder':
        try:
          folder = Folder.objects.get(sharing_id = uu_id)
          if folder.shared_users.get(id=person.id):
            print("folder is shared with user")
            if folder.id==item_id:
              return True
            else:
              dummy_folder = Folder.objects.get(id=item_id)
              while dummy_folder.parent!=None:
                print("running loop")
                print(dummy_folder)
                if dummy_folder.parent.id==folder.id:
                  return True
                else:
                  dummy_folder = Folder.objects.get(id = dummy_folder.parent.id)
              return False
          else:
            raise Person.DoesNotExist
        except (Folder.DoesNotExist,ValidationError,Person.DoesNotExist):
          return False
      elif item=='file':
        try:
          file = File.objects.get(sharing_id = uu_id)
          if file.shared_users.get(id=person.id):
            if file.id==item_id:
              return True
            else:
              return False
          else:
            raise Person.DoesNotExist
        except (File.DoesNotExist,ValidationError,Person.DoesNotExist):
          return False
      elif item=='folder' and not is_folder:
        try:
          folder = Folder.objects.get(sharing_id = uu_id)
          if folder.shared_users.get(id=person.id):
            dummy_file = File.objects.get(id=item_id)
            dummy_folder = dummy_file.folder
            while dummy_folder.parent.id!=None:
              if dummy_folder.parent.id==folder.id:
                return True
              else:
                dummy_folder = Folder.objects.get(id = dummy_folder.parent.id)
            return False
          else:
            raise Person.DoesNotExist
        except (Folder.DoesNotExist,ValidationError,Person.DoesNotExist):
          return False
      else:
        return False
      return False
