
import inspect
import unittest

import errors
import injecting
import scoping
import wrapping


class NewInjectorTest(unittest.TestCase):

    def test_can_create_injector_with_all_defaults(self):
        _ = injecting.new_injector()

    def test_creates_injector_using_given_modules(self):
        injector = injecting.new_injector(modules=[errors])
        self.assertIsInstance(injector.provide(errors.Error),
                              errors.Error)

    def test_creates_injector_using_given_classes(self):
        class SomeClass(object):
            pass
        injector = injecting.new_injector(classes=[SomeClass])
        self.assertIsInstance(injector.provide(SomeClass), SomeClass)

    def test_creates_injector_using_given_provider_fns(self):
        def new_foo():
            return 'a-foo'
        class ClassWithFooInjected(object):
            def __init__(self, foo):
                self.foo = foo
        injector = injecting.new_injector(
            classes=[ClassWithFooInjected], provider_fns=[new_foo])
        self.assertEqual('a-foo', injector.provide(ClassWithFooInjected).foo)

    def test_creates_injector_using_given_binding_fns(self):
        class ClassWithFooInjected(object):
            def __init__(self, foo):
                pass
        class SomeClass(object):
            pass
        def binding_fn(bind, **unused_kwargs):
            bind('foo', to_class=SomeClass)
        injector = injecting.new_injector(classes=[ClassWithFooInjected],
                                          binding_fns=[binding_fn])
        self.assertIsInstance(injector.provide(ClassWithFooInjected),
                              ClassWithFooInjected)

    def test_creates_injector_using_given_scopes(self):
        class SomeClass(object):
            def __init__(self, foo):
                self.foo = foo
        def binding_fn(bind, **unused_kwargs):
            bind('foo', to_provider=lambda: object(), in_scope='foo-scope')
        injector = injecting.new_injector(
            classes=[SomeClass], binding_fns=[binding_fn],
            id_to_scope={'foo-scope': scoping.SingletonScope()})
        some_class_one = injector.provide(SomeClass)
        some_class_two = injector.provide(SomeClass)
        self.assertIs(some_class_one.foo, some_class_two.foo)


