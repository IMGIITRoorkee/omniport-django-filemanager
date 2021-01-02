from django.http import HttpResponse

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from kernel.models import Person

from kernel.permissions.omnipotence import HasOmnipotenceRights
from django_filemanager.serializers import subFolderSerializer, FolderSerializer, rootFolderSerializer
from django_filemanager.constants import ACCEPT, REJECT, REQUEST_STATUS_MAP
from django_filemanager.models import Folder, File, FileManager, BASE_PROTECTED_URL
from django_filemanager.utils import update_root_folders
from django_filemanager.permissions import HasFolderOwnerPermission, HasFoldersOwnerPermission,   HasRootFolderPermission


class FolderViewSet(viewsets.ModelViewSet):
    """
    This view gets all the files in a folder corresponding
    to the logged in user
    """

    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated]
    permission_classes_by_action = {
        'get_data_request': [HasOmnipotenceRights],
        'handle_request': [HasOmnipotenceRights],
        'get_root': [HasRootFolderPermission],
        'destroy': [HasFolderOwnerPermission],
        'bulk_delete': [HasFoldersOwnerPermission],
        'default': [IsAuthenticated],
    }

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError as e:
            return [permission() for permission in self.permission_classes_by_action['default']]

    def get_queryset(self):
        person = self.request.person
        queryset = Folder.objects.filter(person=person)
        return queryset

    @action(detail=False, methods=['get'])
    def get_root(self, request):
        filemanager_name = request.query_params.get('filemanager', None)
        try:
            filemanager = FileManager.objects.get(
                filemanager_url_path=filemanager_name)
        except:
            return Response("Filemanager instance with given name doesnot exists", status=status.HTTP_400_BAD_REQUEST)
        person = self.request.person
        self.check_object_permissions(self.request, filemanager)
        update_root_folders_response = update_root_folders(person)
        if update_root_folders_response['status'] == 200:
            folder = Folder.objects.get(
                person=person, root=None, parent=None, filemanager=filemanager)
            serializer = self.serializer_class(folder)
            return Response(serializer.data)
        else:
            return Response(update_root_folders_response['message'], update_root_folders_response['status'])

    @action(detail=False, methods=['get'])
    def get_root_folders(self, request):
        person = self.request.person
        update_root_folders_response = update_root_folders(person)
        if update_root_folders_response['status'] == 200:
            folders = Folder.objects.filter(
                person=person, parent=None
            )
            serializer = rootFolderSerializer(
                folders, many=True
            )
            return Response(serializer.data)
        else:
            return Response(update_root_folders_response['message'], update_root_folders_response['status'])

    @action(detail=False, methods=['get'])
    def shared_with_me(self, request):
        person = self.request.person
        update_root_folders_response = update_root_folders(person)
        if update_root_folders_response['status'] == 200:
            folders = Folder.objects.filter(
                shared_users=person
            )
            serializer = FolderSerializer(
                folders, many=True
            )
            return Response(serializer.data)
        else:
            return Response(update_root_folders_response['message'], update_root_folders_response['status'])

    @action(detail=True, methods=['post'])
    def generate_data_request(self, request, pk):
        try:
            folder = Folder.objects.get(pk=pk)
        except Folder.DoesNotExist:
            return HttpResponse("Folder Not available", status=status.HTTP_400_BAD_REQUEST)

        additional_space = request.data.get("additional_space")
        if additional_space == None:
            return HttpResponse("additional_space keyword required", status=status.HTTP_400_BAD_REQUEST)
        folder.additional_space = additional_space
        folder.data_request_status = '1'
        folder.save()
        serializer = rootFolderSerializer(folder)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def get_data_request(self, request):
        folders = Folder.objects.filter(
            root=None,  parent=None
        ).exclude(data_request_status=REQUEST_STATUS_MAP['not_made'])
        params = request.GET
        if "data_request_status" in params.keys():
            status = params['data_request_status']
            if status in REQUEST_STATUS_MAP.keys():
                folders = folders.filter(
                    data_request_status=REQUEST_STATUS_MAP[status])
        if "data_request_status!" in params.keys():
            status = params['data_request_status!']
            if status in REQUEST_STATUS_MAP.keys():
                folders = folders.exclude(
                    data_request_status=REQUEST_STATUS_MAP[status])

        serializer = rootFolderSerializer(folders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def handle_request(self, request, pk):
        try:
            folder = Folder.objects.get(pk=pk)
        except Folder.DoesNotExist:
            return HttpResponse("Folder Not available", status=status.HTTP_400_BAD_REQUEST)

        response = request.data.get("response")
        if response == None:
            return HttpResponse("response required", status=status.HTTP_400_BAD_REQUEST)
        if response == ACCEPT:
            folder.max_space = folder.max_space + folder.additional_space
            folder.data_request_status = "2"
            folder.save()
            serializer = rootFolderSerializer(folder)
            return Response(serializer.data)
        elif response == REJECT:
            folder.data_request_status = "3"
            folder.save()
            serializer = rootFolderSerializer(folder)
            return Response(serializer.data)
        else:
            return HttpResponse("Wrong type of response", status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['PATCH'], )
    def update_shared_users(self, request, *args, **kwargs):
        pk = kwargs['pk']
        try:
            folder = Folder.objects.get(pk=pk)
        except Folder.DoesNotExist:
            return HttpResponse("Folder Not available", status=status.HTTP_400_BAD_REQUEST)

        try:
            shared_users = list(
                filter(None, request.data.getlist('shared_users')))
            shared_users_initially = [x.id for x in folder.shared_users.all()]
            deleted_users = list(set(shared_users_initially)-set(shared_users))
            new_users = list(set(shared_users) - set(shared_users_initially))
            try:
                for user in deleted_users:
                    person = Person.objects.get(
                        id=user)
                    folder.shared_users.remove(person)
                for user in new_users:
                    person = Person.objects.get(
                        id=user)
                    folder.shared_users.add(person)
                return HttpResponse("Folder shared with the users", status=status.HTTP_200_OK)
            except Exception as e:
                return HttpResponse(f"Error occured while updating users due to {e}", status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return HttpResponse(f"Unable to change shared_user due to {e}", status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request, *args, **kwargs):
        data = dict(request.data)
        try:
            arr = data["folder_id_arr"]
        except KeyError:
            return HttpResponse("folder ids not found.", status=status.HTTP_400_BAD_REQUEST)

        folders = Folder.objects.filter(pk__in=arr)
        if len(folders) == 0:
            return HttpResponse("no folder ids given", status=status.HTTP_400_BAD_REQUEST)
        self.check_object_permissions(self.request, folders)
        total_folder_size = 0
        for folder in folders:
            total_folder_size = total_folder_size + folder.content_size
        parent = folders[0].parent
        try:
            while not parent == None:
                updated_size = parent.content_size - total_folder_size
                parent.content_size = updated_size
                parent.save()
                parent = parent.parent
            folders.delete()
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return HttpResponse(f"error in deliting folders due to {e}", status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.root == None:
            root_folder = instance.root
        else:
            root_folder = instance
        updated_size = root_folder.content_size - instance.content_size
        root_folder.content_size = updated_size
        root_folder.save()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_folder_size(self, folder):
        size = 0
        files = folder.files.all()
        folders = folder.folders.all()
        for file in files:
            size = size + file.size
        if folders == None:
            return size
        else:
            for child in folders:
                size = size + self.get_folder_size(child)
            return size

    @action(methods=['get'], detail=True, url_name='parents', url_path='parents')
    def get_parent_folders(self, request, pk):
        try:
            folder = Folder.objects.get(pk=pk)
        except Folder.DoesNotExist:
            return HttpResponse("Folder Not available", status=status.HTTP_400_BAD_REQUEST)
        self.check_object_permissions(self.request, folder)
        parents = []
        while folder != None:
            parents.insert(0, folder)
            folder = folder.parent
        serializer = subFolderSerializer(parents, many=True)
        return Response(serializer.data)
