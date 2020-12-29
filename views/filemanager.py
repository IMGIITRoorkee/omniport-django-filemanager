from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from kernel.models import Person
from shell.models import Student, FacultyMember
from shell.models.roles.maintainer import Maintainer

from kernel.permissions.omnipotence import HasOmnipotenceRights
from kernel.managers.get_role import get_all_roles
from django_filemanager.serializers import FileManagerSerializer
from django_filemanager.models import Folder, FileManager
from django_filemanager.constants import DEFAULT_ROOT_FOLDER_NAME_TEMPLATE


class FileManagerViewSet(viewsets.ModelViewSet):
    """
    This view allows user to view all existing filemanager instances
    """

    serializer_class = FileManagerSerializer
    queryset = FileManager.objects.all()
    permission_classes = [HasOmnipotenceRights]

    def create(self, request, *args, **kwargs):
        is_public = request.data.get("is_public")
        try:
            folder_name_template = request.data.get(
                "folder_name_template", None)
            filemanager_access_permissions = request.data.get(
                "filemanager_access_permissions", None)
            if folder_name_template == None or folder_name_template == "":
                folder_name_template = DEFAULT_ROOT_FOLDER_NAME_TEMPLATE
            filemanager = FileManager.objects.create(
                filemanager_name=request.data.get("filemanager_name"),
                folder_name_template=folder_name_template,
                filemanager_access_permissions=str(
                    filemanager_access_permissions),
                filemanager_extra_space_options=request.data.getlist(
                    "filemanager_extra_space_options"
                ),
                max_space=request.data.get("max_space"),
                logo=request.data.get("logo"),
                is_public=is_public == "True" or is_public == "true"
            )
        except:
            return Response("Unable to create filemanager", status=400)

        try:
            people = Person.objects.exclude(user=None)
            batch = []
            for i in range(0, len(people)):
                person = people[i]
                try:
                    code = compile(
                        filemanager.filemanager_access_permissions, '<bool>', 'eval')
                    filemanager_access_permission = eval(code)
                except:
                    filemanager.delete()
                    return Response("Unable to evaluate filemanager access permission", status=400)

                if filemanager_access_permission:
                    try:
                        unique_name = eval(filemanager.folder_name_template)
                    except:
                        filemanager.delete()
                        return Response("Unable to evaluate folder name template", status=400)
                    new_root_folder = Folder(filemanager=filemanager,
                                             folder_name=unique_name,
                                             person=people[i],
                                             max_space=filemanager.max_space,
                                             starred=False,
                                             root=None,
                                             parent=None,
                                             )
                    batch.append(new_root_folder)
            folders = Folder.objects.bulk_create(batch, 20)
            return Response(status=200)
        except:
            return Response("Filemanager created. Error in assigning root folders", status=400)
