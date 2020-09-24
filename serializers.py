from rest_framework import serializers

from formula_one.serializers.base import ModelSerializer
from django_filemanager.models import Folder, File, FileManager


class FileSerializer(ModelSerializer):
    """
    Serializer for File object
    """

    path = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ['extension', 'size']

    def get_path(self, obj):
        return obj.file_relative_path()


class FileCreateSerializer(ModelSerializer):
    """
    Serializer for creating file object
    """

    class Meta:
        model = File
        exclude = ('folder',)

    def create(self, validated_data):
        """
        Create and return new File, given the validated data
        """

        person = self.context['request'].person
        folder, created = Folder.objects.get_or_create(person=person)
        file_object = File.objects.create(**validated_data, folder=folder)
        return file_object


class FileUpdateSerializer(ModelSerializer):
    """
    Serializer for updating file object
    """

    class Meta:
        model = File
        fields = ('file_name', 'is_public', 'id', 'datetime_modified')


class subFolderSerializer(ModelSerializer):
    class Meta:
        model = Folder
        fields = '__all__'


class FolderSerializer(ModelSerializer):
    """
    Serializer for Folder object
    """

    files = FileSerializer(many=True, source='file_set', read_only=True)
    folders = subFolderSerializer(read_only=True, many=True)

    # def get_folders(self, obj):
    #     return obj.folders.all()

    class Meta:
        model = Folder
        fields = '__all__'
        read_only_fields = ['person', 'max_space', 'content_size','files']

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
        read_only_fields = ['filemanager_name',]
