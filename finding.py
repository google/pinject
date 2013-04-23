
import inspect
import sys


def find_classes(modules=None, classes=None):
    modules = _get_explicit_or_default_modules(modules, classes)
    if classes is not None:
        all_classes = set(classes)
    else:
        all_classes = set()
    for module in modules:
        # TODO(kurts): how is a module getting to be None??
        if module is not None:
            all_classes |= _find_classes_in_module(module)
    return all_classes


def _get_explicit_or_default_modules(modules=None, classes=None):
    if modules is None and classes is None:
        return sys.modules.values()
    elif modules is None:
        return []
    else:
        return modules


def _find_classes_in_module(module):
    classes = set()
    for member_name, member in inspect.getmembers(module):
        if inspect.isclass(member) and not member_name == '__class__':
            classes.add(member)
    return classes


def find_functions(modules=None, classes=None):
    modules = _get_explicit_or_default_modules(modules, classes)
    functions = set()
    for module in modules:
        # TODO(kurts): how is a module getting to be None??
        if module is not None:
            for member_name, member in inspect.getmembers(module):
                if inspect.isfunction(member):
                    functions.add(member)
    return functions
