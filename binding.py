
import re
import threading

import errors


class BindingKey(object):
    """The key for a binding."""

    pass


class BindingKeyWithoutAnnotation(BindingKey):
    """A key with no annotation."""

    def __init__(self, arg_name):
        self._arg_name = arg_name

    def __eq__(self, other):
        return (isinstance(other, BindingKeyWithoutAnnotation) and
                self._arg_name == other._arg_name)

    def __hash__(self):
        return hash(self._arg_name)

    def __str__(self):
        return 'the arg name {0}'.format(self._arg_name)


# class BindingKeyWithAnnotation(BindingKey):
#     """A key with an annotation."""

#     def __init__(self, arg_name, annotation):
#         self._arg_name = arg_name
#         self._annotation = annotation

#     def __eq__(self, other):
#         return (isinstance(other, BindingKeyWithAnnotation) and
#                 self._arg_name == other._arg_name and
#                 self._annotation == other._annotation)

#     def __hash__(self):
#         return hash(self._arg_name) ^ hash(self._annotation)

#     def __str__(self):
#         return 'the arg name {0} annotated with {1}'.format(
#             self._arg_name, self._annotation)


class Binding(object):

    def __init__(self, binding_key, provider_fn):
        self.binding_key = binding_key
        self.provider_fn = provider_fn


def new_binding_mapping(explicit_bindings, implicit_bindings):
    explicit_binding_key_to_provider_fn = {}
    for binding in explicit_bindings:
        binding_key = binding.binding_key
        provider_fn = binding.provider_fn
        if binding_key in explicit_binding_key_to_provider_fn:
            raise errors.ConflictingBindingsError(binding_key)
        explicit_binding_key_to_provider_fn[binding_key] = provider_fn

    implicit_binding_key_to_provider_fn = {}
    collided_binding_key_to_provider_fns = {}
    for binding in implicit_bindings:
        binding_key = binding.binding_key
        provider_fn = binding.provider_fn
        if binding_key in explicit_binding_key_to_provider_fn:
            continue
        if binding_key in implicit_binding_key_to_provider_fn:
            existing_provider_fn = implicit_binding_key_to_provider_fn[binding_key]
            del implicit_binding_key_to_provider_fn[binding_key]
            provider_fns = collided_binding_key_to_provider_fns.setdefault(
                binding_key, set())
            provider_fns.add('{0}.{1}'.format(existing_provider_fn.__module__,
                                              existing_provider_fn.__name__))
        if binding_key in collided_binding_key_to_provider_fns:
            provider_fnes = collided_binding_key_to_provider_fns[binding_key]
            provider_fnes.add('{0}.{1}'.format(provider_fn.__module__,
                                               provider_fn.__name__))
        else:
            implicit_binding_key_to_provider_fn[binding_key] = binding.provider_fn

    binding_key_to_provider_fn = explicit_binding_key_to_provider_fn
    binding_key_to_provider_fn.update(implicit_binding_key_to_provider_fn)
    return _BindingMapping(
        binding_key_to_provider_fn,  collided_binding_key_to_provider_fns)


class _BindingMapping(object):

    def __init__(self, binding_key_to_provider_fn,
                 collided_binding_key_to_provider_fns):
        self._binding_key_to_provider_fn = binding_key_to_provider_fn
        self._collided_binding_key_to_provider_fns = (
            collided_binding_key_to_provider_fns)

    def get_instance(self, binding_key):
        if binding_key in self._binding_key_to_provider_fn:
            return self._binding_key_to_provider_fn[binding_key]()
        elif binding_key in self._collided_binding_key_to_provider_fns:
            raise errors.AmbiguousArgNameError(
                binding_key,
                self._collided_binding_key_to_provider_fns[binding_key])
        else:
            raise errors.NothingInjectableForArgNameError(binding_key)


def default_get_arg_names_from_class_name(class_name):
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


def get_implicit_bindings(
    classes, future_injector,
    get_arg_names_from_class_name=default_get_arg_names_from_class_name):
    """Creates a mapping from arg names to classes.

    Args:
      classes: an iterable of classes
      get_arg_names_from_class_name: a function taking an (unqualified) class
          name and returning a (possibly empty) iterable of the arg names that
          would map to that class
    Returns:
      an _ArgNameClassMapping
    """
    implicit_bindings = []
    for cls in classes:
        arg_names = get_arg_names_from_class_name(cls.__name__)
        for arg_name in arg_names:
            binding_key = BindingKeyWithoutAnnotation(arg_name)
            def ProvideCls(cls=cls):
                return future_injector.provide(cls)
            implicit_bindings.append(Binding(binding_key, ProvideCls))
    return implicit_bindings


# class Binder(object):

#     def __init__(self, future_injector, collected_bindings):
#         self._future_injector = future_injector
#         self._collected_bindings = collected_bindings
#         self._lock = threading.Lock()

#     def bind(self, arg_name,  # annotated_with=None, in_scope=None
#              to_class=None, to_instance=None, to_provider=None):
#         binding_key = BindingKeyWithoutAnnotation(arg_name)

#         specified_to_params = ['to_class' if to_class is not None else None,
#                                'to_provider' if to_provider is not None else None,
#                                'to_instance' if to_instance is not None else None]
#         specified_to_params = [x for x in specified_to_params if x is not None]
#         if not specified_to_params:
#             raise errors.NoBindingTargetError(binding_key)
#         elif len(specified_to_params) > 1:
#             raise errors.MultipleBindingTargetsError(
#                 binding_key, specified_to_params)

#         if to_class is not None:
#             if not isinstance(to_class, type):
#                 raise errors.InvalidBindingTargetError(
#                     binding_key, to_class, 'class')
#             provider_fn = lambda: self._future_injector.provide(to_class)
#         elif to_instance is not None:
#             provider_fn = lambda: to_instance
#         else:  # to_provider is not None
#             if not callable(to_provider):
#                 raise errors.InvalidBindingTargetError(
#                     binding_key, to_provider, 'callable')
#             provider_fn = to_provider

#         with self._lock:
#             self._collected_bindings.append(Binding(binding_key, provider_fn))
