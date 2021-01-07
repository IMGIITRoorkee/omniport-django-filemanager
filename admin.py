from omniport.admin.site import omnipotence

from django_filemanager.models import *


omnipotence.register(File)
omnipotence.register(Folder)
omnipotence.register(FileManager)
