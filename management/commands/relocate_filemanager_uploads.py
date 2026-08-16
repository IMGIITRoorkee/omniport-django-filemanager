import os
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand

from django_filemanager.models import File
from django_filemanager.upload_to import storage_path


class Command(BaseCommand):
    """
    This class describes the command to be executed
    """

    help = """Relocate every file whose stored path still holds the name it was
    uploaded under, so that the path stops being derivable from the owner's
    identifier and the name of the document. File.file_name keeps that name for
    display and download. Safe to interrupt and to run again: a file is linked
    to its new path before the row is written and unlinked from the old path
    only after, so an interrupted run never leaves a row without a file.
    Usage: django-admin relocate_filemanager_uploads [--dry-run]
    """

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        relocated = already_opaque = missing = 0

        for file in File.objects.select_related(
                'folder__filemanager').order_by('pk').iterator():
            name = file.upload.name
            if not name or is_opaque(name):
                already_opaque += 1
                continue

            source = os.path.join(settings.NETWORK_STORAGE_ROOT, name)
            if not os.path.isfile(source):
                self.stderr.write(f'{file.pk}: nothing stored at {name}')
                missing += 1
                continue

            # The extension comes off the stored name rather than off
            # file_name, because it is the stored name that is served
            destination_name = storage_path(
                file.folder, os.path.basename(name))
            self.stdout.write(f'{file.pk}: {name} -> {destination_name}')
            relocated += 1
            if dry_run:
                continue

            destination = os.path.join(
                settings.NETWORK_STORAGE_ROOT, destination_name)
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            os.link(source, destination)
            File.objects.filter(pk=file.pk).update(
                upload=destination_name,
                file_name=file.file_name or os.path.basename(name),
            )
            os.remove(source)

        summary = (f'{relocated} relocated, {already_opaque} already opaque, '
                   f'{missing} missing')
        if dry_run:
            self.stdout.write(self.style.WARNING(f'Dry run: {summary}'))
        else:
            self.stdout.write(self.style.SUCCESS(summary))


def is_opaque(name):
    """
    Report whether a stored path already carries an opaque name
    :param name: the stored path of a file
    :return: whether its last segment is a UUID
    """

    try:
        uuid.UUID(os.path.splitext(os.path.basename(name))[0])
    except ValueError:
        return False
    return True
