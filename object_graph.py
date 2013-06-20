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


import functools
import inspect
import types

from . import bindings
from . import binding_keys
from . import decorators
from . import errors
from . import finding
from . import injection_contexts
from . import object_providers
from . import providing
from . import scoping


_SHORT_USER_VISIBLE_STACK_TRACE = True


def new_object_graph(
        modules=finding.ALL_IMPORTED_MODULES, classes=None, binding_specs=None,
        only_use_explicit_bindings=False, allow_injecting_none=False,
        get_arg_names_from_class_name=(
            bindings.default_get_arg_names_from_class_name),
        get_arg_names_from_provider_fn_name=(
            providing.default_get_arg_names_from_provider_fn_name),
        id_to_scope=None, is_scope_usable_from_scope=lambda _1, _2: True):
    """
          is_scope_usable_from_scope_fn: a function taking two scope IDs and
              returning whether an object in the first scope can be injected
              into an object from the second scope
    """
    try:
        injection_context_factory = injection_contexts.InjectionContextFactory(
            is_scope_usable_from_scope)
        id_to_scope = scoping.get_id_to_scope_with_defaults(id_to_scope)
        bindable_scopes = scoping.BindableScopes(id_to_scope)
        known_scope_ids = id_to_scope.keys()

        found_classes = finding.find_classes(modules, classes)
        if only_use_explicit_bindings:
            implicit_class_bindings = []
        else:
            implicit_class_bindings = bindings.get_implicit_class_bindings(
                found_classes, get_arg_names_from_class_name)
        explicit_bindings = bindings.get_explicit_class_bindings(
            found_classes, get_arg_names_from_class_name)
        binder = bindings.Binder(explicit_bindings, known_scope_ids)
        if binding_specs is not None:
            binding_specs = list(binding_specs)
            while binding_specs:
                binding_spec = binding_specs.pop()
                try:
                    binding_spec.configure(binder.bind)
                    has_configure = True
                except NotImplementedError:
                    has_configure = False
                dependencies = binding_spec.dependencies()
                binding_specs.extend(dependencies)
                provider_bindings = bindings.get_provider_bindings(
                    binding_spec, get_arg_names_from_provider_fn_name)
                explicit_bindings.extend(provider_bindings)
                if not has_configure and not dependencies and not provider_bindings:
                    raise errors.EmptyBindingSpecError(binding_spec)

        binding_key_to_binding, collided_binding_key_to_bindings = (
            bindings.get_overall_binding_key_to_binding_maps(
                [implicit_class_bindings, explicit_bindings]))
        binding_mapping = bindings.BindingMapping(
            binding_key_to_binding, collided_binding_key_to_bindings)
    except errors.Error as e:
        if _SHORT_USER_VISIBLE_STACK_TRACE:
            raise e
        else:
            raise

    is_injectable_fn = {True: decorators.is_explicitly_injectable,
                        False: (lambda cls: True)}[only_use_explicit_bindings]
    obj_provider = object_providers.ObjectProvider(
        binding_mapping, bindable_scopes, allow_injecting_none)
    return ObjectGraph(
        obj_provider, injection_context_factory, is_injectable_fn)


class ObjectGraph(object):

    def __init__(self, obj_provider, injection_context_factory,
                 is_injectable_fn):
        self._obj_provider = obj_provider
        self._injection_context_factory = injection_context_factory
        self._is_injectable_fn = is_injectable_fn

    def provide(self, cls):
        if not self._is_injectable_fn(cls):
            raise errors.NonExplicitlyBoundClassError(cls)
        try:
            return self._obj_provider.provide_class(
                cls, self._injection_context_factory.new())
        except errors.Error as e:
            if _SHORT_USER_VISIBLE_STACK_TRACE:
                raise e
            else:
                raise

    # TODO(kurts): what's the use case for this, really?  Provider functions
    # are already injected by default.  Functional programming?
    def wrap(self, fn):
        # This has to return a function with a different signature (and can't
        # use @decorator) since otherwise python would require the caller to
        # pass in all positional args that have no defaults, instead of
        # letting those be injected if they're not passed in.
        arg_names, unused_varargs, unused_keywords, defaults = inspect.getargspec(fn)
        if defaults is None:
            defaults = []
        injectable_arg_names = arg_names[:(len(arg_names) - len(defaults))]
        @functools.wraps(fn)
        def WrappedFn(*pargs, **kwargs):
            injected_arg_names = [
                arg_name for index, arg_name in enumerate(injectable_arg_names)
                if index >= len(pargs) and arg_name not in kwargs]
            if injected_arg_names:
                kwargs = dict(kwargs)
                for arg_name in injected_arg_names:
                    kwargs[arg_name] = self._obj_provider.provide_from_binding_key(
                        binding_keys.new(arg_name),
                        self._injection_context_factory.new())
            return fn(*pargs, **kwargs)
        return WrappedFn
