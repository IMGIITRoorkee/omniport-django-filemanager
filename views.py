from rest_framework import viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, JsonResponse
import json
from rest_framework.decorators import action

from django_filemanager.serializers import FileSerializer, subFolderSerializer, FolderSerializer, rootFolderSerializer, FileManagerSerializer
from django_filemanager.constants import ACCEPT, REJECT, REQUEST_STATUS_MAP
from django_filemanager.models import Folder, File, FileManager
from django_filemanager.permissions import HasItemPermissions
from django_filemanager.constants import SHARED


class FolderViewSet(viewsets.ModelViewSet):
    """
    This view gets all the files in a folder corresponding
    to the logged in user
    """

    serializer_class = FolderSerializer

    def get_queryset(self):
        person = self.request.person
        queryset = Folder.objects.filter(person=person)
        return queryset

    @action(detail=False, methods=['get'])
    def get_root(self, request):
        filemanager_name = request.query_params.get('filemanager', None)
        try:
            filemanager = FileManager.objects.get(
                filemanager_name=filemanager_name)
        except:
            return Response("Filemanager instance with given name doesnot exists", status=status.HTTP_400_BAD_REQUEST)
        person = self.request.person
        try:
            folder = Folder.objects.get(
                person=person, root=None, parent=None, filemanager=filemanager)
        except Folder.DoesNotExist:
            folder = Folder(person=person, root=None,
                            parent=None, content_size=0, max_space=1024, filemanager=filemanager)
            folder.save()

            folder = Folder.objects.get(
                person=person, root=None, parent=None)
        except Folder.DoesNotExist:
            folder = Folder(person=person, root=None,
                            parent=None, content_size=0, max_space=1024)
            folder.save()
        except Folder.MultipleObjectsReturned:
            return Response("more than one root folder found for same person", status=status.HTTP_409_CONFLICT)
        serializer = self.serializer_class(folder)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def get_root_folders(self, request):
        person = self.request.person
        folders = Folder.objects.filter(
            person=person, parent=None
        )
        serializer = rootFolderSerializer(
            folders, many=True
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def shared_with_me(self, request):
        person = self.request.person
        folders = Folder.objects.filter(
            shared_users=person
        )
        serializer = FolderSerializer(
            folders, many=True
        )
        return Response(serializer.data)

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

    @action(detail=True, methods=['post'], )
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


class FileAccessView(APIView):
    """
    This view allows authenticated users to view the files.

    The files can be viewed based on two conditions:
    1. The file belongs to the user
    2. The file is public
    """

    def get(self, request, format=None):
        path = request.path
        url = path.replace(BASE_URL, '', 1)

        person = request.person

        if File.objects.filter(upload=url).exists():
            file_object = File.objects.get(upload=url)

            if (file_object.belongs_to() == person) or file_object.is_public:
                response = HttpResponse(status=200)
                response['Content-Type'] = ''
                response['X-Accel-Redirect'] = '/personal/{}'.format(url)
                return response

        response = HttpResponse(status=404)
        return response


class FileView(viewsets.ModelViewSet):
    """
    This view allows a user to upload, edit and delete a file
    """
    serializer_class = FileSerializer

    def get_queryset(self):
        person = self.request.person
        queryset = File.objects.filter(folder__person=person)
        return queryset

    def create(self, request, *args, **kwargs):
        parent_folder = Folder.objects.get(pk=request.data.get("folder"))
        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder
        updated_size = root_folder.content_size + \
            int(request.data.get("size"))
        if updated_size > root_folder.max_space:
            return HttpResponse("Space limit exceeded", status=status.HTTP_400_BAD_REQUEST)
        root_folder.content_size = updated_size
        root_folder.save()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        parent_folder = instance.folder
        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder
        updated_size = root_folder.content_size - \
            instance.size
        root_folder.content_size = updated_size
        root_folder.save()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def shared_with_me(self, request):
        person = self.request.person
        files = File.objects.filter(
            shared_users=person
        )
        serializer = FileSerializer(
            files, many=True
        )
        print(serializer)
        return Response(serializer.data)


class AllSharedItems(APIView):

    def get(self, request, *args, **kwargs):
        person = self.request.person
        files_shared = File.objects.filter(
            shared_users=person
        )
        files = FileSerializer(
            files_shared, many=True
        )
        folders_shared = Folder.objects.filter(
            shared_users=person
        )
        folders = FolderSerializer(
            folders_shared, many=True
        )
        serializer = {
            'files': files.data,
            'folders': folders.data,
            'type': SHARED
        }
        return JsonResponse(serializer)


class ItemSharedView(APIView):
    """
    This view allows user to view any of the folder/file which comes under shared folders with the requesting user
    """

    permission_classes = [HasItemPermissions, ]

    def get(self, request, *args, **kwargs):
        item_id = kwargs['id']
        # print(kwargs)
        # print(path)
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


class FileManagerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This view allows user to view all existing filemanager instances
    """

    serializer_class = FileManagerSerializer
    queryset = FileManager.objects.all()
