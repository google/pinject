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
import re
import threading
import types

from .third_party import decorator

from . import binding_keys
from . import decorators
from . import errors
from . import providing
from . import scoping


class Binding(object):

    def __init__(self, binding_key, proviser_fn, scope_id, binding_location):
        self.binding_key = binding_key
        self.proviser_fn = proviser_fn
        self.scope_id = scope_id
        self._binding_location = binding_location

    def __str__(self):
        return 'the binding at {0}, from {1} to {2}, in "{3}" scope'.format(
            self._binding_location, self.binding_key,
            self.proviser_fn._pinject_desc, self.scope_id)


def _handle_explicit_binding_collision(
        colliding_binding, binding_key_to_binding, *pargs):
    other_binding = binding_key_to_binding[colliding_binding.binding_key]
    raise errors.ConflictingBindingsError([colliding_binding, other_binding])


def _handle_implicit_binding_collision(
        colliding_binding, binding_key_to_binding,
        collided_binding_key_to_bindings):
    binding_key = colliding_binding.binding_key
    bindings = collided_binding_key_to_bindings.setdefault(
        binding_key, set())
    bindings.add(binding_key_to_binding[binding_key])
    del binding_key_to_binding[binding_key]


def _get_binding_key_to_binding_maps(bindings, handle_binding_collision_fn):
    binding_key_to_binding = {}
    collided_binding_key_to_bindings = {}
    for binding_ in bindings:
        binding_key = binding_.binding_key
        if binding_key in binding_key_to_binding:
            handle_binding_collision_fn(
                binding_, binding_key_to_binding,
                collided_binding_key_to_bindings)
        if binding_key in collided_binding_key_to_bindings:
            collided_binding_key_to_bindings[binding_key].add(binding_)
        else:
            binding_key_to_binding[binding_key] = binding_
    return binding_key_to_binding, collided_binding_key_to_bindings


def get_overall_binding_key_to_binding_maps(bindings_lists):

    """bindings_lists from lowest to highest priority.  Last item in
    bindings_lists is assumed explicit.

    """
    binding_key_to_binding = {}
    collided_binding_key_to_bindings = {}

    for index, bindings in enumerate(bindings_lists):
        is_final_index = (index == (len(bindings_lists) - 1))
        handle_binding_collision_fn = {
            True: _handle_explicit_binding_collision,
            False: _handle_implicit_binding_collision}[is_final_index]
        this_binding_key_to_binding, this_collided_binding_key_to_bindings = (
            _get_binding_key_to_binding_maps(bindings, handle_binding_collision_fn))
        for good_binding_key in this_binding_key_to_binding:
            collided_binding_key_to_bindings.pop(good_binding_key, None)
        binding_key_to_binding.update(this_binding_key_to_binding)
        collided_binding_key_to_bindings.update(
            this_collided_binding_key_to_bindings)

    return binding_key_to_binding, collided_binding_key_to_bindings


class BindingMapping(object):

    def __init__(self, binding_key_to_binding,
                 collided_binding_key_to_bindings):
        self._binding_key_to_binding = binding_key_to_binding
        self._collided_binding_key_to_bindings = (
            collided_binding_key_to_bindings)

    def get(self, binding_key):
        if binding_key in self._binding_key_to_binding:
            return self._binding_key_to_binding[binding_key]
        elif binding_key in self._collided_binding_key_to_bindings:
            raise errors.AmbiguousArgNameError(
                binding_key,
                self._collided_binding_key_to_bindings[binding_key])
        else:
            raise errors.NothingInjectableForArgError(binding_key)


