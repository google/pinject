
import inspect
import re

import errors
import finding


def _default_get_arg_names_from_class_name(class_name):
    """Converts normal class names into normal arg names.

    Normal class names are assumed to be CamelCase with an optional leading
    underscore.  Normal arg names are assumed to be lower_with_underscores.

    Args:
      class_name: a class name, e.g., "FooBar"
    Returns:
      all likely corresponding param names, e.g., ["foo_bar"]
    """
    parts = []
    rest = class_name
    if rest.startswith('_'):
        rest = rest[1:]
    while True:
        m = re.match(r'([A-Z][a-z]+)(.*)', rest)
        if m is None:
            break
        parts.append(m.group(1))
        rest = m.group(2)
    if not parts:
        return []
    return ['_'.join(part.lower() for part in parts)]


def _new_arg_name_to_class_mapping(
    classes, get_arg_names_from_class_name=_default_get_arg_names_from_class_name):
    """Creates a mapping from arg names to classes.

    Args:
      classes: an iterable of classes
      get_arg_names_from_class_name: a function taking an (unqualified) class
          name and returning a (possibly empty) iterable of the arg names that
          would map to that class
    Returns:
      an _ArgNameClassMapping
    """
    arg_name_to_class = {}
    collided_arg_name_to_class_names = {}
    for cls in classes:
        arg_names = get_arg_names_from_class_name(cls.__name__)
        for arg_name in arg_names:
            if arg_name in arg_name_to_class:
                classes = collided_arg_name_to_class_names.setdefault(arg_name, set())
                classes.add('{0}.{1}'.format(arg_name_to_class[arg_name].__module__,
                                             arg_name_to_class[arg_name].__name__))
                del arg_name_to_class[arg_name]
            if arg_name in collided_arg_name_to_class_names:
                classes = collided_arg_name_to_class_names[arg_name]
                classes.add('{0}.{1}'.format(cls.__module__, cls.__name__))
            else:
                arg_name_to_class[arg_name] = cls
    return _ArgNameClassMapping(arg_name_to_class, collided_arg_name_to_class_names)


class _ArgNameClassMapping(object):
    """A mapping from arg names to classes."""

    def __init__(self, arg_name_to_class, collided_arg_name_to_class_names):
        self._arg_name_to_class = arg_name_to_class
        self._collided_arg_name_to_class_names = collided_arg_name_to_class_names

    def get(self, arg_name):
        if arg_name in self._arg_name_to_class:
            return self._arg_name_to_class[arg_name]
        elif arg_name in self._collided_arg_name_to_class_names:
            raise errors.AmbiguousArgNameError(
                'the arg name {0} ambiguously refers to any of the classes {1}'.format(
                    arg_name, self._collided_arg_name_to_class_names[arg_name]))
        else:
            raise errors.NothingInjectableForArgNameError(
                'there is no injectable class for the arg name {0}'.format(arg_name))


def NewInjector(modules=None, classes=None,
                get_arg_names_from_class_name=_default_get_arg_names_from_class_name,
                # binding_fns=None, binding_modules=None
                ):
    classes = finding.FindClasses(modules, classes)
    arg_name_class_mapping = _new_arg_name_to_class_mapping(
        classes, get_arg_names_from_class_name)
    return _Injector(arg_name_class_mapping)


class _Injector(object):

    def __init__(self, arg_name_class_mapping):
        self._arg_name_class_mapping = arg_name_class_mapping

    def provide(self, thing):
        if isinstance(thing, type):
            return self._provide_class(thing)
        else:
            raise errors.UnknownProvideIdentifierError(
                'cannot provide thing identified by {0}'.format(thing))

    def _provide_arg(self, arg_name):
        # TODO(kurts): make a reasonable error message if the mapping raises.
        arg_class = self._arg_name_class_mapping.get(arg_name)
        return self._provide_class(arg_class)

    def _provide_class(self, cls):
        init_kwargs = {}
        if cls.__init__ is not object.__init__:
            arg_names, unused_varargs, unused_keywords, unused_defaults = inspect.getargspec(cls.__init__)
            for arg_name in _ArgNamesWithoutSelf(arg_names):
                init_kwargs[arg_name] = self._provide_arg(arg_name)
        return cls(**init_kwargs)

    def wrap(self, fn):
        # TODO(kurts): use http://micheles.googlecode.com/hg/decorator/documentation.html
        arg_names, unused_varargs, unused_keywords, defaults = inspect.getargspec(fn)
        if defaults is None:
            defaults = []
        injectable_arg_names = arg_names[:(len(arg_names) - len(defaults))]
        def WrappedFn(*pargs, **kwargs):
            injected_arg_names = [
                arg_name for index, arg_name in enumerate(injectable_arg_names)
                if index >= len(pargs) and arg_name not in kwargs]
            if injected_arg_names:
                kwargs = dict(kwargs)
                for arg_name in injected_arg_names:
                    kwargs[arg_name] = self._provide_arg(arg_name)
            return fn(*pargs, **kwargs)
        return WrappedFn


def _ArgNamesWithoutSelf(args):
    return args[1:]


# class InjectorNotYetInstantiated(object):

#     def __getattribute__(self, unused_name):
#         def RaiseError(*pargs, **kwargs):
#             raise InjectorNotYetInstantiatedError()
#         return RaiseError


# class FutureInjector(object):

#     def __init__(self):
#         self._injector = InjectorNotYetInstantiated()

#     def __getattribute__(self, name):
#         return getattr(self._injector, name)

#     def set_injector(self, injector):
#         if isinstance(self._injector, InjectorNotYetInstantiated):
#             raise ProgrammerError('set_injector() should not be called twice')
#         self._injector = injector
