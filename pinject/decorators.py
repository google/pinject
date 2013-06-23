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
from . import scoping


_ARG_BINDING_KEYS_ATTR = '_pinject_arg_binding_keys'
_IS_WRAPPER_ATTR = '_pinject_is_wrapper'
_ORIG_FN_ATTR = '_pinject_orig_fn'
_PROVIDER_ANNOTATED_WITH_ATTR = '_pinject_provider_annotated_with'
_PROVIDER_ARG_NAME_ATTR = '_pinject_provider_arg_name'
_PROVIDER_IN_SCOPE_ID_ATTR = '_pinject_in_scope_id'


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
        raise errors.EmptyProvidesDecoratorError()
    return _get_pinject_wrapper(provider_arg_name=arg_name,
                                provider_annotated_with=annotated_with,
                                provider_in_scope_id=in_scope)


def _get_provider_fn_decorations(provider_fn, default_arg_names):
    """Retrieves the provider method-relevant info set by decorators.

    If any info wasn't set by decorators, then defaults are returned.

    Args:
      provider_fn: a (possibly decorated) provider function
      default_arg_names: the (possibly empty) arg names to use if none were
          specified via @provides()
    Returns:
      a tuple (annotated_with, arg_names, in_scope_id) where
          annotated_with: an annotation object
          arg_name: the name of the arg provided by the provider function
          in_scope: a scope ID
    """
    if hasattr(provider_fn, _IS_WRAPPER_ATTR):
        annotated_with = getattr(provider_fn, _PROVIDER_ANNOTATED_WITH_ATTR)
        arg_name = getattr(provider_fn, _PROVIDER_ARG_NAME_ATTR)
        if arg_name is not None:
            arg_names = [arg_name]
        else:
            arg_names = default_arg_names
        in_scope_id = getattr(provider_fn, _PROVIDER_IN_SCOPE_ID_ATTR)
        if in_scope_id is None:
            in_scope_id = scoping.DEFAULT_SCOPE
    else:
        annotated_with = None
        arg_names = default_arg_names
        in_scope_id = scoping.DEFAULT_SCOPE
    return annotated_with, arg_names, in_scope_id


def _get_pinject_decorated_fn(fn):
    if hasattr(fn, _IS_WRAPPER_ATTR):
        pinject_decorated_fn = fn
    else:
        def _pinject_decorated_fn(fn_to_wrap, *pargs, **kwargs):
            return fn_to_wrap(*pargs, **kwargs)
        pinject_decorated_fn = decorator.decorator(_pinject_decorated_fn, fn)
        # TODO(kurts): split this so that __init__() decorators don't get
        # provider attributes.
        setattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR, [])
        setattr(pinject_decorated_fn, _IS_WRAPPER_ATTR, True)
        setattr(pinject_decorated_fn, _ORIG_FN_ATTR, fn)
        setattr(pinject_decorated_fn, _PROVIDER_ANNOTATED_WITH_ATTR, None)
        setattr(pinject_decorated_fn, _PROVIDER_ARG_NAME_ATTR, None)
        setattr(pinject_decorated_fn, _PROVIDER_IN_SCOPE_ID_ATTR, None)
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
        if provider_arg_name is not None:
            if getattr(pinject_decorated_fn, _PROVIDER_ARG_NAME_ATTR) is not None:
                raise errors.DuplicateDecoratorError(
                    'arg_name', getattr(pinject_decorated_fn, _ORIG_FN_ATTR))
            setattr(pinject_decorated_fn, _PROVIDER_ARG_NAME_ATTR,
                    provider_arg_name)
        if provider_annotated_with is not None:
            if getattr(pinject_decorated_fn, _PROVIDER_ANNOTATED_WITH_ATTR) is not None:
                raise errors.DuplicateDecoratorError(
                    'annotated_with', getattr(pinject_decorated_fn, _ORIG_FN_ATTR))
            setattr(pinject_decorated_fn, _PROVIDER_ANNOTATED_WITH_ATTR,
                    provider_annotated_with)
        if provider_in_scope_id is not None:
            if getattr(pinject_decorated_fn, _PROVIDER_IN_SCOPE_ID_ATTR) is not None:
                raise errors.DuplicateDecoratorError(
                    'in_scope', getattr(pinject_decorated_fn, _ORIG_FN_ATTR))
            setattr(pinject_decorated_fn, _PROVIDER_IN_SCOPE_ID_ATTR,
                    provider_in_scope_id)
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
