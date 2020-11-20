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

from kernel.models import Person
from django_filemanager.serializers import FileSerializer, subFolderSerializer, FolderSerializer, rootFolderSerializer, FileManagerSerializer
from django_filemanager.constants import ACCEPT, REJECT, REQUEST_STATUS_MAP, BATCH_SIZE
from django_filemanager.models import Folder, File, FileManager, BASE_URL
from django_filemanager.permissions import HasItemPermissions
from django_filemanager.constants import SHARED, STARRED


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
                filemanager_url_path=filemanager_name)
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

    @action(detail=True, methods=['PATCH'], )
    def update_shared_users(self, request, *args, **kwargs):
        pk = kwargs['pk']
        try:
            folder = Folder.objects.get(pk=pk)
        except Folder.DoesNotExist:
            return HttpResponse("Folder Not available", status=status.HTTP_400_BAD_REQUEST)

        try:
            shared_users = request.data.getlist('shared_users')
            folder.shared_users.clear()
            folder.save()
            if len(shared_users) == 1:
                if shared_users[0] != '':
                    person = Person.objects.get(
                        id=request.data['shared_users'])
                    folder.shared_users.add(person)
                    return HttpResponse("Folder shared with the user", status=status.HTTP_200_OK)
                else:
                    return HttpResponse("Removed shared users of the folder", status=status.HTTP_200_OK)
            elif len(shared_users) > 1:
                for user in shared_users:
                    person = Person.objects.get(id=user)
                    folder.shared_users.add(person)
                return HttpResponse("Folder shared with the users", status=status.HTTP_200_OK)
            else:
                return HttpResponse("Number of shared users is undefined", status=status.HTTP_200_OK)
        except:
            return HttpResponse("Unable to change shared_user", status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request, *args, **kwargs):
        data = dict(request.data)
        try:
            arr = data["folder_id_arr"]
        except KeyError:
            return HttpResponse("folder ids not found.", status=status.HTTP_400_BAD_REQUEST)
        try:
            folders = Folder.objects.filter(pk__in=arr)
            if len(folders) == 0:
                return HttpResponse("no folder ids given", status=status.HTTP_400_BAD_REQUEST)
            total_folder_size = 0
            for folder in folders:
                total_folder_size = total_folder_size + folder.content_size
            parent = folders[0].parent
            while not parent == None:
                updated_size = parent.content_size - total_folder_size
                parent.content_size = updated_size
                parent.save()
                parent = parent.parent
            folders.delete()
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        except:
            return HttpResponse("error in deliting folders", status=status.HTTP_400_BAD_REQUEST)

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
        parents = []
        while folder != None:
            parents.insert(0, folder)
            folder = folder.parent
        serializer = subFolderSerializer(parents, many=True)
        return Response(serializer.data)


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
    parser_classes = (FormParser, MultiPartParser, JSONParser)

    def get_queryset(self):
        person = self.request.person
        queryset = File.objects.filter(folder__person=person)
        return queryset

    def create(self, request, *args, **kwargs):
        parent_folder = Folder.objects.get(pk=request.data.get("folder"))
        file_size = int(request.data.get("size"))
        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder
        if root_folder.content_size + file_size > root_folder.max_space:
            return HttpResponse("Space limit exceeded", status=status.HTTP_400_BAD_REQUEST)
        while not parent_folder == None:
            updated_size = parent_folder.content_size + file_size
            parent_folder.content_size = updated_size
            parent_folder.save()
            parent_folder = parent_folder.parent

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request, *args, **kwargs):
        data = dict(request.data)
        no_of_files = len(data.get("is_public"))
        batch = []
        try:
            folder = Folder.objects.get(pk=int(data.get("folder")[0]))
            parent_folder = folder
        except Folder.DoesNotExist:
            return HttpResponse("parent folder doesnot found", status=status.HTTP_400_BAD_REQUEST)
        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder
        total_file_size = 0
        for i in range(0, no_of_files):
            total_file_size = total_file_size + int(data.get("size")[i])
        if total_file_size > root_folder.max_space:
            return HttpResponse("Space limit exceeded", status=status.HTTP_400_BAD_REQUEST)

        while not parent_folder == None:
            updated_size = parent_folder.content_size + total_file_size
            parent_folder.content_size = updated_size
            parent_folder.save()
            parent_folder = parent_folder.parent

        for i in range(0, no_of_files):
            is_public = data.get("is_public")[i] == 'True'
            starred = data.get("starred")[i] == 'True'
            new_file = File(upload=data.get("upload")[i],
                            file_name=data.get("file_name")[i],
                            is_public=is_public,
                            extension=data.get("extension")[i],
                            starred=starred,
                            size=int(data.get("size")[i]),
                            folder=folder,
                            )
            batch.append(new_file)
        files = File.objects.bulk_create(batch, 20)
        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        data = dict(request.data)
        try:
            arr = data["fileIdArr"]
            if len(arr) == 0:
                return HttpResponse("Arrays have no length.", status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            return HttpResponse("file ids not found.", status=status.HTTP_400_BAD_REQUEST)
        try:
            files = File.objects.filter(pk__in=arr)
            parent_folder = files[0].folder
            if not parent_folder.root == None:
                root_folder = parent_folder.root
            else:
                root_folder = parent_folder
            total_file_size = 0
            for file in files:
                total_file_size = total_file_size + file.size
            while not parent_folder == None:
                updated_size = parent_folder.content_size - total_file_size
                parent_folder.content_size = updated_size
                parent_folder.save()
                parent_folder = parent_folder.parent

            files.delete()
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        except:
            return HttpResponse("error in deleting files", status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        parent_folder = instance.folder
        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder
        updated_size = root_folder.content_size - instance.size
        root_folder.content_size = updated_size
        root_folder.save()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @ action(detail=False, methods=['get'])
    def shared_with_me(self, request):
        person = self.request.person
        files = File.objects.filter(
            shared_users=person
        )
        serializer = FileSerializer(
            files, many=True
        )
        return Response(serializer.data)

    @ action(detail=True, methods=['PATCH'], )
    def update_shared_users(self, request, *args, **kwargs):
        pk = kwargs['pk']
        try:
            file = File.objects.get(pk=pk)
        except File.DoesNotExist:
            return HttpResponse("File Not available", status=status.HTTP_400_BAD_REQUEST)

        try:
            shared_users = request.data.getlist('shared_users')
            file.shared_users.clear()
            file.save()
            if len(shared_users) == 1:
                if shared_users[0] != '':
                    person = Person.objects.get(
                        id=request.data['shared_users'])
                    file.shared_users.add(person)
                    return HttpResponse("file shared with the user", status=status.HTTP_200_OK)
                else:
                    return HttpResponse("Removed shared users of the file", status=status.HTTP_200_OK)
            elif len(shared_users) > 1:
                for user in shared_users:
                    person = Person.objects.get(id=user)
                    file.shared_users.add(person)
                return HttpResponse("File shared with the users", status=status.HTTP_200_OK)
            else:
                return HttpResponse("Number of shared users is undefined", status=status.HTTP_200_OK)
        except:
            return HttpResponse("Unable to change shared_user", status=status.HTTP_400_BAD_REQUEST)


class AllSharedItems(APIView):

    def get(self, request, *args, **kwargs):
        filemanager_name = request.query_params.get('filemanager', None)
        try:
            filemanager = FileManager.objects.get(
                filemanager_url_path=filemanager_name)
        except:
            return Response("Filemanager instance with given name doesnot exists", status=status.HTTP_400_BAD_REQUEST)
        person = self.request.person
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
            'filemanager': filemanager_name
        }
        return Response(serializer)


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
            'filemanager': filemanager_name
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


class FileManagerViewSet(viewsets.ModelViewSet):
    """
    This view allows user to view all existing filemanager instances
    """

    serializer_class = FileManagerSerializer
    queryset = FileManager.objects.all()


def make_root_folders(sender, instance, **kwargs):
    filemanager = instance
    try:
        filemanager_access_roles = filemanager.filemanager_access_roles
        obj = {'Student': Q(student=None), 'FacultyMember': Q(facultymember=None),
               'Maintainer': Q(maintainer=None), 'Guest': Q(guest=None)}
        q = obj[filemanager.filemanager_access_roles[0]]
        for i in range(1, len(filemanager_access_roles)):
            q = q & obj[filemanager_access_roles[i]]

        people = Person.objects.exclude(q)
        batch = []
        for i in range(0, len(people)):
            new_root_folder = Folder(filemanager=filemanager,
                                     folder_name=filemanager.folder_name_template,
                                     person=people[i],
                                     max_space=filemanager.max_space,
                                     starred=False,
                                     parent=None,
                                     )
            batch.append(new_root_folder)
        folders = Folder.objects.bulk_create(batch, 20)
        serializer = FolderSerializer(folders, many=True)
        return Response(serializer.data)
    except:
        return Response("Filemanager created. Error in assigning root folders", status=404)


post_save.connect(make_root_folders, sender=FileManager)