class InjectorProvideTest(unittest.TestCase):

    def test_can_provide_trivial_class(self):
        class ExampleClassWithInit(object):
            def __init__(self):
                pass
        injector = injecting.new_injector(classes=[ExampleClassWithInit])
        self.assertTrue(isinstance(injector.provide(ExampleClassWithInit),
                                   ExampleClassWithInit))

    def test_can_provide_class_without_own_init(self):
        class ExampleClassWithoutInit(object):
            pass
        injector = injecting.new_injector(classes=[ExampleClassWithoutInit])
        self.assertIsInstance(injector.provide(ExampleClassWithoutInit),
                              ExampleClassWithoutInit)

    def test_can_directly_provide_class_with_colliding_arg_name(self):
        class _CollidingExampleClass(object):
            pass
        class CollidingExampleClass(object):
            pass
        injector = injecting.new_injector(
            classes=[_CollidingExampleClass, CollidingExampleClass])
        self.assertIsInstance(injector.provide(CollidingExampleClass),
                              CollidingExampleClass)

    def test_can_provide_class_that_itself_requires_injection(self):
        class ClassOne(object):
            def __init__(self, class_two):
                pass
        class ClassTwo(object):
            pass
        injector = injecting.new_injector(classes=[ClassOne, ClassTwo])
        self.assertIsInstance(injector.provide(ClassOne), ClassOne)

    def test_raises_error_if_arg_is_ambiguously_injectable(self):
        class _CollidingExampleClass(object):
            pass
        class CollidingExampleClass(object):
            pass
        class AmbiguousParamClass(object):
            def __init__(self, colliding_example_class):
                pass
        injector = injecting.new_injector(
            classes=[_CollidingExampleClass, CollidingExampleClass,
                     AmbiguousParamClass])
        self.assertRaises(errors.AmbiguousArgNameError,
                          injector.provide, AmbiguousParamClass)

    def test_raises_error_if_arg_refers_to_no_known_class(self):
        class UnknownParamClass(object):
            def __init__(self, unknown_class):
                pass
        injector = injecting.new_injector(classes=[UnknownParamClass])
        self.assertRaises(errors.NothingInjectableForArgError,
                          injector.provide, UnknownParamClass)

    def test_raises_error_if_injection_cycle(self):
        class ClassOne(object):
            def __init__(self, class_two):
                pass
        class ClassTwo(object):
            def __init__(self, class_one):
                pass
        injector = injecting.new_injector(classes=[ClassOne, ClassTwo])
        self.assertRaises(errors.CyclicInjectionError,
                          injector.provide, ClassOne)

    def test_injects_args_of_provider_fns(self):
        class ClassOne(object):
            pass
        def provides_class_one(class_one):
            class_one.three = 3
            return class_one
        class ClassTwo(object):
            def __init__(self, foo):
                self.foo = foo
        def binding_fn(bind, **unused_kwargs):
            bind('foo', to_provider=provides_class_one)
        injector = injecting.new_injector(classes=[ClassOne, ClassTwo],
                                          binding_fns=[binding_fn])
        class_two = injector.provide(ClassTwo)
        self.assertEqual(3, class_two.foo.three)

    def test_can_provide_arg_with_annotation(self):
        class ClassOne(object):
            @wrapping.annotate('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        def bind_annotated_foo(bind, **unused_kwargs):
            bind('foo', annotated_with='an-annotation', to_instance='a-foo')
        injector = injecting.new_injector(classes=[ClassOne],
                                          binding_fns=[bind_annotated_foo])
        class_one = injector.provide(ClassOne)
        self.assertEqual('a-foo', class_one.foo)

    def test_annotated_arg_is_provided_in_correct_scope(self):
        class SomeClass(object):
            @wrapping.annotate('foo', 'specific-foo')
            @wrapping.annotate('bar', 'specific-bar')
            def __init__(self, foo, bar):
                self.foo = foo
                self.bar = bar
        def binding_fn(bind, **unused_kwargs):
            bind('foo', annotated_with='specific-foo', to_provider=lambda: object(),
                 in_scope=scoping.SINGLETON)
            bind('bar', annotated_with='specific-bar', to_provider=lambda: object(),
                 in_scope=scoping.PROTOTYPE)
        injector = injecting.new_injector(classes=[SomeClass],
                                          binding_fns=[binding_fn])
        class_one = injector.provide(SomeClass)
        class_two = injector.provide(SomeClass)
        self.assertIs(class_one.foo, class_two.foo)
        self.assertIsNot(class_one.bar, class_two.bar)

    def test_raises_error_if_only_binding_has_different_annotation(self):
        class ClassOne(object):
            @wrapping.annotate('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        def bind_annotated_foo(bind, **unused_kwargs):
            bind('foo', annotated_with='other-annotation', to_instance='a-foo')
        injector = injecting.new_injector(classes=[ClassOne],
                                          binding_fns=[bind_annotated_foo])
        self.assertRaises(errors.NothingInjectableForArgError,
                          injector.provide, ClassOne)

    def test_raises_error_if_only_binding_has_no_annotation(self):
        class ClassOne(object):
            @wrapping.annotate('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        def bind_unannotated_foo(bind, **unused_kwargs):
            bind('foo', to_instance='a-foo')
        injector = injecting.new_injector(classes=[ClassOne],
                                          binding_fns=[bind_unannotated_foo])
        self.assertRaises(errors.NothingInjectableForArgError,
                          injector.provide, ClassOne)

    def test_can_provide_using_explicit_provider_fn(self):
        class ClassOne(object):
            def __init__(self, foo):
                self.foo = foo
            @staticmethod
            @wrapping.provides('foo')
            def foo_provider():
                return 'a-foo'
        injector = injecting.new_injector(classes=[ClassOne])
        class_one = injector.provide(ClassOne)
        self.assertEqual('a-foo', class_one.foo)

    def test_can_provide_using_implicit_provider_fn(self):
        class ClassOne(object):
            def __init__(self, foo):
                self.foo = foo
            @staticmethod
            def new_foo():
                return 'a-foo'
        injector = injecting.new_injector(classes=[ClassOne])
        class_one = injector.provide(ClassOne)
        self.assertEqual('a-foo', class_one.foo)

    def test_implicit_provider_fn_overrides_implicit_class_binding(self):
        class ClassOne(object):
            def __init__(self, foo):
                self.foo = foo
        class Foo(object):
            @staticmethod
            def new_foo():
                return 'a-foo'
        injector = injecting.new_injector(classes=[ClassOne, Foo])
        class_one = injector.provide(ClassOne)
        self.assertEqual('a-foo', class_one.foo)

    def test_autoinjects_args_of_provider_fn(self):
        class ClassOne(object):
            def __init__(self, foo):
                self.foo = foo
        def new_foo(bar):
            return 'a-foo with {0}'.format(bar)
        def new_bar():
            return 'a-bar'
        injector = injecting.new_injector(
            classes=[ClassOne], provider_fns=[new_foo, new_bar])
        class_one = injector.provide(ClassOne)
        self.assertEqual('a-foo with a-bar', class_one.foo)

    def test_can_use_annotate_with_provides(self):
        class ClassOne(object):
            @wrapping.annotate('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        @wrapping.provides('foo', annotated_with='an-annotation')
        @wrapping.annotate('bar', 'another-annotation')
        def new_foo(bar):
            return 'a-foo with {0}'.format(bar)
        @wrapping.provides('bar', annotated_with='another-annotation')
        def new_bar():
            return 'a-bar'
        injector = injecting.new_injector(
            classes=[ClassOne], provider_fns=[new_foo, new_bar])
        class_one = injector.provide(ClassOne)
        self.assertEqual('a-foo with a-bar', class_one.foo)


class InjectorWrapTest(unittest.TestCase):

    def test_can_inject_nothing_into_fn_with_zero_params(self):
        def return_something():
            return 'something'
        wrapped = injecting.new_injector(classes=[]).wrap(return_something)
        self.assertEqual('something', wrapped())

    def test_can_inject_nothing_into_fn_with_positional_passed_params(self):
        def add(a, b):
            return a + b
        wrapped = injecting.new_injector(classes=[]).wrap(add)
        self.assertEqual(5, wrapped(2, 3))

    def test_can_inject_nothing_into_fn_with_keyword_passed_params(self):
        def add(a, b):
            return a + b
        wrapped = injecting.new_injector(classes=[]).wrap(add)
        self.assertEqual(5, wrapped(a=2, b=3))

    def test_can_inject_nothing_into_fn_with_defaults(self):
        def add(a=2, b=3):
            return a + b
        wrapped = injecting.new_injector(classes=[]).wrap(add)
        self.assertEqual(5, wrapped())

    def test_can_inject_nothing_into_fn_with_pargs_and_kwargs(self):
        def add(*pargs, **kwargs):
            return pargs[0] + kwargs['b']
        wrapped = injecting.new_injector(classes=[]).wrap(add)
        self.assertEqual(5, wrapped(2, b=3))

    def test_can_inject_something_into_first_positional_param(self):
        class Foo(object):
            def __init__(self):
                self.a = 2
        def add(foo, b):
            return foo.a + b
        wrapped = injecting.new_injector(classes=[Foo]).wrap(add)
        self.assertEqual(5, wrapped(b=3))

    def test_can_inject_something_into_non_first_positional_param(self):
        class Foo(object):
            def __init__(self):
                self.b = 3
        def add(a, foo):
            return a + foo.b
        wrapped = injecting.new_injector(classes=[Foo]).wrap(add)
        self.assertEqual(5, wrapped(2))
