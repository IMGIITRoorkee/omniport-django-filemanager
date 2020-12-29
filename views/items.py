import json

from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.db.models.signals import post_save

from rest_framework import viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from kernel.models import Person
from shell.models import Student, FacultyMember
from shell.models.roles.maintainer import Maintainer

from kernel.permissions.omnipotence import HasOmnipotenceRights
from kernel.managers.get_role import get_all_roles
from django_filemanager.serializers import FileSerializer, subFolderSerializer, FolderSerializer, rootFolderSerializer, FileManagerSerializer
from django_filemanager.constants import ACCEPT, REJECT, REQUEST_STATUS_MAP, BATCH_SIZE
from django_filemanager.models import Folder, File, FileManager, BASE_PROTECTED_URL
from django_filemanager.utils import update_root_folders
from django_filemanager.permissions import HasItemPermissions, HasFolderOwnerPermission, HasFoldersOwnerPermission, HasFileOwnerPermission, HasFilesOwnerPermission, HasRootFolderPermission
from django_filemanager.constants import SHARED, STARRED, DEFAULT_ROOT_FOLDER_NAME_TEMPLATE


class AllSharedItems(APIView):

    def get(self, request, *args, **kwargs):
        filemanager_name = request.query_params.get('filemanager', None)
        try:
            filemanager = FileManager.objects.get(
                filemanager_url_path=filemanager_name)
        except:
            return Response("Filemanager instance with given name doesnot exists", status=status.HTTP_400_BAD_REQUEST)
        person = self.request.person
        update_root_folders_response = update_root_folders(person)
        if update_root_folders_response['status'] == 200:
            files_shared = File.objects.filter(
                folder__filemanager=filemanager).filter(shared_users=person
                                                        )
            files = FileSerializer(
                files_shared, many=True
            )
            folders_shared = Folder.objects.filter(
                filemanager=filemanager).filter(shared_users=person
                                                )
            folders = FolderSerializer(
                folders_shared, many=True
            )
            serializer = {
                'files': files.data,
                'folders': folders.data,
                'type': SHARED,
                'filemanager': filemanager_name,
                'filemanagername': filemanager.filemanager_name
            }
            return Response(serializer)
        else:
            return Response(update_root_folders_response['message'], update_root_folders_response['status'])


class AllStarredItems(APIView):
    """
    This view allows user to view all the starred items
    """

    def get(self, request, *args, **kwargs):
        filemanager_name = request.query_params.get('filemanager', None)
        try:
            filemanager = FileManager.objects.get(
                filemanager_url_path=filemanager_name)
        except:
            return Response("Filemanager instance with given name doesnot exists", status=status.HTTP_400_BAD_REQUEST)
        person = self.request.person
        files_starred = File.objects.filter(
            folder__filemanager=filemanager).filter(folder__person=person).filter(starred=True
                                                                                  )
        files = FileSerializer(
            files_starred, many=True
        )
        folders_starred = Folder.objects.filter(
            filemanager=filemanager).filter(person=person).filter(starred=True
                                                                  )
        folders = FolderSerializer(
            folders_starred, many=True
        )
        serializer = {
            'files': files.data,
            'folders': folders.data,
            'type': STARRED,
            'filemanager': filemanager_name,
            'filemanagername': filemanager.filemanager_name
        }
        return Response(serializer)


class ItemSharedView(APIView):
    """
    This view allows user to view any of the folder/file which comes under shared folders with the requesting user
    """

    permission_classes = [HasItemPermissions, ]

    def get(self, request, *args, **kwargs):
        item_id = kwargs['id']
        if kwargs['item2'] == 'folder':
            folder = Folder.objects.get(id=item_id)
            serializer = FolderSerializer(folder)
            return Response(serializer.data)
        elif kwargs['item2'] == 'file':
            file = File.objects.get(id=item_id)
            serializer = FileSerializer(file)
            return Response(serializer.data)
        else:
            return Response("requested wrong item", status=404)
