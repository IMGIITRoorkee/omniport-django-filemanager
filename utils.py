import logging
import os

from rest_framework.serializers import ValidationError

from django_filemanager.expressions import (
    evaluate_access_permission,
    resolve_folder_name,
)
from django_filemanager.models import Folder, FileManager
from kernel.models import Person

logger = logging.getLogger(__name__)


def safe_item_name(name):
    """
    Reduce a caller supplied file or folder name to a name. Every stored name
    is later joined onto a directory to build a path on disk, so a separator
    or a parent reference in one escapes the storage tree.
    :param name: the name the caller asked for
    :return: the same name, once it cannot traverse
    """

    name = (name or '').strip()
    if not name or name in ('.', '..') or name != os.path.basename(name):
        raise ValidationError('a name is required and cannot traverse')
    return name


def update_root_folders(person):
    """
    Give the person a root folder in every filemanager that admits them. A
    filemanager whose configuration does not resolve is skipped, because every
    listing in the service walks this loop and one bad row must not empty it.
    :param person: the person whose root folders are brought up to date
    """

    for filemanager in FileManager.objects.all():
        try:
            Folder.objects.get(
                person=person, root=None, parent=None, filemanager=filemanager)
            continue
        except Folder.DoesNotExist:
            pass

        try:
            if not evaluate_access_permission(
                    filemanager.filemanager_access_permissions, person):
                continue
            folder_name = resolve_folder_name(
                filemanager.folder_name_template, person)
            Folder.objects.create(filemanager=filemanager,
                                  folder_name=folder_name,
                                  person=person,
                                  max_space=filemanager.max_space,
                                  starred=False,
                                  root=None,
                                  parent=None,
                                  )
        except Exception:
            logger.exception(
                'No root folder for %s in %s', person, filemanager)


def add_content_size(parent_folder, size):
    while not parent_folder == None:
        updated_size = parent_folder.content_size + size
        parent_folder.content_size = updated_size
        parent_folder.save()
        parent_folder = parent_folder.parent


def reduce_content_size(parent_folder, size):
    while not parent_folder == None:
        updated_size = parent_folder.content_size - size
        parent_folder.content_size = updated_size
        parent_folder.save()
        parent_folder = parent_folder.parent


def is_file_shared(person, file):
    # share_with_all means every Channeli user, so an absent person is not one
    if person is None:
        return False
    parent_folder = file.folder
    if person in file.shared_users.all() or file.share_with_all:
        return True
    while not parent_folder == None:
        if(person in parent_folder.shared_users.all() or parent_folder.share_with_all):
            return True
        parent_folder = parent_folder.parent
    return False


def is_folder_shared(person, folder):
    # share_with_all means every Channeli user, so an absent person is not one
    if person is None:
        return False
    parent_folder = folder
    if person in folder.shared_users.all() or folder.share_with_all:
        return True
    while not parent_folder == None:
        if(person in parent_folder.shared_users.all() or parent_folder.share_with_all):
            return True
        parent_folder = parent_folder.parent
    return False
