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
import functools
import inspect
import types

from . import arg_binding_keys
from . import bindings
from . import decorators
from . import errors
from . import finding
from . import injection_contexts
from . import locations
from . import object_providers
from . import providing
from . import required_bindings as required_bindings_lib
from . import scoping


def new_object_graph(
        modules=finding.ALL_IMPORTED_MODULES, classes=None, binding_specs=None,
        only_use_explicit_bindings=False, allow_injecting_none=False,
        configure_method_name='configure',
        dependencies_method_name='dependencies',
        get_arg_names_from_class_name=(
            bindings.default_get_arg_names_from_class_name),
        get_arg_names_from_provider_fn_name=(
            providing.default_get_arg_names_from_provider_fn_name),
        id_to_scope=None, is_scope_usable_from_scope=lambda _1, _2: True,
        use_short_stack_traces=True):
    """Creates a new object graph.

    Args:
      modules: the modules in which to search for classes for which to create
          implicit bindings; if None, then no modules; by default, all
          modules imported at the time of calling this method
      classes: the classes for which to create implicit bindings; if None (the
          default), then no classes
      binding_specs: the BindingSpec subclasses to get bindings and provider
          methods from; if None (the default), then no binding specs
      only_use_explicit_bindings: whether to use only explicit bindings (i.e.,
          created by binding specs or @pinject.injectable, etc.)
      allow_injecting_none: whether to allow a provider method to provide None
      configure_method_name: the name of binding specs' configure method
      dependencies_method_name: the name of binding specs' dependencies method
      get_arg_names_from_class_name: a function mapping a class name to a
          sequence of the arg names to which those classes should be
          implicitly bound (if any)
      get_arg_names_from_provider_fn_name: a function mapping a provider
          method name to a sequence of the arg names for which that method is
          a provider (if any)
      id_to_scope: a map from scope ID to the concrete Scope implementation
          instance for that scope
      is_scope_usable_from_scope: a function taking two scope IDs and
          returning whether an object in the first scope can be injected into
          an object from the second scope; by default, injection is allowed
          from any scope into any other scope
      use_short_stack_traces: whether to shorten the stack traces for
          exceptions that Pinject raises, so that they don't contain the
          innards of Pinject
    Returns:
      an ObjectGraph
    Raises:
      Error: the object graph is not creatable as specified

    """
    try:
        if modules is not None and modules is not finding.ALL_IMPORTED_MODULES:
            _verify_types(modules, types.ModuleType, 'modules')
        if classes is not None:
            _verify_types(classes, types.TypeType, 'classes')
        if binding_specs is not None:
            _verify_subclasses(
                binding_specs, bindings.BindingSpec, 'binding_specs')
        if get_arg_names_from_class_name is not None:
            _verify_callable(get_arg_names_from_class_name,
                             'get_arg_names_from_class_name')
        if get_arg_names_from_provider_fn_name is not None:
            _verify_callable(get_arg_names_from_provider_fn_name,
                             'get_arg_names_from_provider_fn_name')
        if is_scope_usable_from_scope is not None:
            _verify_callable(is_scope_usable_from_scope,
                             'is_scope_usable_from_scope')
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
        required_bindings = required_bindings_lib.RequiredBindings()
        if binding_specs is not None:
            binding_specs = list(binding_specs)
            processed_binding_specs = set()
            while binding_specs:
                binding_spec = binding_specs.pop()
                if binding_spec in processed_binding_specs:
                    continue
                processed_binding_specs.add(binding_spec)
                all_kwargs = {'bind': binder.bind,
                              'require': required_bindings.require}
                has_configure = hasattr(binding_spec, configure_method_name)
                if has_configure:
                    configure_method = getattr(binding_spec, configure_method_name)
                    configure_kwargs = _pare_to_present_args(
                        all_kwargs, configure_method)
                    if not configure_kwargs:
                        raise errors.ConfigureMethodMissingArgsError(
                            configure_method, all_kwargs.keys())
                    try:
                        configure_method(**configure_kwargs)
                    except NotImplementedError:
                        has_configure = False
                dependencies = None
                if hasattr(binding_spec, dependencies_method_name):
                    dependencies_method = (
                        getattr(binding_spec, dependencies_method_name))
                    dependencies = dependencies_method()
                    binding_specs.extend(dependencies)
                provider_bindings = bindings.get_provider_bindings(
                    binding_spec, known_scope_ids,
                    get_arg_names_from_provider_fn_name)
                explicit_bindings.extend(provider_bindings)
                if (not has_configure and
                    not dependencies and
                    not provider_bindings):
                    raise errors.EmptyBindingSpecError(binding_spec)
        binding_key_to_binding, collided_binding_key_to_bindings = (
            bindings.get_overall_binding_key_to_binding_maps(
                [implicit_class_bindings, explicit_bindings]))
        binding_mapping = bindings.BindingMapping(
            binding_key_to_binding, collided_binding_key_to_bindings)
        binding_mapping.verify_requirements(required_bindings.get())
    except errors.Error as e:
        if use_short_stack_traces:
            raise e
        else:
            raise

    is_injectable_fn = {True: decorators.is_explicitly_injectable,
                        False: (lambda cls: True)}[only_use_explicit_bindings]
    obj_provider = object_providers.ObjectProvider(
        binding_mapping, bindable_scopes, allow_injecting_none)
    return ObjectGraph(
        obj_provider, injection_context_factory, is_injectable_fn,
        use_short_stack_traces)


