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


import collections
import inspect

from .third_party import decorator

from . import arg_binding_keys
from . import binding_keys
from . import errors
from . import locations
from . import scoping


_ARG_BINDING_KEYS_ATTR = '_pinject_arg_binding_keys'
_IS_WRAPPER_ATTR = '_pinject_is_wrapper'
_NON_INJECTABLE_ARG_NAMES_ATTR = '_pinject_non_injectables'
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
    return _get_pinject_wrapper(locations.get_back_frame_loc(),
                                arg_binding_key=arg_binding_key)


def inject(arg_names=None, all_except=None):
    """Marks an initializer explicitly as injectable.

    An initializer marked with @inject will be usable even when setting
    only_use_explicit_bindings=True when calling new_object_graph().

    This decorator can be used on an initializer or provider method to
    separate the injectable args from the args that will be passed directly.
    If arg_names is specified, then it must be a sequence, and only those args
    are injected (and the rest must be passed directly).  If all_except is
    specified, then it must be a sequence, and only those args are passed
    directly (and the rest must be specified).  If neither arg_names nor
    all_except are specified, then all args are injected (and none may be
    passed directly).

    arg_names or all_except, when specified, must not be empty and must
    contain a (possibly empty, possibly non-proper) subset of the named args
    of the decorated function.  all_except may not be all args of the
    decorated function (because then why call that provider method or
    initialzer via Pinject?).  At most one of arg_names and all_except may be
    specified.  A function may be decorated by @inject at most once.

    """
    back_frame_loc = locations.get_back_frame_loc()
    if arg_names is not None and all_except is not None:
        raise errors.TooManyArgsToInjectDecoratorError(back_frame_loc)
    for arg, arg_value in [('arg_names', arg_names),
                           ('all_except', all_except)]:
        if arg_value is not None:
            if not arg_value:
                raise errors.EmptySequenceArgError(back_frame_loc, arg)
            if (not isinstance(arg_value, collections.Sequence) or
                isinstance(arg_value, basestring)):
                raise errors.WrongArgTypeError(
                    arg, 'sequence (of arg names)', type(arg_value).__name__)
    if arg_names is None and all_except is None:
        all_except = []
    return _get_pinject_wrapper(
        back_frame_loc, inject_arg_names=arg_names,
        inject_all_except_arg_names=all_except)


def injectable(fn):
    """Deprecated.  Use @inject() instead.

    TODO(kurts): remove after 2014/6/30.
    """
    return inject()(fn)


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
    return _get_pinject_wrapper(locations.get_back_frame_loc(),
                                provider_arg_name=arg_name,
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


# TODO(kurts): separate out the parts for different decorators.
def _get_pinject_wrapper(
        decorator_loc, arg_binding_key=None, provider_arg_name=None,
        provider_annotated_with=None, provider_in_scope_id=None,
        inject_arg_names=None, inject_all_except_arg_names=None):
    def get_pinject_decorated_fn_with_additions(fn):
        pinject_decorated_fn = _get_pinject_decorated_fn(fn)
        orig_arg_names, unused_varargs, unused_keywords, unused_defaults = (
            inspect.getargspec(getattr(pinject_decorated_fn, _ORIG_FN_ATTR)))
        if arg_binding_key is not None:
            if not arg_binding_key.can_apply_to_one_of_arg_names(
                    orig_arg_names):
                raise errors.NoSuchArgToInjectError(
                    decorator_loc, arg_binding_key, fn)
            if arg_binding_key.conflicts_with_any_arg_binding_key(
                    getattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR)):
                raise errors.MultipleAnnotationsForSameArgError(
                    arg_binding_key, decorator_loc)
            getattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR).append(
                arg_binding_key)
        if (provider_arg_name is not None or
            provider_annotated_with is not None or
            provider_in_scope_id is not None):
            provider_decorations = getattr(
                pinject_decorated_fn, _PROVIDER_DECORATIONS_ATTR)
            provider_decorations.append(ProviderDecoration(
                provider_arg_name, provider_annotated_with,
                provider_in_scope_id))
        if (inject_arg_names is not None or
            inject_all_except_arg_names is not None):
            if hasattr(pinject_decorated_fn, _NON_INJECTABLE_ARG_NAMES_ATTR):
                raise errors.DuplicateDecoratorError('inject', decorator_loc)
            non_injectable_arg_names = []
            setattr(pinject_decorated_fn, _NON_INJECTABLE_ARG_NAMES_ATTR,
                    non_injectable_arg_names)
            if inject_arg_names is not None:
                non_injectable_arg_names[:] = [
                    x for x in orig_arg_names if x not in inject_arg_names]
                arg_names_to_verify = inject_arg_names
            else:
                non_injectable_arg_names[:] = inject_all_except_arg_names
                arg_names_to_verify = inject_all_except_arg_names
            for arg_name in arg_names_to_verify:
                if arg_name not in orig_arg_names:
                    raise errors.NoSuchArgError(decorator_loc, arg_name)
            if len(non_injectable_arg_names) == len(orig_arg_names):
                raise errors.NoRemainingArgsToInjectError(decorator_loc)
        return pinject_decorated_fn
    return get_pinject_decorated_fn_with_additions


def is_explicitly_injectable(cls):
    return (hasattr(cls, '__init__') and
            hasattr(cls.__init__, _IS_WRAPPER_ATTR))


def get_injectable_arg_binding_keys(fn, direct_pargs, direct_kwargs):
    non_injectable_arg_names = []
    if hasattr(fn, _IS_WRAPPER_ATTR):
        existing_arg_binding_keys = getattr(fn, _ARG_BINDING_KEYS_ATTR)
        orig_fn = getattr(fn, _ORIG_FN_ATTR)
        if hasattr(fn, _NON_INJECTABLE_ARG_NAMES_ATTR):
            non_injectable_arg_names = getattr(
                fn, _NON_INJECTABLE_ARG_NAMES_ATTR)
    else:
        existing_arg_binding_keys = []
        orig_fn = fn

    arg_names, unused_varargs, unused_keywords, defaults = (
        inspect.getargspec(orig_fn))
    num_args_with_defaults = len(defaults) if defaults is not None else 0
    if num_args_with_defaults:
        arg_names = arg_names[:-num_args_with_defaults]
    unbound_injectable_arg_names = arg_binding_keys.get_unbound_arg_names(
        [arg_name for arg_name in _remove_self_if_exists(arg_names)
         if arg_name not in non_injectable_arg_names],
        existing_arg_binding_keys)

    all_arg_binding_keys = list(existing_arg_binding_keys)
    all_arg_binding_keys.extend([arg_binding_keys.new(arg_name)
                                 for arg_name in unbound_injectable_arg_names])
    return all_arg_binding_keys


# TODO(kurts): this feels icky.  Is there no way around this, because
# cls.__init__() takes self but instance.__init__() doesn't, and python is
# awkward here?
def _remove_self_if_exists(args):
    if args and args[0] == 'self':
        return args[1:]
    else:
        return args
