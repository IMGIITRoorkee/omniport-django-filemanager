import os
from django.http import HttpResponse
from django.conf import settings

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from kernel.models import Person

from django_filemanager.serializers import FileSerializer
from django_filemanager.models import Folder, File, FileManager, BASE_PROTECTED_URL
from django_filemanager.permissions import HasFileOwnerPermission, HasFilesOwnerPermission
from django_filemanager.constants import BATCH_SIZE


class FileAccessView(APIView):
    """
    This view allows authenticated users to view the files.

    The files can be viewed based on two conditions:
    1. The file belongs to the user
    2. The file is public
    """

    def get(self, request, format=None):
        path = request.path
        url = path.replace(BASE_PROTECTED_URL, '', 1)
        person = request.person
        if File.objects.filter(upload=url).exists():
            file_object = File.objects.get(upload=url)
            if (file_object.belongs_to() == person) or (person in file_object.shared_users.all()):
                response = HttpResponse(status=200)
                response['Content-Type'] = ''
                response['X-Accel-Redirect'] = '/external/{}'.format(url)
                return response
        if FileManager.objects.filter(logo=url).exists():
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

    permission_classes_by_action = {
        'destroy': [HasFileOwnerPermission],
        'bulk_delete': [HasFilesOwnerPermission],
        'default': [IsAuthenticated],
    }

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError as e:
            return [permission() for permission in self.permission_classes_by_action['default']]

    def get_queryset(self):
        person = self.request.person
        queryset = File.objects.filter(folder__person=person)
        return queryset

    def create(self, request, *args, **kwargs):
        parent_folder = Folder.objects.get(pk=request.data.get('folder'))
        file_size = int(request.data.get('size'))
        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder
        if root_folder.content_size + file_size > root_folder.max_space:
            return HttpResponse('Space limit exceeded', status=status.HTTP_400_BAD_REQUEST)
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
        no_of_files = len(data.get('file_name'))
        batch = []
        try:
            folder = Folder.objects.get(pk=int(data.get('folder')[0]))
            parent_folder = folder
        except Folder.DoesNotExist:
            return HttpResponse('parent folder doesnot found', status=status.HTTP_400_BAD_REQUEST)
        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder
        total_file_size = 0
        for i in range(0, no_of_files):
            total_file_size = total_file_size + int(data.get('size')[i])
        if root_folder.content_size + total_file_size > root_folder.max_space:
            return HttpResponse('Space limit exceeded', status=status.HTTP_400_BAD_REQUEST)

        while not parent_folder == None:
            updated_size = parent_folder.content_size + total_file_size
            parent_folder.content_size = updated_size
            parent_folder.save()
            parent_folder = parent_folder.parent

        for i in range(0, no_of_files):
            starred = data.get('starred')[i] == 'True'
            new_file = File(upload=data.get('upload')[i],
                            file_name=data.get('file_name')[i],
                            extension=data.get('extension')[i],
                            starred=starred,
                            size=int(data.get('size')[i]),
                            folder=folder,
                            )
            batch.append(new_file)
        files = File.objects.bulk_create(batch, BATCH_SIZE[0])
        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data)

    def update(self,request,*args,**kwargs):
        data = dict(request.data)
        file = File.objects.get(id=kwargs['pk'])
        if data.get('file_name') and (data.get('file_name') != file.file_name):
            folder_name = str(file.folder.path)

            if(file.folder.filemanager.is_public):
                base_location = "public"
            else:
                base_location = "protected"

            app_name = str(
                file.folder.filemanager.filemanager_name)
            path = os.path.join(
                base_location,
                app_name,
                folder_name,
            )
            prev_filename = file.file_name
            updated_filename = str(data.get('file_name')[0])
            # Full path to the file
            initial_destination = os.path.join(
                settings.NETWORK_STORAGE_ROOT,
                path,
                prev_filename,
            )
            final_destination = os.path.join(
                settings.NETWORK_STORAGE_ROOT,
                path,
                updated_filename,
            )
            upload_name = os.path.join(
                path,
                updated_filename
            )
            os.rename(initial_destination,final_destination)
            file.upload.name = str(upload_name)
            file.save()
        return super().update(request,*args,**kwargs)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        data = dict(request.data)
        try:
            arr = data['fileIdArr']
            if len(arr) == 0:
                return HttpResponse('Arrays have no length.', status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            return HttpResponse('file ids not found.', status=status.HTTP_400_BAD_REQUEST)
        files = File.objects.filter(pk__in=arr)
        self.check_object_permissions(self.request, files)
        parent_folder = files[0].folder
        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder
        total_file_size = 0
        for file in files:
            total_file_size = total_file_size + file.size
        try:
            while not parent_folder == None:
                updated_size = parent_folder.content_size - total_file_size
                parent_folder.content_size = updated_size
                parent_folder.save()
                parent_folder = parent_folder.parent

            files.delete()
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return HttpResponse(f'error in deleting files due to {e}', status=status.HTTP_400_BAD_REQUEST)

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
            return HttpResponse('File Not available', status=status.HTTP_400_BAD_REQUEST)

        try:
            shared_users = list(
                filter(None, request.data.getlist('shared_users')))
            shared_users_initially = [x.id for x in file.shared_users.all()]
            deleted_users = list(set(shared_users_initially)-set(shared_users))
            new_users = list(set(shared_users) - set(shared_users_initially))
            try:
                for user in deleted_users:
                    person = Person.objects.get(
                        id=user)
                    file.shared_users.remove(person)
                for user in new_users:
                    person = Person.objects.get(
                        id=user)
                    file.shared_users.add(person)
                return HttpResponse('File shared with the users', status=status.HTTP_200_OK)
            except Exception as e:
                return HttpResponse(f'Error occured while updating users due to {e}', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return HttpResponse(f'Unable to change shared_user due to {e}', status=status.HTTP_400_BAD_REQUEST)
