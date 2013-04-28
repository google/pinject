
import inspect
import unittest

import binding
import errors
import object_graph
import scoping
import wrapping


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
        obj_graph = object_graph.new_object_graph(modules=None, classes=[SomeClass])
        self.assertIsInstance(obj_graph.provide(SomeClass), SomeClass)

    def test_creates_object_graph_using_given_binding_specs(self):
        class ClassWithFooInjected(object):
            def __init__(self, foo):
                pass
        class SomeClass(object):
            pass
        class SomeBindingSpec(binding.BindingSpec):
            def configure(self, bind):
                bind('foo', to_class=SomeClass)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassWithFooInjected],
            binding_specs=[SomeBindingSpec()])
        self.assertIsInstance(obj_graph.provide(ClassWithFooInjected),
                              ClassWithFooInjected)

    def test_uses_binding_spec_dependencies(self):
        class BindingSpecOne(binding.BindingSpec):
            def configure(self, bind):
                bind('foo', to_instance='a-foo')
        class BindingSpecTwo(binding.BindingSpec):
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

    def test_raises_error_if_binding_spec_is_empty(self):
        class EmptyBindingSpec(binding.BindingSpec):
            pass
        self.assertRaises(errors.EmptyBindingSpecError,
                          object_graph.new_object_graph, modules=None, classes=None,
                          binding_specs=[EmptyBindingSpec()])

    def test_creates_object_graph_using_given_scopes(self):
        class SomeClass(object):
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(binding.BindingSpec):
            @wrapping.in_scope('foo-scope')
            def provide_foo(self):
                return object()
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], binding_specs=[SomeBindingSpec()],
            id_to_scope={'foo-scope': scoping.SingletonScope()})
        some_class_one = obj_graph.provide(SomeClass)
        some_class_two = obj_graph.provide(SomeClass)
        self.assertIs(some_class_one.foo, some_class_two.foo)


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
        class SomeBindingSpec(binding.BindingSpec):
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

    def test_can_provide_arg_with_annotation(self):
        class ClassOne(object):
            @wrapping.annotate_arg('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(binding.BindingSpec):
            def configure(self, bind):
                bind('foo', annotated_with='an-annotation', to_instance='a-foo')
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()])
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo', class_one.foo)

    def test_annotated_arg_is_provided_in_correct_scope(self):
        class SomeClass(object):
            @wrapping.annotate_arg('foo', 'specific-foo')
            @wrapping.annotate_arg('bar', 'specific-bar')
            def __init__(self, foo, bar):
                self.foo = foo
                self.bar = bar
        class SomeBindingSpec(binding.BindingSpec):
            @wrapping.annotated_with('specific-foo')
            @wrapping.in_scope(scoping.SINGLETON)
            def provide_foo(self):
                return object()
            @wrapping.annotated_with('specific-bar')
            @wrapping.in_scope(scoping.PROTOTYPE)
            def provide_bar(self):
                return object()
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], binding_specs=[SomeBindingSpec()])
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
        class SomeBindingSpec(binding.BindingSpec):
            def configure(self, bind):
                bind('foo', to_class=InjectedClass, in_scope=scoping.SINGLETON)
                bind('bar', to_class=InjectedClass, in_scope=scoping.SINGLETON)
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], binding_specs=[SomeBindingSpec()])
        some_class = obj_graph.provide(SomeClass)
        self.assertIs(some_class.foo, some_class.bar)

    def test_raises_error_if_only_binding_has_different_annotation(self):
        class ClassOne(object):
            @wrapping.annotate_arg('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(binding.BindingSpec):
            def configure(self, bind):
                bind('foo', annotated_with='other-annotation', to_instance='a-foo')
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()])
        self.assertRaises(errors.NothingInjectableForArgError,
                          obj_graph.provide, ClassOne)

    def test_raises_error_if_only_binding_has_no_annotation(self):
        class ClassOne(object):
            @wrapping.annotate_arg('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(binding.BindingSpec):
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
        class SomeBindingSpec(binding.BindingSpec):
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
        class SomeBindingSpec(binding.BindingSpec):
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
        class SomeBindingSpec(binding.BindingSpec):
            def provide_foo(self, bar):
                return 'a-foo with {0}'.format(bar)
            def provide_bar(self):
                return 'a-bar'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()])
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo with a-bar', class_one.foo)

    def test_can_use_annotate_with_provides(self):
        class ClassOne(object):
            @wrapping.annotate_arg('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(binding.BindingSpec):
            @wrapping.annotated_with('an-annotation')
            @wrapping.annotate_arg('bar', 'another-annotation')
            def provide_foo(self, bar):
                return 'a-foo with {0}'.format(bar)
            @wrapping.annotated_with('another-annotation')
            def provide_bar(self):
                return 'a-bar'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()])
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo with a-bar', class_one.foo)

    def test_inject_decorated_class_can_be_directly_provided(self):
        class SomeClass(object):
            @wrapping.injectable
            def __init__(self):
                self.foo = 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], only_use_explicit_bindings=True)
        class_one = obj_graph.provide(SomeClass)
        self.assertEqual('a-foo', class_one.foo)

    def test_non_inject_decorated_class_cannot_be_directly_provided(self):
        class SomeClass(object):
            def __init__(self):
                self.foo = 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], only_use_explicit_bindings=True)
        self.assertRaises(
            errors.NonExplicitlyBoundClassError, obj_graph.provide, SomeClass)

    def test_inject_decorated_class_is_explicitly_bound(self):
        class ClassOne(object):
            @wrapping.injectable
            def __init__(self, class_two):
                self.class_two = class_two
        class ClassTwo(object):
            @wrapping.injectable
            def __init__(self):
                self.foo = 'a-foo'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne, ClassTwo],
            only_use_explicit_bindings=True)
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-foo', class_one.class_two.foo)

    def test_explicit_binding_is_explicitly_bound(self):
        class ClassOne(object):
            @wrapping.injectable
            def __init__(self, class_two):
                self.class_two = class_two
        class SomeBindingSpec(binding.BindingSpec):
            def configure(self, bind):
                bind('class_two', to_instance='a-class-two')
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()],
            only_use_explicit_bindings=True)
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-class-two', class_one.class_two)

    def test_provider_fn_is_explicitly_bound(self):
        class ClassOne(object):
            @wrapping.injectable
            def __init__(self, class_two):
                self.class_two = class_two
        class SomeBindingSpec(binding.BindingSpec):
            def provide_class_two(self):
                return 'a-class-two'
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[ClassOne], binding_specs=[SomeBindingSpec()],
            only_use_explicit_bindings=True)
        class_one = obj_graph.provide(ClassOne)
        self.assertEqual('a-class-two', class_one.class_two)

    def test_non_bound_non_decorated_class_is_not_explicitly_bound(self):
        class ClassOne(object):
            @wrapping.injectable
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

    def test_can_inject_none_when_allowing_injecting_none(self):
        class SomeClass(object):
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(binding.BindingSpec):
            def provide_foo(self):
                return None
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], binding_specs=[SomeBindingSpec()],
            allow_injecting_none=True)
        some_class = obj_graph.provide(SomeClass)
        self.assertIsNone(some_class.foo)

    def test_cannot_inject_none_when_disallowing_injecting_none(self):
        class SomeClass(object):
            def __init__(self, foo):
                self.foo = foo
        class SomeBindingSpec(binding.BindingSpec):
            def provide_foo(self):
                return None
        obj_graph = object_graph.new_object_graph(
            modules=None, classes=[SomeClass], binding_specs=[SomeBindingSpec()],
            allow_injecting_none=False)
        self.assertRaises(errors.InjectingNoneDisallowedError,
                          obj_graph.provide, SomeClass)