def _verify_type(elt, required_type, arg_name):
    if type(elt) != required_type:
        raise errors.WrongArgTypeError(
            arg_name, required_type.__name__, type(elt).__name__)


def _verify_types(seq, required_type, arg_name):
    if not isinstance(seq, collections.Sequence):
        raise errors.WrongArgTypeError(
            arg_name, 'sequence (of {0})'.format(required_type.__name__),
            type(seq).__name__)
    for idx, elt in enumerate(seq):
        if type(elt) != required_type:
            raise errors.WrongArgElementTypeError(
                arg_name, idx, required_type.__name__, type(elt).__name__)


def _verify_subclasses(seq, required_superclass, arg_name):
    if not isinstance(seq, collections.Sequence):
        raise errors.WrongArgTypeError(
            arg_name,
            'sequence (of subclasses of {0})'.format(
                required_superclass.__name__),
            type(seq).__name__)
    for idx, elt in enumerate(seq):
        if not isinstance(elt, required_superclass):
            raise errors.WrongArgElementTypeError(
                arg_name, idx,
                'subclass of {0}'.format(required_superclass.__name__),
                type(elt).__name__)


def _verify_callable(fn, arg_name):
    if not callable(fn):
        raise errors.WrongArgTypeError(arg_name, 'callable', type(fn).__name__)


def _pare_to_present_args(kwargs, fn):
    arg_names, _, _, _ = inspect.getargspec(fn)
    return {arg: value for arg, value in kwargs.iteritems() if arg in arg_names}


class ObjectGraph(object):
    """A graph of objects instantiable with dependency injection."""

    def __init__(self, obj_provider, injection_context_factory,
                 is_injectable_fn, use_short_stack_traces):
        self._obj_provider = obj_provider
        self._injection_context_factory = injection_context_factory
        self._is_injectable_fn = is_injectable_fn
        self._use_short_stack_traces = use_short_stack_traces

    def provide(self, cls):
        """Provides an instance of the given class.

        Args:
          cls: a class (not an instance)
        Returns:
          an instance of cls
        Raises:
          Error: an instance of cls is not providable
        """
        _verify_type(cls, types.TypeType, 'cls')
        if not self._is_injectable_fn(cls):
            provide_loc = locations.get_back_frame_loc()
            raise errors.NonExplicitlyBoundClassError(provide_loc, cls)
        try:
            return self._obj_provider.provide_class(
                cls, self._injection_context_factory.new(cls.__init__),
                direct_init_pargs=[], direct_init_kwargs={})
        except errors.Error as e:
            if self._use_short_stack_traces:
                raise e
            else:
                raise
