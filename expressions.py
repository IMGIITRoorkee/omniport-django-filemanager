"""
Resolution of the FileManager configuration fields that were previously
evaluated as Python. Those fields are database backed, so evaluating them
handed anyone able to write the table arbitrary code execution.

An access permission is parsed against this grammar and nothing wider:

    expression := 'True' | 'False'
                | "'<Role>'" ('in' | 'not in') roles
                | 'not' expression
                | expression ('and' | 'or') expression
    roles      := 'get_all_roles(person)' ['.keys()']

The source is parsed with ast.parse and walked node by node against the
allow-list below. Only get_all_roles is ever called, and only on the person,
so no part of the stored string is executed.
"""

import ast
import os

from kernel.managers.get_role import get_all_roles

PERSON = 'person'
ROLES = 'get_all_roles'
KEYS = 'keys'
# The admin form offers person.user.username; nothing else is a folder name
FOLDER_NAME_ATTRIBUTES = frozenset(
    {'user', 'username', 'full_name', 'short_name'})
PUBLIC_URL_SCHEMES = ('http://', 'https://')


def resolve_folder_name(template, person):
    """
    Resolve a root folder name template against a person
    :param template: a dotted attribute path rooted at the person, such as the
    default 'person.user.username'
    :param person: the person the folder belongs to
    :return: the resolved folder name
    """

    root, *attributes = template.strip().split('.')
    if root != PERSON:
        raise ValueError(f'a folder name template must start with {PERSON}')
    value = person
    for attribute in attributes:
        if attribute not in FOLDER_NAME_ATTRIBUTES:
            raise ValueError(f'{attribute} is not a folder name attribute')
        value = getattr(value, attribute)
    return value


def resolve_public_url(base_url, path):
    """
    Join a filemanager base public URL with a path below it
    :param base_url: the stored base_public_url
    :param path: the path of the item below the root folder
    :return: the public URL, or None if the stored value is not one
    """

    if not base_url or not base_url.startswith(PUBLIC_URL_SCHEMES):
        return None
    return os.path.join(base_url, path)


def evaluate_access_permission(expression, person):
    """
    Evaluate a filemanager access permission against a person
    :param expression: an expression in the grammar documented above
    :param person: the person seeking a root folder in the filemanager
    :return: whether the filemanager grants the person a root folder
    """

    try:
        tree = ast.parse(expression.strip(), mode='eval')
    except SyntaxError as error:
        raise ValueError(f'{expression} does not parse') from error
    return _evaluate(tree.body, person)


def _evaluate(node, person):
    """
    Evaluate one node of a parsed access permission
    :param node: the node to evaluate
    :param person: the person the permission is evaluated against
    :return: the boolean the node stands for
    """

    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _evaluate(node.operand, person)
    if isinstance(node, ast.BoolOp):
        results = [_evaluate(value, person) for value in node.values]
        return all(results) if isinstance(node.op, ast.And) else any(results)
    if isinstance(node, ast.Compare):
        return _evaluate_role_test(node, person)
    raise ValueError(f'{type(node).__name__} is not an access permission')


def _evaluate_role_test(node, person):
    """
    Evaluate the membership test the grammar admits
    :param node: the comparison to evaluate
    :param person: the person whose roles are tested
    :return: whether the person fulfills the role
    """

    if len(node.ops) != 1 or not isinstance(node.ops[0], (ast.In, ast.NotIn)):
        raise ValueError('a role test compares a role name against the roles')
    role = node.left
    if not isinstance(role, ast.Constant) or not isinstance(role.value, str):
        raise ValueError('a role test starts with a quoted role name')
    _assert_roles_of_person(node.comparators[0])
    is_fulfilled = role.value in get_all_roles(person)
    return is_fulfilled if isinstance(node.ops[0], ast.In) else not is_fulfilled


def _assert_roles_of_person(node):
    """
    Refuse anything that is not literally get_all_roles(person), written with
    or without a trailing .keys()
    :param node: the node the role name is tested against
    """

    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == KEYS and not node.args and not node.keywords):
        node = node.func.value
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == ROLES and not node.keywords
            and len(node.args) == 1 and isinstance(node.args[0], ast.Name)
            and node.args[0].id == PERSON):
        raise ValueError(f'a role test is against {ROLES}({PERSON})')
