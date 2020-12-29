from rest_framework import serializers

from formula_one.serializers.base import ModelSerializer
from django_filemanager.models import Folder, File, FileManager
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

    class Meta:
        model = Folder
        fields = '__all__'


class FileSerializer(ModelSerializer):
    """
    Serializer for File object
    """

    path = serializers.ReadOnlyField()
    shared_users = PersonSerializer(many=True, read_only=True)
    folder = subFolderSerializer()
    file_url = serializers.ReadOnlyField()
    is_filemanager_public = serializers.ReadOnlyField()

    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ['shared_users']


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