class ObjectGraphWrapTest(unittest.TestCase):

    def test_can_inject_nothing_into_fn_with_zero_params(self):
        def return_something():
            return 'something'
        wrapped = object_graph.new_object_graph(modules=None, classes=[]).wrap(
            return_something)
        self.assertEqual('something', wrapped())

    def test_can_inject_nothing_into_fn_with_positional_passed_params(self):
        def add(a, b):
            return a + b
        wrapped = object_graph.new_object_graph(modules=None, classes=[]).wrap(add)
        self.assertEqual(5, wrapped(2, 3))

    def test_can_inject_nothing_into_fn_with_keyword_passed_params(self):
        def add(a, b):
            return a + b
        wrapped = object_graph.new_object_graph(modules=None, classes=[]).wrap(add)
        self.assertEqual(5, wrapped(a=2, b=3))

    def test_can_inject_nothing_into_fn_with_defaults(self):
        def add(a=2, b=3):
            return a + b
        wrapped = object_graph.new_object_graph(classes=[]).wrap(add)
        self.assertEqual(5, wrapped())

    def test_can_inject_nothing_into_fn_with_pargs_and_kwargs(self):
        def add(*pargs, **kwargs):
            return pargs[0] + kwargs['b']
        wrapped = object_graph.new_object_graph(modules=None, classes=[]).wrap(add)
        self.assertEqual(5, wrapped(2, b=3))

    def test_can_inject_something_into_first_positional_param(self):
        class Foo(object):
            def __init__(self):
                self.a = 2
        def add(foo, b):
            return foo.a + b
        wrapped = object_graph.new_object_graph(modules=None, classes=[Foo]).wrap(add)
        self.assertEqual(5, wrapped(b=3))

    def test_can_inject_something_into_non_first_positional_param(self):
        class Foo(object):
            def __init__(self):
                self.b = 3
        def add(a, foo):
            return a + foo.b
        wrapped = object_graph.new_object_graph(modules=None, classes=[Foo]).wrap(add)
        self.assertEqual(5, wrapped(2))
