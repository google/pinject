
import inspect
import unittest

import binding
import errors
import injecting


class FakeInjector(object):

    def _provide_from_binding_key(self, binding_key, binding_key_stack):
        return 'provided with {0}'.format(binding_key)


class AnnotateTest(unittest.TestCase):

    def test_adds_binding_in_pinject_decorated_fn(self):
        @injecting.annotate('foo', 'an-annotation')
        def some_function(foo):
            return foo
        self.assertTrue(hasattr(some_function, injecting._IS_DECORATOR_ATTR))
        self.assertEqual([binding.BindingKeyWithAnnotation('foo', 'an-annotation')],
                         [b.binding_key for b in getattr(some_function,
                                                         injecting._BINDINGS_ATTR)])
        self.assertEqual(['provided with the arg name foo annotated with an-annotation'],
                         [b.proviser_fn('unused-binding-key-stack', FakeInjector())
                          for b in getattr(some_function, injecting._BINDINGS_ATTR)])


class InjectTest(unittest.TestCase):

    def test_adds_binding_in_pinject_decorated_fn(self):
        @injecting.inject('foo', with_instance=3)
        def some_function(foo):
            return foo
        self.assertTrue(hasattr(some_function, injecting._IS_DECORATOR_ATTR))
        self.assertEqual([binding.BindingKeyWithoutAnnotation('foo')],
                         [b.binding_key for b in getattr(some_function,
                                                         injecting._BINDINGS_ATTR)])
        self.assertEqual([3],
                         [b.proviser_fn('unused-binding-key-stack', 'unused-injector')
                          for b in getattr(some_function, injecting._BINDINGS_ATTR)])

    def test_raises_error_if_injecting_nonexistent_arg(self):
        def do_bad_inject():
            @injecting.inject('foo', with_instance=3)
            def some_function(bar):
                return bar
        self.assertRaises(errors.NoSuchArgToInjectError, do_bad_inject)

    def test_reuses_decorated_fn_when_multiple_injections(self):
        @injecting.inject('foo', with_instance=3)
        @injecting.inject('bar', with_instance=4)
        def some_function(foo, bar):
            return foo + bar
        self.assertEqual([binding.BindingKeyWithoutAnnotation('bar'),
                          binding.BindingKeyWithoutAnnotation('foo')],
                         [b.binding_key
                          for b in getattr(some_function,
                                           injecting._BINDINGS_ATTR)])

    def test_can_call_inject_decorated_fn_normally(self):
        @injecting.inject('foo', with_instance=3)
        def some_function(foo):
            return foo
        self.assertEqual('an-arg', some_function('an-arg'))

    def test_can_introspect_inject_decorated_fn(self):
        @injecting.inject('foo', with_instance=3)
        def some_function(foo, bar='BAR', *pargs, **kwargs):
            pass
        arg_names, varargs, keywords, defaults = inspect.getargspec(
            some_function)
        self.assertEqual(['foo', 'bar'], arg_names)
        self.assertEqual('pargs', varargs)
        self.assertEqual('kwargs', keywords)
        self.assertEqual(('BAR',), defaults)


class NewInjectorTest(unittest.TestCase):

    def test_creates_injector_using_given_modules(self):
        injector = injecting.new_injector(modules=[errors])
        self.assertIsInstance(injector.provide(errors.Error),
                              errors.Error)

    def test_creates_injector_using_given_classes(self):
        class SomeClass(object):
            pass
        injector = injecting.new_injector(classes=[SomeClass])
        self.assertIsInstance(injector.provide(SomeClass), SomeClass)

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

    def test_can_provide_class_with_explicitly_injected_arg(self):
        class SomeClass(object):
            @injecting.inject('foo', with_instance=3)
            def __init__(self, foo):
                self.foo = foo
        injector = injecting.new_injector(classes=[SomeClass])
        self.assertEqual(3, injector.provide(SomeClass).foo)

    def test_can_provide_class_with_explicitly_and_implicitly_injected_args(self):
        class ClassOne(object):
            def __init__(self):
                self.foo = 1
        class ClassTwo(object):
            @injecting.inject('foo', with_instance=2)
            def __init__(self, foo, class_one):
                self.foo = foo
                self.class_one = class_one
        injector = injecting.new_injector(classes=[ClassOne, ClassTwo])
        class_two = injector.provide(ClassTwo)
        self.assertEqual(2, class_two.foo)
        self.assertEqual(1, class_two.class_one.foo)

    def test_injects_implicitly_injected_args_of_provider_fns(self):
        class ClassOne(object):
            pass
        def provides_class_one(class_one):
            class_one.three = 3
            return class_one
        class ClassTwo(object):
            @injecting.inject('foo', with_provider=provides_class_one)
            def __init__(self, foo):
                self.foo = foo
        injector = injecting.new_injector(classes=[ClassOne, ClassTwo])
        class_two = injector.provide(ClassTwo)
        self.assertEqual(3, class_two.foo.three)

    def test_injects_explicitly_injected_args_of_provider_fns(self):
        class ClassOne(object):
            pass
        @injecting.inject('three', with_instance=3)
        def provides_class_one(three):
            class_one = ClassOne()
            class_one.three = three
            return class_one
        class ClassTwo(object):
            @injecting.inject('foo', with_provider=provides_class_one)
            def __init__(self, foo):
                self.foo = foo
        injector = injecting.new_injector(classes=[ClassOne, ClassTwo])
        class_two = injector.provide(ClassTwo)
        self.assertEqual(3, class_two.foo.three)

    def test_can_provide_arg_with_annotation(self):
        class ClassOne(object):
            @injecting.annotate('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        def bind_annotated_foo(bind, **unused_kwargs):
            bind('foo', annotated_with='an-annotation', to_instance='a-foo')
        injector = injecting.new_injector(classes=[ClassOne],
                                          binding_fns=[bind_annotated_foo])
        class_one = injector.provide(ClassOne)
        self.assertEqual('a-foo', class_one.foo)

    def test_raises_error_if_only_binding_has_different_annotation(self):
        class ClassOne(object):
            @injecting.annotate('foo', 'an-annotation')
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
            @injecting.annotate('foo', 'an-annotation')
            def __init__(self, foo):
                self.foo = foo
        def bind_unannotated_foo(bind, **unused_kwargs):
            bind('foo', to_instance='a-foo')
        injector = injecting.new_injector(classes=[ClassOne],
                                          binding_fns=[bind_unannotated_foo])
        self.assertRaises(errors.NothingInjectableForArgError,
                          injector.provide, ClassOne)


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
