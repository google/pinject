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
import types
import unittest

from pinject import bindings
from pinject import decorators
from pinject import errors
from pinject import object_graph
from pinject import scoping


class NewObjectGraphTest(unittest.TestCase):

    def test_can_create_object_graph_with_all_defaults(self):
        _ = object_graph.new_object_graph()

    def test_creates_object_graph_using_given_modules(self):
        obj_graph = object_graph.new_object_graph(modules=[errors])
        self.assertIsInstance(obj_graph.provide(errors.Error),
                              errors.Error)

    def test_creates_object_graph_using_given_classes(self):
        class SomeClass(object):
            pass
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass])
        self.assertIsInstance(obj_graph.provide(SomeClass), SomeClass)

    def test_creates_object_graph_using_given_binding_specs(self):
        class ClassWithFooInjected(object):
            def __init__(self, foo):
                pass
        class SomeClass(object):
            pass
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self, bind):
                bind('foo', to_class=SomeClass)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassWithFooInjected],
            binding_specs=[SomeBindingSpec()])
        self.assertIsInstance(obj_graph.provide(ClassWithFooInjected),
                              ClassWithFooInjected)

    def test_uses_binding_spec_dependencies(self):
        class BindingSpecOne(bindings.BindingSpec):
            def configure(self, bind):
                bind('foo', to_instance='a-foo')
        class BindingSpecTwo(bindings.BindingSpec):
            def configure(self, bind):
                bind('bar', to_instance='a-bar')
            def dependencies(self):
                return [BindingSpecOne()]
        class SomeClass(object):
            def __init__(self, foo, bar):
                self.foobar = '{0}{1}'.format(foo, bar)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], binding_specs=[BindingSpecTwo()])
        some_class = obj_graph.provide(SomeClass)
        self.assertEqual('a-fooa-bar', some_class.foobar)

    def test_allows_dag_binding_spec_dependencies(self):
        class CommonBindingSpec(bindings.BindingSpec):
            def configure(self, bind):
                bind('foo', to_instance='a-foo')
        class BindingSpecOne(bindings.BindingSpec):
            def dependencies(self):
                return [CommonBindingSpec()]
        class BindingSpecTwo(bindings.BindingSpec):
            def dependencies(self):
                return [CommonBindingSpec()]
        class RootBindingSpec(bindings.BindingSpec):
            def dependencies(self):
                return [BindingSpecOne(), BindingSpecTwo()]
        class SomeClass(object):
            def __init__(self, foo):
                self.foo = foo
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[RootBindingSpec()])
        some_class = obj_graph.provide(SomeClass)
        self.assertEqual('a-foo', some_class.foo)

    def test_allows_customizing_binding_spec_standard_method_names(self):
        class BindingSpecOne(bindings.BindingSpec):
            def Configure(self, bind):
                bind('foo', to_instance='a-foo')
            def Dependencies(self):
                return []
        class BindingSpecTwo(bindings.BindingSpec):
            def Configure(self, bind):
                pass
            def Dependencies(self):
                return [BindingSpecOne()]
        class SomeClass(object):
            def __init__(self, foo):
                self.foo = foo
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], binding_specs=[BindingSpecTwo()],
            configure_method_name='Configure',
            dependencies_method_name='Dependencies')
        some_class = obj_graph.provide(SomeClass)
        self.assertEqual('a-foo', some_class.foo)

    def test_customizing_binding_spec_method_names_allow_method_omission(self):
        class BindingSpecOne(bindings.BindingSpec):
            def Configure(self, bind):
                bind('foo', to_instance='a-foo')
            # Dependencies() omitted
        class BindingSpecTwo(bindings.BindingSpec):
            # Configure() omitted
            def Dependencies(self):
                return [BindingSpecOne()]
        class SomeClass(object):
            def __init__(self, foo):
                self.foo = foo
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], binding_specs=[BindingSpecTwo()],
            configure_method_name='Configure',
            dependencies_method_name='Dependencies')
        some_class = obj_graph.provide(SomeClass)
        self.assertEqual('a-foo', some_class.foo)

    def test_allows_binding_spec_with_only_provider_methods(self):
        class ClassWithFooInjected(object):
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(bindings.BindingSpec):
            def provide_foo(self):
                return 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassWithFooInjected],
            binding_specs=[SomeBindingSpec()],
            configure_method_name='Configure',
            dependencies_method_name='Dependencies')
        self.assertEqual('a-foo', obj_graph.provide(ClassWithFooInjected).foo)

    def test_raises_error_if_binding_spec_is_empty(self):
        class EmptyBindingSpec(bindings.BindingSpec):
            pass
        self.assertRaises(errors.EmptyBindingSpecError,
                          object_graph.new_object_graph, modules=None,
                          classes=None, binding_specs=[EmptyBindingSpec()])

    def test_creates_object_graph_using_given_scopes(self):
        class SomeClass(object):
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(bindings.BindingSpec):
            @decorators.provides(in_scope='foo-scope')
            def provide_foo(self):
                return object()
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[SomeBindingSpec()],
            id_to_scope={'foo-scope': scoping.SingletonScope()})
        some_class_one = obj_graph.provide(SomeClass)
        some_class_two = obj_graph.provide(SomeClass)
        self.assertIs(some_class_one.foo, some_class_two.foo)

    def test_raises_exception_if_modules_is_wrong_type(self):
        self.assertRaises(errors.WrongArgTypeError,
                          object_graph.new_object_graph, modules=42)

    def test_raises_exception_if_classes_is_wrong_type(self):
        self.assertRaises(errors.WrongArgTypeError,
                          object_graph.new_object_graph, classes=42)

    def test_raises_exception_if_binding_specs_is_wrong_type(self):
        self.assertRaises(errors.WrongArgTypeError,
                          object_graph.new_object_graph, binding_specs=42)

    def test_raises_exception_if_get_arg_names_from_class_name_is_wrong_type(self):
        self.assertRaises(errors.WrongArgTypeError,
                          object_graph.new_object_graph,
                          get_arg_names_from_class_name=42)

    def test_raises_exception_if_get_arg_names_from_provider_fn_name_is_wrong_type(self):
        self.assertRaises(errors.WrongArgTypeError,
                          object_graph.new_object_graph,
                          get_arg_names_from_provider_fn_name=42)

    def test_raises_exception_if_is_scope_usable_from_scope_is_wrong_type(self):
        self.assertRaises(errors.WrongArgTypeError,
                          object_graph.new_object_graph,
                          is_scope_usable_from_scope=42)

    def test_raises_exception_if_configure_method_has_no_expected_args(self):
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self):
                pass
        self.assertRaises(errors.ConfigureMethodMissingArgsError,
                          object_graph.new_object_graph,
                          modules=None, binding_specs=[SomeBindingSpec()])

    def test_raises_exception_if_required_binding_missing(self):
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self, require):
                require('foo')
        self.assertRaises(
            errors.MissingRequiredBindingError, object_graph.new_object_graph,
            modules=None, binding_specs=[SomeBindingSpec()])

    def test_raises_exception_if_required_binding_conflicts(self):
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self, require):
                require('foo')
        class Foo(object):
            pass
        class _Foo(object):
            pass
        self.assertRaises(errors.ConflictingRequiredBindingError,
                          object_graph.new_object_graph,
                          modules=None, classes=[Foo, _Foo],
                          binding_specs=[SomeBindingSpec()])


