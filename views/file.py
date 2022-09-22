from genericpath import isfile
import os
import shutil
import re
from django.http import HttpResponse
from django.conf import settings
import zipfile

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
from django_filemanager.permissions import HasFileOwnerPermission, HasFilesOwnerPermission, HasFolderOwnerPermission
from django_filemanager.constants import BATCH_SIZE
from django_filemanager.utils import add_content_size, reduce_content_size, is_file_shared
from django_filemanager.views.utils.file import create_file, file_exists
from django_filemanager.views.utils.copy_folder import sanitize_folder_name, shift_single_folder


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
        pk_chars = re.search(r'^\d+', url)
        pk = None
        if pk_chars:
            pk = int(pk_chars.group())
        person = request.person
        if FileManager.objects.filter(logo=url).exists():
            response = HttpResponse(status=200)
            response['Content-Type'] = ''
            response['X-Accel-Redirect'] = '/personal/{}'.format(url)
            return response
        if File.objects.filter(upload=url).exists():
            file_object = File.objects.get(upload=url)
            isShared = is_file_shared(person, file_object)
            if (file_object.belongs_to() == person) or isShared:
                response = HttpResponse(status=200)
                response['Content-Type'] = ''
                response['Content-Disposition'] = "attachment; filename=%s" % file_object.file_name
                response['X-Accel-Redirect'] = '/external/{}'.format(url)
                return response
        if File.objects.filter(pk=pk).exists():
            file_object = File.objects.get(pk=pk)
            isShared = is_file_shared(person, file_object)
            if (file_object.belongs_to() == person) or isShared:
                response = HttpResponse(status=200)
                response['Content-Type'] = ''
                response['Content-Disposition'] = "attachment; filename=%s" % file_object.file_name
                response['X-Accel-Redirect'] = '/external/{}'.format(
                    file_object.upload.name)
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
        'bulk_create': [HasFolderOwnerPermission],
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
        data = request.data
        try:
            folder = Folder.objects.get(pk=int(data.get('folder')))
            parent_folder = folder
        except Folder.DoesNotExist:
            return HttpResponse('parent folder doesnot found', status=status.HTTP_400_BAD_REQUEST)
        self.check_object_permissions(self.request, parent_folder)

        file_size = int(data.get('size'))
        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder
        if root_folder.content_size + file_size > root_folder.max_space:
            return HttpResponse('Space limit exceeded', status=status.HTTP_400_BAD_REQUEST)

        starred = data.get('starred') == 'True'

        new_file = File.objects.create(upload=data.get('upload'),
                                       file_name=data.get('file_name'),
                                       extension=data.get('extension'),
                                       starred=starred,
                                       size=int(data.get('size')),
                                       folder=parent_folder,
                                       )
        serializer = self.get_serializer(new_file)
        headers = self.get_success_headers(serializer.data)
        add_content_size(parent_folder, file_size)
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
        self.check_object_permissions(self.request, parent_folder)
        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder
        total_file_size = 0
        for i in range(0, no_of_files):
            total_file_size = total_file_size + int(data.get('size')[i])
        if root_folder.content_size + total_file_size > root_folder.max_space:
            return HttpResponse('Space limit exceeded', status=status.HTTP_400_BAD_REQUEST)

        add_content_size(parent_folder, total_file_size)

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

    def update(self, request, *args, **kwargs):
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
                file.upload.name
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
            os.rename(initial_destination, final_destination)
            file.upload.name = str(upload_name)
            file.save()
        return super().update(request, *args, **kwargs)

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
        total_file_size = 0
        for file in files:
            total_file_size = total_file_size + file.size
        try:
            reduce_content_size(parent_folder, total_file_size)
            files.delete()
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return HttpResponse(f'error in deleting files due to {e}', status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        parent_folder = instance.folder
        reduce_content_size(parent_folder, instance.size)
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
        share_with_all = request.data.get('share_with_all') == 'true'
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
                file.share_with_all = share_with_all
                for user in deleted_users:
                    person = Person.objects.get(
                        id=user)
                    file.shared_users.remove(person)
                for user in new_users:
                    person = Person.objects.get(
                        id=user)
                    file.shared_users.add(person)
                file.save()
                updated_file = FileSerializer(file)
                return Response(updated_file.data)
            except Exception as e:
                return HttpResponse(f'Error occured while updating users due to {e}', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return HttpResponse(f'Unable to change shared_user due to {e}', status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False, url_name='zip', url_path='zip')
    def zip(self, request):
        data = request.data
        try:
            folder = Folder.objects.get(pk=data.get('folder'))
            parent_folder = folder
        except Folder.DoesNotExist:
            return HttpResponse('parent folder doesnot found', status=status.HTTP_400_BAD_REQUEST)
        self.check_object_permissions(self.request, parent_folder)

        if not parent_folder.root == None:
            root_folder = parent_folder.root
        else:
            root_folder = parent_folder

        file = data.get('upload')
        file_path = file.temporary_file_path()
        directory_path = os.path.dirname(file_path)

        contents = []
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            size = sum([zinfo.file_size for zinfo in zip_ref.filelist])
            if root_folder.content_size + size > root_folder.max_space:
                return HttpResponse('Space limit exceeded', status=status.HTTP_400_BAD_REQUEST)

            for p in zip_ref.namelist():
                contents.append(p.split('/')[0])
            zip_ref.extractall(directory_path)
        contents = list(set(contents))
        if parent_folder.filemanager.is_public:
            base_location = 'public'
        else:
            base_location = 'protected'

        filemanager_path = os.path.join(
            settings.NETWORK_STORAGE_ROOT, base_location, parent_folder.filemanager.filemanager_url_path)
        for content in contents:
            path = os.path.join(directory_path, content)
            final_destination = os.path.join(parent_folder.path, content)
            if os.path.isdir(path) and not os.path.exists(final_destination):
                content = sanitize_folder_name(os.path.join(
                    filemanager_path, parent_folder.get_path()), content)
                shift_single_folder(
                    path, parent_folder.path, filemanager_path, parent_folder.filemanager, content)
                shutil.move(path, os.path.join(
                    filemanager_path, parent_folder.get_path(), content))
            elif os.path.isfile(path) and not os.path.exists(final_destination):
                parent_folders = parent_folder.get_path().split('/')
                parent_path = filemanager_path
                for parent in parent_folders:
                    parent_path = os.path.join(parent_path, parent)
                    if not os.path.isdir(parent_path):
                        os.mkdir(parent_path)
                content = file_exists(parent_path, content)
                extension = os.path.splitext(path)[1]
                filesize = os.path.getsize(path)
                file_obj = create_file(
                    parent_folder, content, extension, filesize)
                shutil.copy(path, os.path.join(
                    parent_path, content))
        add_content_size(parent_folder, size)
        return HttpResponse('Created', status=status.HTTP_200_OK)
