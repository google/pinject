"""Copyright 2013 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


import inspect

from .third_party import decorator

from . import arg_binding_keys
from . import binding_keys
from . import errors
from . import locations
from . import scoping


_ARG_BINDING_KEYS_ATTR = '_pinject_arg_binding_keys'
_IS_WRAPPER_ATTR = '_pinject_is_wrapper'
_ORIG_FN_ATTR = '_pinject_orig_fn'
_PROVIDER_DECORATIONS_ATTR = '_pinject_provider_decorations'


def annotate_arg(arg_name, with_annotation):
    """Adds an annotation to an injected arg.

    arg_name must be one of the named args of the decorated function, i.e.,
      @annotate_arg('foo', with_annotation='something')
      def a_function(foo):  # ...
    is OK, but
      @annotate_arg('foo', with_annotation='something')
      def a_function(bar, **kwargs):  # ...
    is not.

    The same arg (on the same function) may not be annotated twice.

    Args:
      arg_name: the name of the arg to annotate on the decorated function
      with_annotation: an annotation object
    Returns:
      a function that will decorate functions passed to it
    """
    arg_binding_key = arg_binding_keys.new(arg_name, with_annotation)
    return _get_pinject_wrapper(arg_binding_key=arg_binding_key)


def injectable(fn):
    """Marks an initializer explicitly as injectable.

    An initializer marked with @injectable will be usable even if setting
    only_use_explicit_bindings=True when calling new_object_graph().

    Args:
      fn: the function to decorate
    Returns:
      fn, decorated
    """
    if not inspect.isfunction(fn):
        raise errors.InjectableDecoratorAppliedToNonInitError(fn)
    if fn.__name__ != '__init__':
        raise errors.InjectableDecoratorAppliedToNonInitError(fn)
    return _get_pinject_decorated_fn(fn)


def provides(arg_name=None, annotated_with=None, in_scope=None):
    """Modifies the binding of a provider method.

    If arg_name is specified, then the created binding is for that arg name
    instead of the one gotten from the provider method name (e.g., 'foo' from
    'provide_foo').

    If annotated_with is specified, then the created binding includes that
    annotation object.

    If in_scope is specified, then the created binding is in the scope with
    that scope ID.

    At least one of the args must be specified.  A provider method may not be
    decorated with @provides() twice.

    Args:
      arg_name: the name of the arg to annotate on the decorated function
      annotated_with: an annotation object
      in_scope: a scope ID
    Returns:
      a function that will decorate functions passed to it
    """
    if arg_name is None and annotated_with is None and in_scope is None:
        raise errors.EmptyProvidesDecoratorError(locations.get_back_frame_loc())
    return _get_pinject_wrapper(provider_arg_name=arg_name,
                                provider_annotated_with=annotated_with,
                                provider_in_scope_id=in_scope)


class ProviderDecoration(object):
    """The provider method-relevant info set by @provides.

    Attributes:
      arg_name: the name of the arg provided by the provider function
      annotated_with: an annotation object
      in_scope_id: a scope ID
    """

    def __init__(self, arg_name, annotated_with, in_scope_id):
        self.arg_name = arg_name
        self.annotated_with = annotated_with
        self.in_scope_id = in_scope_id

    def __eq__(self, other):
        return (self.arg_name == other.arg_name and
                self.annotated_with == other.annotated_with and
                self.in_scope_id == other.in_scope_id)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return (hash(self.arg_name) ^ hash(self.annotated_with) ^
                hash(self.in_scope_id))


def get_provider_fn_decorations(provider_fn, default_arg_names):
    """Retrieves the provider method-relevant info set by decorators.

    If any info wasn't set by decorators, then defaults are returned.

    Args:
      provider_fn: a (possibly decorated) provider function
      default_arg_names: the (possibly empty) arg names to use if none were
          specified via @provides()
    Returns:
      a sequence of ProviderDecoration
    """
    if hasattr(provider_fn, _IS_WRAPPER_ATTR):
        provider_decorations = getattr(provider_fn, _PROVIDER_DECORATIONS_ATTR)
        if provider_decorations:
            expanded_provider_decorations = []
            for provider_decoration in provider_decorations:
                # TODO(kurts): seems like default scope should be done at
                # ProviderDecoration instantiation time.
                if provider_decoration.in_scope_id is None:
                    provider_decoration.in_scope_id = scoping.DEFAULT_SCOPE
                if provider_decoration.arg_name is not None:
                    expanded_provider_decorations.append(provider_decoration)
                else:
                    expanded_provider_decorations.extend(
                        [ProviderDecoration(default_arg_name,
                                            provider_decoration.annotated_with,
                                            provider_decoration.in_scope_id)
                         for default_arg_name in default_arg_names])
            return expanded_provider_decorations
    return [ProviderDecoration(default_arg_name,
                               annotated_with=None,
                               in_scope_id=scoping.DEFAULT_SCOPE)
            for default_arg_name in default_arg_names]


def _get_pinject_decorated_fn(fn):
    if hasattr(fn, _IS_WRAPPER_ATTR):
        pinject_decorated_fn = fn
    else:
        def _pinject_decorated_fn(fn_to_wrap, *pargs, **kwargs):
            return fn_to_wrap(*pargs, **kwargs)
        pinject_decorated_fn = decorator.decorator(_pinject_decorated_fn, fn)
        # TODO(kurts): split this so that __init__() decorators don't get
        # the provider attribute.
        setattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR, [])
        setattr(pinject_decorated_fn, _IS_WRAPPER_ATTR, True)
        setattr(pinject_decorated_fn, _ORIG_FN_ATTR, fn)
        setattr(pinject_decorated_fn, _PROVIDER_DECORATIONS_ATTR, [])
    return pinject_decorated_fn


def _get_pinject_wrapper(arg_binding_key=None, provider_arg_name=None,
                         provider_annotated_with=None, provider_in_scope_id=None):
    def get_pinject_decorated_fn_with_additions(fn):
        pinject_decorated_fn = _get_pinject_decorated_fn(fn)
        if arg_binding_key is not None:
            arg_names, unused_varargs, unused_keywords, unused_defaults = (
                inspect.getargspec(getattr(pinject_decorated_fn, _ORIG_FN_ATTR)))
            if not arg_binding_key.can_apply_to_one_of_arg_names(arg_names):
                raise errors.NoSuchArgToInjectError(arg_binding_key, fn)
            if arg_binding_key.conflicts_with_any_arg_binding_key(
                    getattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR)):
                raise errors.MultipleAnnotationsForSameArgError(arg_binding_key)
            getattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR).append(arg_binding_key)
        if (provider_arg_name is not None or
            provider_annotated_with is not None or
            provider_in_scope_id is not None):
            provider_decorations = getattr(
                pinject_decorated_fn, _PROVIDER_DECORATIONS_ATTR)
            provider_decorations.append(ProviderDecoration(
                provider_arg_name, provider_annotated_with,
                provider_in_scope_id))
        return pinject_decorated_fn
    return get_pinject_decorated_fn_with_additions


def is_explicitly_injectable(cls):
    return (hasattr(cls, '__init__') and
            hasattr(cls.__init__, _IS_WRAPPER_ATTR))


def get_injectable_arg_binding_keys(fn):
    if hasattr(fn, _IS_WRAPPER_ATTR):
        existing_arg_binding_keys = getattr(fn, _ARG_BINDING_KEYS_ATTR)
        arg_names, unused_varargs, unused_keywords, defaults = (
            inspect.getargspec(getattr(fn, _ORIG_FN_ATTR)))
        num_to_keep = (len(arg_names) - len(defaults)) if defaults else len(arg_names)
        arg_names = arg_names[:num_to_keep]
        unbound_arg_names = arg_binding_keys.get_unbound_arg_names(
            [arg_name for arg_name in _remove_self_if_exists(arg_names)],
            existing_arg_binding_keys)
    else:
        existing_arg_binding_keys = []
        arg_names, unused_varargs, unused_keywords, defaults = (
            inspect.getargspec(fn))
        num_to_keep = (len(arg_names) - len(defaults)) if defaults else len(arg_names)
        arg_names = arg_names[:num_to_keep]
        unbound_arg_names = _remove_self_if_exists(arg_names)
    all_arg_binding_keys = list(existing_arg_binding_keys)
    all_arg_binding_keys.extend([arg_binding_keys.new(arg_name)
                                 for arg_name in unbound_arg_names])
    return all_arg_binding_keys


# TODO(kurts): this feels icky.  Is there no way around this, because
# cls.__init__() takes self but instance.__init__() doesn't, and python is
# awkward here?
def _remove_self_if_exists(args):
    if args and args[0] == 'self':
        return args[1:]
    else:
        return args
