from django.core.files.storage import FileSystemStorage


class CleanFileNameStorage(FileSystemStorage):

    def get_valid_name(self, name):
        """
        Return a filename, based on the provided filename, that's suitable for
        use in the target storage system.
        """
        return name
