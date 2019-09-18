from rest_framework import serializers

from kernel.serializers.root import ModelSerializer
from django_filemanager.models import *


class FileSerializer(ModelSerializer):
    """
    Serializer for File object
    """

    path = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ('id', 'file_name', 'is_public', 'upload', 'path')

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
        fields = ('file_name', 'is_public', 'id')


class FolderSerializer(ModelSerializer):
    """
    Serializer for Folder object
    """

    files = FileSerializer(many=True, source='file_set')

    class Meta:
        model = Folder
        fields = ('files', 'folder_name')
