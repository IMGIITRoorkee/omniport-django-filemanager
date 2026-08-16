from django.core.files.storage import FileSystemStorage


class CleanFileNameStorage(FileSystemStorage):
    """
    Named by the migrations. Its get_valid_name used to return the uploaded
    filename unchanged, which switched off the sanitisation Django applies.
    """