def default_get_arg_names_from_class_name(class_name):
    """Converts normal class names into normal arg names.

    Normal class names are assumed to be CamelCase with an optional leading
    underscore.  Normal arg names are assumed to be lower_with_underscores.

    Args:
      class_name: a class name, e.g., "FooBar" or "_FooBar"
    Returns:
      all likely corresponding arg names, e.g., ["foo_bar"]
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


def get_explicit_class_bindings(
        classes,
        get_arg_names_from_class_name=default_get_arg_names_from_class_name):
    explicit_bindings = []
    for cls in classes:
        if decorators.is_explicitly_injectable(cls):
            for arg_name in get_arg_names_from_class_name(cls.__name__):
                binding_key = binding_keys.new(arg_name)
                proviser_fn = create_class_proviser_fn(binding_key, cls)
                explicit_bindings.append(Binding(
                    binding_key, proviser_fn, scoping.DEFAULT_SCOPE,
                    _get_obj_location(cls)))
    return explicit_bindings


def get_provider_bindings(
        binding_spec,
        get_arg_names_from_provider_fn_name=(
            providing.default_get_arg_names_from_provider_fn_name)):
    provider_bindings = []
    fns = inspect.getmembers(binding_spec, lambda x: type(x) == types.MethodType)
    for _, fn in fns:
        default_arg_names = get_arg_names_from_provider_fn_name(fn.__name__)
        provider_bindings.extend(
            get_provider_fn_bindings(fn, default_arg_names))
    return provider_bindings


def get_implicit_class_bindings(
        classes,
        get_arg_names_from_class_name=(
            default_get_arg_names_from_class_name)):
    implicit_bindings = []
    for cls in classes:
        arg_names = get_arg_names_from_class_name(cls.__name__)
        for arg_name in arg_names:
            binding_key = binding_keys.new(arg_name)
            proviser_fn = create_class_proviser_fn(binding_key, cls)
            implicit_bindings.append(Binding(
                binding_key, proviser_fn, scoping.DEFAULT_SCOPE,
                _get_obj_location(cls)))
    return implicit_bindings


class Binder(object):

    def __init__(self, collected_bindings, scope_ids):
        self._collected_bindings = collected_bindings
        self._scope_ids = scope_ids
        self._lock = threading.Lock()
        self._class_bindings_created = []

    def bind(self, arg_name, annotated_with=None,
             to_class=None, to_instance=None, in_scope=scoping.DEFAULT_SCOPE):
        if in_scope not in self._scope_ids:
            raise errors.UnknownScopeError(in_scope)
        binding_key = binding_keys.new(arg_name, annotated_with)
        specified_to_params = ['to_class' if to_class is not None else None,
                               'to_instance' if to_instance is not None else None]
        specified_to_params = [x for x in specified_to_params if x is not None]
        if not specified_to_params:
            raise errors.NoBindingTargetError(binding_key)
        elif len(specified_to_params) > 1:
            raise errors.MultipleBindingTargetsError(
                binding_key, specified_to_params)

        # TODO(kurts): this is such a hack; isn't there a better way?
        if to_class is not None:
            @decorators.annotate_arg('_pinject_class', (to_class, in_scope))
            @decorators.provides(annotated_with=annotated_with, in_scope=in_scope)
            def provide_it(_pinject_class):
                return _pinject_class
            with self._lock:
                self._collected_bindings.extend(
                    get_provider_fn_bindings(provide_it, [arg_name]))
                if (to_class, in_scope) not in self._class_bindings_created:
                    self._collected_bindings.append(Binding(
                        binding_keys.new('_pinject_class', (to_class, in_scope)),
                        create_class_proviser_fn(binding_key, to_class),
                        in_scope, _get_obj_location(to_class)))
                    self._class_bindings_created.append((to_class, in_scope))
        else:
            proviser_fn = create_instance_proviser_fn(binding_key, to_instance)
            back_frame = inspect.currentframe().f_back
            with self._lock:
                self._collected_bindings.append(Binding(
                    binding_key, proviser_fn, in_scope,
                    '{0}:{1}'.format(back_frame.f_code.co_filename,
                                     back_frame.f_lineno)))


def _get_obj_location(cls):
    try:
        return '{0}:{1}'.format(
            inspect.getfile(cls), inspect.getsourcelines(cls)[1])
    except (TypeError, IOError):
        return 'unknown location'


def _get_class_name_and_loc(cls):
    try:
        return '{0} at {1}:{2}'.format(
            cls.__name__, inspect.getfile(cls), inspect.getsourcelines(cls)[1])
    except (TypeError, IOError):
        return '{0}.{1}'.format(inspect.getmodule(cls).__name__, cls.__name__)


def create_class_proviser_fn(binding_key, to_class):
    if not inspect.isclass(to_class):
        raise errors.InvalidBindingTargetError(
            binding_key, to_class, 'class')
    proviser_fn = lambda injection_context, obj_provider: obj_provider.provide_class(
        to_class, injection_context)
    class_name_and_loc = _get_class_name_and_loc(to_class)
    proviser_fn._pinject_desc = 'the class {0}'.format(class_name_and_loc)
    return proviser_fn


def create_instance_proviser_fn(binding_key, to_instance):
    proviser_fn = lambda injection_context, obj_provider: to_instance
    proviser_fn._pinject_desc = 'the instance {0!r}'.format(to_instance)
    return proviser_fn


class BindingSpec(object):

    def configure(self, bind):
        raise NotImplementedError()

    def dependencies(self):
        return []


def get_provider_fn_bindings(provider_fn, default_arg_names):
    annotated_with, arg_names, in_scope_id = (
        decorators._get_provider_fn_decorations(provider_fn, default_arg_names))
    proviser_fn = lambda injection_context, obj_provider: (
        obj_provider.call_with_injection(provider_fn, injection_context))
    proviser_fn._pinject_desc = 'the provider {0!r}'.format(provider_fn)
    return [
        Binding(binding_keys.new(arg_name, annotated_with), proviser_fn,
                in_scope_id, _get_obj_location(provider_fn))
        for arg_name in arg_names]
