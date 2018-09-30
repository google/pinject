#!/usr/bin/python

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
import sys
import traceback
import types

from pinject import bindings
from pinject import decorators
from pinject import errors
from pinject import initializers
from pinject import object_graph
from pinject import scoping


def _print_raised_exception(exc, fn, *pargs, **kwargs):
    try:
        fn(*pargs, **kwargs)
        raise Exception('failed to raise')
    except exc:
        traceback.print_exc()


def print_ambiguous_arg_name_error():
    class SomeClass(object):
        def __init__(self, foo):
            pass
    class Foo(object):
        pass
    class _Foo(object):
        pass
    obj_graph = object_graph.new_object_graph(
        modules=None, classes=[SomeClass, Foo, _Foo])
    _print_raised_exception(errors.AmbiguousArgNameError,
                            obj_graph.provide, SomeClass)


def print_bad_dependency_scope_error():
    class Foo(object):
        pass
    class Bar(object):
        def __init__(self, foo):
            pass
    obj_graph = object_graph.new_object_graph(
        modules=None, classes=[Foo, Bar],
        is_scope_usable_from_scope=lambda _1, _2: False)
    _print_raised_exception(errors.BadDependencyScopeError,
                            obj_graph.provide, Bar)


def print_configure_method_missing_args_error():
    class SomeBindingSpec(bindings.BindingSpec):
        def configure(self):
            pass
    _print_raised_exception(
        errors.ConfigureMethodMissingArgsError, object_graph.new_object_graph,
        modules=None, binding_specs=[SomeBindingSpec()])


def print_conflicting_explicit_bindings_error():
    class SomeBindingSpec(bindings.BindingSpec):
        def configure(self, bind):
            bind('foo', to_instance=1)
            bind('foo', to_instance=2)
    _print_raised_exception(
        errors.ConflictingExplicitBindingsError, object_graph.new_object_graph,
        modules=None, binding_specs=[SomeBindingSpec()])


def print_conflicting_required_binding_error():
    class SomeBindingSpec(bindings.BindingSpec):
        def configure(self, require):
            require('foo')
    class Foo(object):
        pass
    class _Foo(object):
        pass
    _print_raised_exception(
        errors.ConflictingRequiredBindingError, object_graph.new_object_graph,
        modules=None, classes=[Foo, _Foo], binding_specs=[SomeBindingSpec()])


def print_cyclic_injection_error():
    class ClassOne(object):
        def __init__(self, class_two):
            pass
    class ClassTwo(object):
        def __init__(self, class_three):
            pass
    class ClassThree(object):
        def __init__(self, class_one):
            pass
    obj_graph = object_graph.new_object_graph(
        modules=None, classes=[ClassOne, ClassTwo, ClassThree])
    _print_raised_exception(errors.CyclicInjectionError,
                            obj_graph.provide, ClassOne)
    # TODO(kurts): make the file:line not get printed twice on each line.


def print_decorator_applied_to_non_init_error():
    def apply_injectable_to_random_fn():
        @initializers.copy_args_to_internal_fields
        def random_fn():
            pass
    _print_raised_exception(errors.DecoratorAppliedToNonInitError,
                            apply_injectable_to_random_fn)


def print_directly_passing_injected_args_error():
    class SomeBindingSpec(bindings.BindingSpec):
        def provide_foo(self, injected):
            return 'unused'
        def configure(self, bind):
            bind('injected', to_instance=2)
    class SomeClass(object):
        def __init__(self, provide_foo):
            provide_foo(injected=40)
    obj_graph = object_graph.new_object_graph(
        modules=None, classes=[SomeClass],
        binding_specs=[SomeBindingSpec()])
    _print_raised_exception(errors.DirectlyPassingInjectedArgsError,
                            obj_graph.provide, SomeClass)
    # TODO(kurts): make the error display the line number where the provider
    # was called, not the line number of the top of the function in which the
    # provider is called.


def print_duplicate_decorator_error():
    def do_bad_inject():
        @decorators.inject(['foo'])
        @decorators.inject(['foo'])
        def some_function(foo, bar):
            pass
    _print_raised_exception(errors.DuplicateDecoratorError, do_bad_inject)


def print_empty_binding_spec_error():
    class EmptyBindingSpec(bindings.BindingSpec):
        pass
    _print_raised_exception(
        errors.EmptyBindingSpecError, object_graph.new_object_graph,
        modules=None, binding_specs=[EmptyBindingSpec()])


def print_empty_provides_decorator_error():
    def define_binding_spec():
        class SomeBindingSpec(bindings.BindingSpec):
            @decorators.provides()
            def provide_foo():
                pass
    _print_raised_exception(
        errors.EmptyProvidesDecoratorError, define_binding_spec)


def print_empty_sequence_arg_error():
    def do_bad_inject():
        @decorators.inject(arg_names=[])
        def some_function(foo, bar):
            pass
    _print_raised_exception(errors.EmptySequenceArgError, do_bad_inject)


def print_injecting_none_disallowed_error():
    class SomeClass(object):
        def __init__(self, foo):
            self.foo = foo
    class SomeBindingSpec(bindings.BindingSpec):
        def provide_foo(self):
            return None
    obj_graph = object_graph.new_object_graph(
        modules=None, classes=[SomeClass], binding_specs=[SomeBindingSpec()],
        allow_injecting_none=False)
    _print_raised_exception(errors.InjectingNoneDisallowedError,
                            obj_graph.provide, SomeClass)


def print_invalid_binding_target_error():
    class SomeBindingSpec(bindings.BindingSpec):
        def configure(self, bind):
            bind('foo', to_class='not-a-class')
    _print_raised_exception(
        errors.InvalidBindingTargetError, object_graph.new_object_graph,
        modules=None, binding_specs=[SomeBindingSpec()])