class VerifyTypeTest(unittest.TestCase):

    def test_verifies_correct_type_ok(self):
        object_graph._verify_type(types, types.ModuleType, 'unused')

    def test_raises_exception_if_incorrect_type(self):
        self.assertRaises(errors.WrongArgTypeError, object_graph._verify_type,
                          'not-a-module', types.ModuleType, 'an-arg-name')


class VerifyTypesTest(unittest.TestCase):

    def test_verifies_empty_sequence_ok(self):
        object_graph._verify_types([], types.ModuleType, 'unused')

    def test_verifies_correct_type_ok(self):
        object_graph._verify_types([types], types.ModuleType, 'unused')

    def test_raises_exception_if_not_sequence(self):
        self.assertRaises(errors.WrongArgTypeError, object_graph._verify_types,
                          42, types.ModuleType, 'an-arg-name')

    def test_raises_exception_if_element_is_incorrect_type(self):
        self.assertRaises(errors.WrongArgElementTypeError,
                          object_graph._verify_types,
                          ['not-a-module'], types.ModuleType, 'an-arg-name')


class VerifySubclassesTest(unittest.TestCase):

    def test_verifies_empty_sequence_ok(self):
        object_graph._verify_subclasses([], bindings.BindingSpec, 'unused')

    def test_verifies_correct_type_ok(self):
        class SomeBindingSpec(bindings.BindingSpec):
            pass
        object_graph._verify_subclasses(
            [SomeBindingSpec()], bindings.BindingSpec, 'unused')

    def test_raises_exception_if_not_sequence(self):
        self.assertRaises(errors.WrongArgTypeError,
                          object_graph._verify_subclasses,
                          42, bindings.BindingSpec, 'an-arg-name')

    def test_raises_exception_if_element_is_not_subclass(self):
        class NotBindingSpec(object):
            pass
        self.assertRaises(
            errors.WrongArgElementTypeError, object_graph._verify_subclasses,
            [NotBindingSpec()], bindings.BindingSpec, 'an-arg-name')


