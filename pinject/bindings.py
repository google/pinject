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
from . import locations
from . import providing
from . import scoping


class Binding(object):

    def __init__(self, binding_key, proviser_fn, get_binding_target_desc_fn,
                 scope_id, get_binding_loc_fn):
        self.binding_key = binding_key
        self.proviser_fn = proviser_fn
        self.get_binding_target_desc_fn = get_binding_target_desc_fn
        self.scope_id = scope_id
        self._get_binding_loc_fn = get_binding_loc_fn

    def __str__(self):
        return 'the binding at {0}, from {1} to {2}, in "{3}" scope'.format(
            self._get_binding_loc_fn(), self.binding_key,
            self.get_binding_target_desc_fn(), self.scope_id)


def _handle_explicit_binding_collision(
        colliding_binding, binding_key_to_binding, *pargs):
    other_binding = binding_key_to_binding[colliding_binding.binding_key]
    raise errors.ConflictingExplicitBindingsError(
        [colliding_binding, other_binding])


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
            _get_binding_key_to_binding_maps(
                bindings, handle_binding_collision_fn))
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

    def verify_requirements(self, required_bindings):
        for required_binding in required_bindings:
            required_binding_key = required_binding.binding_key
            if required_binding_key not in self._binding_key_to_binding:
                if (required_binding_key in
                    self._collided_binding_key_to_bindings):
                    raise errors.ConflictingRequiredBindingError(
                        required_binding,
                        self._collided_binding_key_to_bindings[
                            required_binding_key])
                else:
                    raise errors.MissingRequiredBindingError(required_binding)

    def get(self, binding_key, injection_site_desc):
        if binding_key in self._binding_key_to_binding:
            return self._binding_key_to_binding[binding_key]
        elif binding_key in self._collided_binding_key_to_bindings:
            raise errors.AmbiguousArgNameError(
                injection_site_desc, binding_key,
                self._collided_binding_key_to_bindings[binding_key])
        else:
            raise errors.NothingInjectableForArgError(
                binding_key, injection_site_desc)


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
                explicit_bindings.append(new_binding_to_class(
                    binding_keys.new(arg_name), cls, scoping.DEFAULT_SCOPE,
                    lambda cls=cls: locations.get_loc(cls)))
    return explicit_bindings


def get_provider_bindings(
        binding_spec, known_scope_ids,
        get_arg_names_from_provider_fn_name=(
            providing.default_get_arg_names_from_provider_fn_name)):
    provider_bindings = []
    fns = inspect.getmembers(binding_spec,
                             lambda x: type(x) == types.MethodType)
    for _, fn in fns:
        default_arg_names = get_arg_names_from_provider_fn_name(fn.__name__)
        fn_bindings = get_provider_fn_bindings(fn, default_arg_names)
        for binding in fn_bindings:
            if binding.scope_id not in known_scope_ids:
                raise errors.UnknownScopeError(
                    binding.scope_id, locations.get_name_and_loc(fn))
        provider_bindings.extend(fn_bindings)
    return provider_bindings


def get_implicit_class_bindings(
        classes,
        get_arg_names_from_class_name=(
            default_get_arg_names_from_class_name)):
    implicit_bindings = []
    for cls in classes:
        arg_names = get_arg_names_from_class_name(cls.__name__)
        for arg_name in arg_names:
            implicit_bindings.append(new_binding_to_class(
                binding_keys.new(arg_name), cls, scoping.DEFAULT_SCOPE,
                lambda cls=cls: locations.get_loc(cls)))
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
            raise errors.UnknownScopeError(
                in_scope, locations.get_back_frame_loc())
        binding_key = binding_keys.new(arg_name, annotated_with)
        specified_to_params = [
            'to_class' if to_class is not None else None,
            'to_instance' if to_instance is not None else None]
        specified_to_params = [x for x in specified_to_params if x is not None]
        if not specified_to_params:
            binding_loc = locations.get_back_frame_loc()
            raise errors.NoBindingTargetArgsError(binding_loc, binding_key)
        elif len(specified_to_params) > 1:
            binding_loc = locations.get_back_frame_loc()
            raise errors.MultipleBindingTargetArgsError(
                binding_loc, binding_key, specified_to_params)

        # TODO(kurts): this is such a hack; isn't there a better way?
        if to_class is not None:
            @decorators.annotate_arg('_pinject_class', (to_class, in_scope))
            @decorators.provides(annotated_with=annotated_with,
                                 in_scope=in_scope)
            def provide_it(_pinject_class):
                return _pinject_class
            with self._lock:
                self._collected_bindings.extend(
                    get_provider_fn_bindings(provide_it, [arg_name]))
                if (to_class, in_scope) not in self._class_bindings_created:
                    back_frame_loc = locations.get_back_frame_loc()
                    self._collected_bindings.append(new_binding_to_class(
                        binding_keys.new('_pinject_class',
                                         (to_class, in_scope)),
                        to_class, in_scope, lambda: back_frame_loc))
                    self._class_bindings_created.append((to_class, in_scope))
        else:
            back_frame_loc = locations.get_back_frame_loc()
            with self._lock:
                self._collected_bindings.append(new_binding_to_instance(
                    binding_key, to_instance, in_scope,
                    lambda: back_frame_loc))


def new_binding_to_class(binding_key, to_class, in_scope, get_binding_loc_fn):
    if not inspect.isclass(to_class):
        raise errors.InvalidBindingTargetError(
            get_binding_loc_fn(), binding_key, to_class, 'class')
    def Proviser(injection_context, obj_provider, pargs, kwargs):
        return obj_provider.provide_class(
            to_class, injection_context, pargs, kwargs)
    def GetBindingTargetDesc():
        return 'the class {0}'.format(locations.get_name_and_loc(to_class))
    return Binding(binding_key, Proviser, GetBindingTargetDesc, in_scope,
                   get_binding_loc_fn)


def new_binding_to_instance(
        binding_key, to_instance, in_scope, get_binding_loc_fn):
    def Proviser(injection_context, obj_provider, pargs, kwargs):
        if pargs or kwargs:
            raise TypeError('instance provider takes no arguments'
                            ' ({0} given)'.format(len(pargs) + len(kwargs)))
        return to_instance
    def GetBindingTargetDesc():
        return 'the instance {0!r}'.format(to_instance)
    return Binding(binding_key, Proviser, GetBindingTargetDesc, in_scope,
                   get_binding_loc_fn)


class BindingSpec(object):

    def configure(self, bind):
        raise NotImplementedError()

    def dependencies(self):
        return []

    def __eq__(self, other):
        return type(self) == type(other)

    def __hash__(self):
        return hash(type(self))


def get_provider_fn_bindings(provider_fn, default_arg_names):
    provider_decorations = decorators.get_provider_fn_decorations(
        provider_fn, default_arg_names)
    def Proviser(injection_context, obj_provider, pargs, kwargs):
        return obj_provider.call_with_injection(
            provider_fn, injection_context, pargs, kwargs)
    def GetBindingTargetDescFn():
        return 'the provider method {0}'.format(
            locations.get_name_and_loc(provider_fn))
    return [
        Binding(binding_keys.new(provider_decoration.arg_name,
                                 provider_decoration.annotated_with),
                Proviser, GetBindingTargetDescFn,
                provider_decoration.in_scope_id,
                lambda p_fn=provider_fn: locations.get_loc(p_fn))
        for provider_decoration in provider_decorations]