def print_missing_required_binding_error():
    class SomeBindingSpec(bindings.BindingSpec):
        def configure(self, require):
            require('foo')
    _print_raised_exception(
        errors.MissingRequiredBindingError, object_graph.new_object_graph,
        modules=None, binding_specs=[SomeBindingSpec()])


def print_multiple_annotations_for_same_arg_error():
    def define_some_class():
        class SomeClass(object):
            @decorators.annotate_arg('foo', 'an-annotation')
            @decorators.annotate_arg('foo', 'an-annotation')
            def __init__(self, foo):
                return foo
    _print_raised_exception(
        errors.MultipleAnnotationsForSameArgError, define_some_class)


def print_multiple_binding_target_args_error():
    class SomeClass(object):
        pass
    class SomeBindingSpec(bindings.BindingSpec):
        def configure(self, bind):
            bind('foo', to_class=SomeClass, to_instance=SomeClass())
    _print_raised_exception(
        errors.MultipleBindingTargetArgsError, object_graph.new_object_graph,
        modules=None, binding_specs=[SomeBindingSpec()])


def print_no_binding_target_args_error():
    class SomeBindingSpec(bindings.BindingSpec):
        def configure(self, bind):
            bind('foo')
    _print_raised_exception(
        errors.NoBindingTargetArgsError, object_graph.new_object_graph,
        modules=None, binding_specs=[SomeBindingSpec()])


def print_no_remaining_args_to_inject_error():
    def do_bad_inject():
        @decorators.inject(all_except=['foo', 'bar'])
        def some_function(foo, bar):
            pass
    _print_raised_exception(errors.NoRemainingArgsToInjectError, do_bad_inject)


def print_no_such_arg_error():
    def do_bad_inject():
        @decorators.inject(arg_names=['bar'])
        def some_function(foo):
            pass
    _print_raised_exception(errors.NoSuchArgError, do_bad_inject)


def print_no_such_arg_to_inject_error():
    def do_bad_annotate_arg():
        @decorators.annotate_arg('foo', 'an-annotation')
        def some_function(bar):
            return bar
    _print_raised_exception(
        errors.NoSuchArgToInjectError, do_bad_annotate_arg)


def print_non_explicitly_bound_class_error():
    class ImplicitlyBoundClass(object):
        pass
    obj_graph = object_graph.new_object_graph(
        modules=None, classes=[ImplicitlyBoundClass],
        only_use_explicit_bindings=True)
    _print_raised_exception(
        errors.NonExplicitlyBoundClassError, obj_graph.provide, ImplicitlyBoundClass)


def print_nothing_injectable_for_arg_error():
    class UnknownParamClass(object):
        def __init__(self, unknown_class):
            pass
    obj_graph = object_graph.new_object_graph(
        modules=None, classes=[UnknownParamClass])
    _print_raised_exception(errors.NothingInjectableForArgError,
                            obj_graph.provide, UnknownParamClass)


def print_only_instantiable_via_provider_function_error():
    class SomeBindingSpec(bindings.BindingSpec):
        @decorators.inject(['injected'])
        def provide_foo(self, passed_directly, injected):
            return passed_directly + injected
        def configure(self, bind):
            bind('injected', to_instance=2)
    class SomeClass(object):
        def __init__(self, foo):
            self.foo = foo
    obj_graph = object_graph.new_object_graph(
        modules=None, classes=[SomeClass],
        binding_specs=[SomeBindingSpec()])
    _print_raised_exception(errors.OnlyInstantiableViaProviderFunctionError,
                            obj_graph.provide, SomeClass)


def print_overriding_default_scope_error():
    _print_raised_exception(
        errors.OverridingDefaultScopeError, object_graph.new_object_graph,
        modules=None, id_to_scope={scoping.DEFAULT_SCOPE: 'a-scope'})


def print_pargs_disallowed_when_copying_args_error():
    def do_bad_initializer():
        class SomeClass(object):
            @initializers.copy_args_to_internal_fields
            def __init__(self, *pargs):
                pass
    _print_raised_exception(
        errors.PargsDisallowedWhenCopyingArgsError, do_bad_initializer)


def print_too_many_args_to_inject_decorator_error():
    def do_bad_inject():
        @decorators.inject(['foo'], all_except=['bar'])
        def some_function(foo, bar):
            pass
    _print_raised_exception(errors.TooManyArgsToInjectDecoratorError,
                            do_bad_inject)


def print_unknown_scope_error():
    class SomeBindingSpec(bindings.BindingSpec):
        def configure(self, bind):
            bind('foo', to_instance='a-foo', in_scope='unknown-scope')
    _print_raised_exception(
        errors.UnknownScopeError, object_graph.new_object_graph,
        modules=None, binding_specs=[SomeBindingSpec()])


def print_wrong_arg_element_type_error():
    _print_raised_exception(
        errors.WrongArgElementTypeError, object_graph.new_object_graph,
        modules=[42])


def print_wrong_arg_type_error():
    _print_raised_exception(
        errors.WrongArgTypeError, object_graph.new_object_graph, modules=42)


all_print_method_pairs = inspect.getmembers(
    sys.modules[__name__],
    lambda x: (type(x) == types.FunctionType and
               x.__name__.startswith('print_') and
               x.__name__.endswith('_error')))
all_print_method_pairs.sort(key=lambda x: x[0])
all_print_methods = [value for name, value in all_print_method_pairs]
for print_method in all_print_methods:
    print '#' * 78
    print_method()
print '#' * 78