class VerifyCallableTest(unittest.TestCase):

    def test_verifies_callable_ok(self):
        object_graph._verify_callable(lambda: None, 'unused')

    def test_raises_exception_if_not_callable(self):
        self.assertRaises(errors.WrongArgTypeError,
                          object_graph._verify_callable, 42, 'an-arg-name')


class PareToPresentArgsTest(unittest.TestCase):

    def test_removes_only_args_not_present(self):
        def fn(self, present):
            pass
        self.assertEqual(
            {'present': 'a-present-value'},
            object_graph._pare_to_present_args(
                {'present': 'a-present-value', 'missing': 'a-missing-value'},
                fn))


class ObjectGraphProvideTest(unittest.TestCase):

    def test_can_provide_trivial_class(self):
        class ExampleClassWithInit(object):
            def __init__(self):
                pass
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ExampleClassWithInit])
        self.assertTrue(isinstance(obj_graph.provide(ExampleClassWithInit),
                                   ExampleClassWithInit))

    def test_can_provide_class_without_own_init(self):
        class ExampleClassWithoutInit(object):
            pass
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ExampleClassWithoutInit])
        self.assertIsInstance(obj_graph.provide(ExampleClassWithoutInit),
                              ExampleClassWithoutInit)

    def test_can_directly_provide_class_with_colliding_arg_name(self):
        class _CollidingExampleClass(object):
            pass
        class CollidingExampleClass(object):
            pass
        obj_graph = object_graph.new_object_graph(
            modules=None,
            classes=[_CollidingExampleClass, CollidingExampleClass])
        self.assertIsInstance(obj_graph.provide(CollidingExampleClass),
                              CollidingExampleClass)

    def test_can_provide_class_that_itself_requires_injection(self):
        class ClassOne(object):
            def __init__(self, class_two):
                pass
        class ClassTwo(object):
            pass
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne, ClassTwo])
        self.assertIsInstance(obj_graph.provide(ClassOne), ClassOne)

    def test_raises_error_if_arg_is_ambiguously_injectable(self):
        class _CollidingExampleClass(object):
            pass
        class CollidingExampleClass(object):
            pass
        class AmbiguousParamClass(object):
            def __init__(self, colliding_example_class):
                pass
        obj_graph = object_graph.new_object_graph(
            modules=None,
            classes=[_CollidingExampleClass, CollidingExampleClass,
                     AmbiguousParamClass])
        self.assertRaises(errors.AmbiguousArgNameError,
                          obj_graph.provide, AmbiguousParamClass)

    def test_raises_error_if_arg_refers_to_no_known_class(self):
        class UnknownParamClass(object):
            def __init__(self, unknown_class):
                pass
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[UnknownParamClass])
        self.assertRaises(errors.NothingInjectableForArgError,
                          obj_graph.provide, UnknownParamClass)

    def test_raises_error_if_injection_cycle(self):
        class ClassOne(object):
            def __init__(self, class_two):
                pass
        class ClassTwo(object):
            def __init__(self, class_one):
                pass
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne, ClassTwo])
        self.assertRaises(errors.CyclicInjectionError,
                          obj_graph.provide, ClassOne)

    def test_injects_args_of_provider_fns(self):
        class ClassOne(object):
            pass
        class SomeBindingSpec(bindings.BindingSpec):
            def provide_foo(self, class_one):
                class_one.three = 3
                return class_one
        class ClassTwo(object):
            def __init__(self, foo):
                self.foo = foo
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne, ClassTwo],
            binding_specs=[SomeBindingSpec()])
        class_two = obj_graph.provide(ClassTwo)
        self.assertEqual(3, class_two.foo.three)

    def test_injects_provider_fn_if_so_named(self):
        class ClassOne(object):
            def __init__(self):
                self.forty_two = 42
        class ClassTwo(object):
            def __init__(self, provide_class_one):
                self.provide_class_one = provide_class_one
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne, ClassTwo])
        class_two = obj_graph.provide(ClassTwo)
        self.assertEqual(42, class_two.provide_class_one().forty_two)

    def test_can_provide_arg_with_annotation(self):
        class ClassOne(object):
            @decorators.annotate_arg('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self, bind):
                bind('foo', annotated_with='an-annotation', to_instance='a-foo')
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()])
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo', class_one.foo)

    def test_all_parts_of_provide_decorator_are_used(self):
        class SomeClass(object):
            @decorators.annotate_arg('foo', 'specific-foo')
            @decorators.annotate_arg('bar', 'specific-bar')
            def __init__(self, foo, bar):
                self.foo = foo
                self.bar = bar
        class SomeBindingSpec(bindings.BindingSpec):
            @decorators.provides('foo', annotated_with='specific-foo',
                                 in_scope=scoping.SINGLETON)
            def provide_foo(self):
                return object()
            @decorators.provides('bar', annotated_with='specific-bar',
                                 in_scope=scoping.PROTOTYPE)
            def provide_bar(self):
                return object()
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[SomeBindingSpec()])
        class_one = obj_graph.provide(SomeClass)
        class_two = obj_graph.provide(SomeClass)
        self.assertIs(class_one.foo, class_two.foo)
        self.assertIsNot(class_one.bar, class_two.bar)

    def test_singleton_classes_are_singletons_across_arg_names(self):
        class InjectedClass(object):
            pass
        class SomeClass(object):
            def __init__(self, foo, bar):
                self.foo = foo
                self.bar = bar
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self, bind):
                bind('foo', to_class=InjectedClass, in_scope=scoping.SINGLETON)
                bind('bar', to_class=InjectedClass, in_scope=scoping.SINGLETON)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[SomeBindingSpec()])
        some_class = obj_graph.provide(SomeClass)
        self.assertIs(some_class.foo, some_class.bar)

    def test_raises_error_if_only_binding_has_different_annotation(self):
        class ClassOne(object):
            @decorators.annotate_arg('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self, bind):
                bind('foo', annotated_with='other-annotation',
                     to_instance='a-foo')
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()])
        self.assertRaises(errors.NothingInjectableForArgError,
                          obj_graph.provide, ClassOne)

    def test_raises_error_if_only_binding_has_no_annotation(self):
        class ClassOne(object):
            @decorators.annotate_arg('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self, bind):
                bind('foo', to_instance='a-foo')
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()])
        self.assertRaises(errors.NothingInjectableForArgError,
                          obj_graph.provide, ClassOne)

    def test_can_provide_using_provider_fn(self):
        class ClassOne(object):
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(bindings.BindingSpec):
            def provide_foo(self):
                return 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()])
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo', class_one.foo)

    def test_provider_fn_overrides_implicit_class_binding(self):
        class ClassOne(object):
            def __init__(self, foo):
                self.foo = foo
        class Foo(object):
            pass
        class SomeBindingSpec(bindings.BindingSpec):
            def provide_foo(self):
                return 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne, Foo],
            binding_specs=[SomeBindingSpec()])
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo', class_one.foo)

    def test_autoinjects_args_of_provider_fn(self):
        class ClassOne(object):
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(bindings.BindingSpec):
            def provide_foo(self, bar):
                return 'a-foo with {0}'.format(bar)
            def provide_bar(self):
                return 'a-bar'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()])
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo with a-bar', class_one.foo)

    def test_can_use_annotate_arg_with_provides(self):
        class ClassOne(object):
            @decorators.annotate_arg('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(bindings.BindingSpec):
            @decorators.provides(annotated_with='an-annotation')
            @decorators.annotate_arg('bar', 'another-annotation')
            def provide_foo(self, bar):
                return 'a-foo with {0}'.format(bar)
            @decorators.provides(annotated_with='another-annotation')
            def provide_bar(self):
                return 'a-bar'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()])
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo with a-bar', class_one.foo)

    def test_injectable_decorated_class_can_be_directly_provided(self):
        class SomeClass(object):
            @decorators.injectable
            def __init__(self):
                self.foo = 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], only_use_explicit_bindings=True)
        class_one = obj_graph.provide(SomeClass)
        self.assertEqual('a-foo', class_one.foo)

    def test_inject_decorated_class_can_be_directly_provided(self):
        class SomeClass(object):
            @decorators.inject()
            def __init__(self):
                self.foo = 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], only_use_explicit_bindings=True)
        class_one = obj_graph.provide(SomeClass)
        self.assertEqual('a-foo', class_one.foo)

    def test_non_explicitly_injectable_class_cannot_be_directly_provided(self):
        class SomeClass(object):
            def __init__(self):
                self.foo = 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], only_use_explicit_bindings=True)
        self.assertRaises(
            errors.NonExplicitlyBoundClassError, obj_graph.provide, SomeClass)

    def test_injectable_decorated_class_is_explicitly_bound(self):
        class ClassOne(object):
            @decorators.injectable
            def __init__(self, class_two):
                self.class_two = class_two
        class ClassTwo(object):
            @decorators.injectable
            def __init__(self):
                self.foo = 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne, ClassTwo],
            only_use_explicit_bindings=True)
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo', class_one.class_two.foo)

    def test_inject_decorated_class_is_explicitly_bound(self):
        class ClassOne(object):
            @decorators.inject()
            def __init__(self, class_two):
                self.class_two = class_two
        class ClassTwo(object):
            @decorators.inject()
            def __init__(self):
                self.foo = 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne, ClassTwo],
            only_use_explicit_bindings=True)
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo', class_one.class_two.foo)

    def test_explicit_binding_is_explicitly_bound(self):
        class ClassOne(object):
            @decorators.injectable
            def __init__(self, class_two):
                self.class_two = class_two
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self, bind):
                bind('class_two', to_instance='a-class-two')
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()],
            only_use_explicit_bindings=True)
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-class-two', class_one.class_two)

    def test_provider_fn_is_explicitly_bound(self):
        class ClassOne(object):
            @decorators.injectable
            def __init__(self, class_two):
                self.class_two = class_two
        class SomeBindingSpec(bindings.BindingSpec):
            def provide_class_two(self):
                return 'a-class-two'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()],
            only_use_explicit_bindings=True)
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-class-two', class_one.class_two)

    def test_non_bound_non_decorated_class_is_not_explicitly_bound(self):
        class ClassOne(object):
            @decorators.injectable
            def __init__(self, class_two):
                self.class_two = class_two
        class ClassTwo(object):
            def __init__(self):
                self.foo = 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne, ClassTwo],
            only_use_explicit_bindings=True)
        self.assertRaises(errors.NothingInjectableForArgError,
                          obj_graph.provide, ClassOne)

    def test_can_pass_direct_args_to_provider_fn(self):
        class SomeBindingSpec(bindings.BindingSpec):
            @decorators.inject(['injected'])
            def provide_foo(self, passed_directly_parg, passed_directly_kwarg,
                            injected):
                return passed_directly_parg + passed_directly_kwarg + injected
            def configure(self, bind):
                bind('injected', to_instance=2)
        class SomeClass(object):
            def __init__(self, provide_foo):
                self.foo = provide_foo(30, passed_directly_kwarg=10)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[SomeBindingSpec()])
        some_class = obj_graph.provide(SomeClass)
        self.assertEqual(42, some_class.foo)

    def test_can_pass_kwargs_to_provider_fn(self):
        class SomeBindingSpec(bindings.BindingSpec):
            def provide_foo(self, injected, **kwargs):
                return injected + kwargs['kwarg']
            def configure(self, bind):
                bind('injected', to_instance=2)
        class SomeClass(object):
            def __init__(self, provide_foo):
                self.foo = provide_foo(kwarg=40)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[SomeBindingSpec()])
        some_class = obj_graph.provide(SomeClass)
        self.assertEqual(42, some_class.foo)

    def test_cannot_pass_injected_args_to_provider_fn(self):
        class SomeBindingSpec(bindings.BindingSpec):
            def provide_foo(self, injected):
                return 'unused'
            def configure(self, bind):
                bind('injected', to_instance=2)
        class SomeClass(object):
            def __init__(self, provide_foo):
                self.foo = provide_foo(injected=40)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[SomeBindingSpec()])
        self.assertRaises(errors.DirectlyPassingInjectedArgsError,
                          obj_graph.provide, SomeClass)

    def test_cannot_pass_non_existent_args_to_provider_fn(self):
        class SomeBindingSpec(bindings.BindingSpec):
            @decorators.inject(['injected'])
            def provide_foo(self, injected):
                pass
            def configure(self, bind):
                bind('injected', to_instance=2)
        class SomeClass(object):
            def __init__(self, provide_foo):
                self.foo = provide_foo(non_existent=40)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[SomeBindingSpec()])
        self.assertRaises(TypeError, obj_graph.provide, SomeClass)

    def test_inject_decorator_works_on_initializer(self):
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self, bind):
                bind('injected', to_instance=2)
        class Foo(object):
            @decorators.inject(['injected'])
            def __init__(self, passed_directly_parg, passed_directly_kwarg,
                         injected):
                self.forty_two = (passed_directly_parg +
                                  passed_directly_kwarg + injected)
        class SomeClass(object):
            def __init__(self, provide_foo):
                self.foo = provide_foo(30, passed_directly_kwarg=10)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass, Foo],
            binding_specs=[SomeBindingSpec()])
        some_class = obj_graph.provide(SomeClass)
        self.assertEqual(42, some_class.foo.forty_two)

    def test_cannot_pass_non_existent_args_to_provider_fn_for_instance(self):
        class SomeBindingSpec(bindings.BindingSpec):
            def configure(self, bind):
                bind('foo', to_instance='a-foo')
        class SomeClass(object):
            def __init__(self, provide_foo):
                self.foo = provide_foo(non_existent=42)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[SomeBindingSpec()])
        self.assertRaises(TypeError, obj_graph.provide, SomeClass)

    def test_cannot_directly_inject_something_expecting_direct_args(self):
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
        self.assertRaises(errors.OnlyInstantiableViaProviderFunctionError,
                          obj_graph.provide, SomeClass)

    def test_can_inject_none_when_allowing_injecting_none(self):
        class SomeClass(object):
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(bindings.BindingSpec):
            def provide_foo(self):
                return None
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[SomeBindingSpec()], allow_injecting_none=True)
        some_class = obj_graph.provide(SomeClass)
        self.assertIsNone(some_class.foo)

    def test_cannot_inject_none_when_disallowing_injecting_none(self):
        class SomeClass(object):
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(bindings.BindingSpec):
            def provide_foo(self):
                return None
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass],
            binding_specs=[SomeBindingSpec()], allow_injecting_none=False)
        self.assertRaises(errors.InjectingNoneDisallowedError,
                          obj_graph.provide, SomeClass)

    def test_raises_exception_if_trying_to_provide_nonclass(self):
        class SomeClass(object):
            pass
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass])
        self.assertRaises(errors.WrongArgTypeError, obj_graph.provide, 42)
