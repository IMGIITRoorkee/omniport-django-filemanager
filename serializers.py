import os

from rest_framework import serializers

from kernel.managers.get_role import get_all_roles

from formula_one.serializers.base import ModelSerializer
from django_filemanager.models import Folder, File, FileManager, BASE_PROTECTED_URL
from kernel.models import Person


class PersonSerializer(ModelSerializer):

    class Meta:
        model = Person
        fields = ['id', 'display_picture', 'full_name']


class subFolderSerializer(ModelSerializer):
    filemanagername = serializers.ReadOnlyField()
    person = PersonSerializer(read_only=True)
    shared_users = PersonSerializer(many=True, read_only=True)
    is_filemanager_public = serializers.ReadOnlyField()
    public_folder_url = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = '__all__'

    def get_public_folder_url(self, obj):
        person = None
        request = self.context.get("request")
        if request and hasattr(request, "person"):
            person = request.person
        if(not obj.filemanager.is_public):
            return None
        try:
            baseUrl = eval(obj.filemanager.base_public_url)
            if obj.root:
                root_folder_path = f"{obj.root.get_path()}/"
            else:
                root_folder_path = f"{obj.get_path()}/"
            remaining_path = obj.get_path().split(root_folder_path, 1)[-1]
            path = os.path.join(baseUrl, remaining_path)
        except:
            path = None
        return path


class FileSerializer(ModelSerializer):
    """
    Serializer for File object
    """

    path = serializers.ReadOnlyField()
    shared_users = PersonSerializer(many=True, read_only=True)
    folder = subFolderSerializer()
    file_url = serializers.SerializerMethodField()
    is_filemanager_public = serializers.ReadOnlyField()

    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ['shared_users']

    def get_file_url(self, obj):
        person = None
        request = self.context.get("request")
        if request and hasattr(request, "person"):
            person = request.person
        if(not obj.folder.filemanager.is_public):
            return obj.upload.name
        try:
            baseUrl = eval(obj.folder.filemanager.base_public_url)
            if obj.folder.root:
                root_folder_path = f"{obj.folder.root.get_path()}/"
            else:
                root_folder_path = f"{obj.folder.get_path()}/"
            remaining_path = obj.upload.name.split(root_folder_path, 1)[-1]
            path = os.path.join(baseUrl, remaining_path)
        except:
            baseUrl = BASE_PROTECTED_URL
            remaining_path = obj.upload.name
            path = os.path.join(baseUrl, remaining_path)
        return path


class FolderSerializer(ModelSerializer):
    """
    Serializer for Folder object
    """

    files = FileSerializer(many=True,  read_only=True)
    folders = subFolderSerializer(read_only=True, many=True)
    filemanagername = serializers.ReadOnlyField()
    person = PersonSerializer(read_only=True)
    shared_users = PersonSerializer(many=True, read_only=True)
    is_filemanager_public = serializers.ReadOnlyField()

    class Meta:
        model = Folder
        fields = '__all__'
        read_only_fields = ['person', 'filemanagername', 'max_space'
                            'content_size', 'shared_users', 'path', 'is_filemanager_public']

    def create(self, validated_data):
        """
        Create a new Folder instance from the validated data, adding person
        :param validated_data: the validated data passed to the serializer
        :return: the newly-created Folder instance
        """

        person = self.context.get('request').person
        validated_data['person'] = person
        application = super().create(validated_data)

        return application


class FileManagerSerializer(ModelSerializer):
    """
    Serializer for filemanager object
    """

    class Meta:
        model = FileManager
        fields = '__all__'


class rootFolderSerializer(ModelSerializer):
    person = PersonSerializer(read_only=True)
    filemanager = FileManagerSerializer(read_only=True)

    class Meta:
        model = Folder
        fields = ['id', 'content_size',
                  'max_space', 'data_request_status', 'additional_space', 'person', 'filemanager', 'is_filemanager_public']
        read_only_fields = ['max_space',
                            'data_request_status', 'additional_space', 'filemanager', 'is_filemanager_public']
