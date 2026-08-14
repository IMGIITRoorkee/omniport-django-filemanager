"""
Resolution of the FileManager configuration fields that were previously
evaluated as Python. Those fields are database backed, so evaluating them
handed anyone able to write the table arbitrary code execution.
"""

import ast

PERSON_ROOT = 'person'


def resolve_folder_name(template, person):
    """
    Resolve a root folder name template against a person
    :param template: a dotted attribute path rooted at the person, such as the
    default 'person.user.username'
    :param person: the person the folder belongs to
    :return: the resolved folder name
    """

    segments = template.split('.')
    if segments[0] != PERSON_ROOT:
        raise ValueError(f'folder name template must start with {PERSON_ROOT}')
    value = person
    for segment in segments[1:]:
        value = getattr(value, segment)
    return value


def evaluate_access_permission(expression):
    """
    Evaluate a filemanager access permission
    :param expression: a boolean literal, the model default being 'True'
    :return: whether the filemanager grants a root folder
    """

    value = ast.literal_eval(expression)
    if not isinstance(value, bool):
        raise ValueError('access permission must be a boolean literal')
    return value
