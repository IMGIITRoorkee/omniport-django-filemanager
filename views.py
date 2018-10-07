from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse

from django_filemanager.serializers import *
from django_filemanager.models import *


class FolderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This view gets all the files in a folder corresponding
    to the logged in user
    """

    serializer_class = FolderSerializer

    def get_queryset(self):
        person = self.request.person
        queryset = Folder.objects.filter(person=person)
        return queryset


class FileView(APIView):
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
            
            if (file_object.belongs_to()==person) or file_object.is_public:
                response = HttpResponse(status=200)
                response['Content-Type'] = ''
                response['X-Accel-Redirect'] = '/personal/{}'.format(url)
                return response

        response = HttpResponse(status=404)
        return response


class FileUploadView(viewsets.ModelViewSet):
    """
    This view allows a user to upload a file
    """

    serializer_class = FileCreateSerializer
    
    def get_queryset(self):
        person = self.request.person
        queryset = File.objects.filter(upload__person=person)
        return queryset
