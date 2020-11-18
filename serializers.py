from rest_framework import serializers

from formula_one.serializers.base import ModelSerializer
from django_filemanager.models import Folder, File, FileManager
from kernel.serializers.person import AvatarSerializer


class FileSerializer(ModelSerializer):
    """
    Serializer for File object
    """

    path = serializers.SerializerMethodField()
    shared_users = AvatarSerializer(many=True, read_only=True)

    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ['shared_users']

    def get_path(self, obj):
        return obj.file_relative_path()


class subFolderSerializer(ModelSerializer):
    filemanagername = serializers.ReadOnlyField()
    person = AvatarSerializer(read_only=True)
    shared_users = AvatarSerializer(many=True, read_only=True)

    class Meta:
        model = Folder
        fields = '__all__'


class FolderSerializer(ModelSerializer):
    """
    Serializer for Folder object
    """

    files = FileSerializer(many=True,  read_only=True)
    folders = subFolderSerializer(read_only=True, many=True)
    filemanagername = serializers.ReadOnlyField()
    person = AvatarSerializer(read_only=True)
    shared_users = AvatarSerializer(many=True, read_only=True)

    # def get_folders(self, obj):
    #     return obj.folders.all()

    class Meta:
        model = Folder
        fields = '__all__'
        read_only_fields = ['person', 'filemanagername', 'max_space'
                            'content_size', 'shared_users', 'path']

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


class rootFolderSerializer(ModelSerializer):
    filemanagername = serializers.ReadOnlyField()
    person = AvatarSerializer(read_only=True)

    class Meta:
        model = Folder
        fields = ['id', 'filemanagername', 'content_size',
                  'max_space', 'data_request_status', 'additional_space', 'person']
        read_only_fields = ['max_space',
                            'data_request_status', 'additional_space']


class FileManagerSerializer(ModelSerializer):
    """
    Serializer for filemanager object
    """

    class Meta:
        model = FileManager
        fields = '__all__'
