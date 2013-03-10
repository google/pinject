
import inspect
import sys


def FindClasses(modules=None, classes=None):
    if modules is None and classes is None:
        modules = sys.modules.values()
    elif modules is None:
        modules = []
    if classes is not None:
        all_classes = set(classes)
    else:
        all_classes = set()
    for module in modules:
        # TODO(kurts): how is a module getting to be None??
        if module is not None:
            all_classes |= _FindClassesInModule(module)
    return all_classes


def _FindClassesInModule(module):
    classes = set()
    for member_name, member in inspect.getmembers(module):
        if inspect.isclass(member) and not member_name == '__class__':
            classes.add(member)
    return classes
