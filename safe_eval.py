def safe_eval_filemanager(expr, person):
    """
    Evaluate a filemanager permission or template expression with restricted
    builtins. Prevents access to os, sys, import, and other dangerous builtins
    while still allowing role/model checks that filemanager expressions use.
    """
    safe_globals = {'__builtins__': {}}
    safe_locals = {
        'person': person,
        'isinstance': isinstance,
        'hasattr': hasattr,
        'getattr': getattr,
        'str': str,
        'int': int,
        'bool': bool,
        'True': True,
        'False': False,
        'None': None,
    }
    try:
        from shell.models import Student, FacultyMember
        from shell.models.roles.maintainer import Maintainer
        from kernel.managers.get_role import get_all_roles
        safe_locals.update({
            'Student': Student,
            'FacultyMember': FacultyMember,
            'Maintainer': Maintainer,
            'get_all_roles': get_all_roles,
        })
    except ImportError:
        pass
    return eval(expr, safe_globals, safe_locals)
