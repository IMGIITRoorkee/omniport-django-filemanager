from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

from django_filemanager.serializers import *
from django_filemanager.models import Folder, File, FileManager
from rest_framework.decorators import action


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
        print(filemanager_name)
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
                            parent=None, content_size=0, max_space=1024,filemanager=filemanager)
            folder.save()

            folder = Folder.objects.get(
                person=person, root=None, parent=None)
        except Folder.DoesNotExist:
            folder = Folder(person=person, root=None,
                            parent=None, content_size=0, max_space=1024)
            folder.save()
        except Folder.MultipleObjectsReturned:
            return Response("more than one root folder found for same person", status=status.HTTP_409_CONFLICT)
        print(folder)
        serializer = self.serializer_class(folder)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def get_root_folders(self,request):
        person = self.request.person
        folders = Folder.objects.filter(
            person=person, parent=None
        )
        serializer = rootFolderSerializer(
            folders, many=True
        )
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
    def get_queryset(self):
        person = self.request.person
        queryset = File.objects.filter(folder__person=person)
        return queryset


class FileManagerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This view allows user to view all existing filemanager instances
    """

    serializer_class = FileManagerSerializer
    queryset = FileManager.objects.all()
