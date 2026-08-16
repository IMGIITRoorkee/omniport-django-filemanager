import os

from rest_framework import serializers

from formula_one.serializers.base import ModelSerializer
from django_filemanager.expressions import resolve_public_url
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
        if(not obj.filemanager.is_public):
            return None
        if obj.root:
            root_folder_path = f"{obj.root.get_path()}/"
        else:
            root_folder_path = f"{obj.get_path()}/"
        remaining_path = obj.get_path().split(root_folder_path, 1)[-1]
        return resolve_public_url(
            obj.filemanager.base_public_url, remaining_path)


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
        if(not obj.folder.filemanager.is_public):
            return obj.upload.name
        if obj.folder.root:
            root_folder_path = f"{obj.folder.root.get_path()}/"
        else:
            root_folder_path = f"{obj.folder.get_path()}/"
        remaining_path = obj.upload.name.split(root_folder_path, 1)[-1]
        return resolve_public_url(
            obj.folder.filemanager.base_public_url, remaining_path
        ) or os.path.join(BASE_PROTECTED_URL, obj.upload.name)


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

    def validate(self, attrs):
        """
        Check that the folder hangs off a folder of the same person. A root
        folder is granted by the filemanager rather than created here.
        :param attrs: the deserialized data passed to the serializer
        :return: the same data, once the tree it names is the person's own
        """

        person = self.context.get('request').person
        if self.instance is None and attrs.get('parent') is None:
            raise serializers.ValidationError(
                {'parent': 'a root folder is granted by the filemanager'})
        for field in ('parent', 'root'):
            folder = attrs.get(field)
            if folder is not None and folder.person != person:
                raise serializers.ValidationError(
                    {field: 'must be a folder of your own'})
        return attrs

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
