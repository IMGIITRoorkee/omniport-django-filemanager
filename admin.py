from kernel.admin.site import omnipotence

from django_filemanager.models import *


omnipotence.register(File)
omnipotence.register(Folder)