
import unittest

import errors
import injecting


class GetArgNamesFromClassNameTest(unittest.TestCase):

    def test_single_word_lowercased(self):
        self.assertEqual(['foo'], injecting._default_get_arg_names_from_class_name('Foo'))

    def test_leading_underscore_stripped(self):
        self.assertEqual(['foo'], injecting._default_get_arg_names_from_class_name('_Foo'))

    def test_multiple_words_lowercased_with_underscores(self):
        self.assertEqual(['foo_bar_baz'], injecting._default_get_arg_names_from_class_name('FooBarBaz'))

    def test_malformed_class_name_raises_error(self):
        self.assertEqual([], injecting._default_get_arg_names_from_class_name('notAllCamelCase'))


class NewArgNameToClassMappingTest(unittest.TestCase):

    def testNoInputClassesReturnsEmptyMapping(self):
        arg_name_class_mapping = injecting._new_arg_name_to_class_mapping([])
        self.assertRaises(errors.NothingInjectableForArgNameError,
                          arg_name_class_mapping.get, 'anything')

    def testSingleClassGetsMapped(self):
        class SomeClass(object):
            pass
        arg_name_class_mapping = injecting._new_arg_name_to_class_mapping(
            [SomeClass])
        self.assertEqual(SomeClass, arg_name_class_mapping.get('some_class'))

    def testUnknownArgNameRaisesError(self):
        class SomeClass(object):
            pass
        arg_name_class_mapping = injecting._new_arg_name_to_class_mapping(
            [SomeClass])
        self.assertRaises(errors.NothingInjectableForArgNameError,
                          arg_name_class_mapping.get, 'unknown_class')

    def testMultipleNoncollidingClassesGetMapped(self):
        class ClassOne(object):
            pass
        class ClassTwo(object):
            pass
        arg_name_class_mapping = injecting._new_arg_name_to_class_mapping(
            [ClassOne, ClassTwo])
        self.assertEqual(ClassOne, arg_name_class_mapping.get('class_one'))
        self.assertEqual(ClassTwo, arg_name_class_mapping.get('class_two'))

    def testMultipleCollidingClassesRaisesError(self):
        class SomeClass(object):
            pass
        class _SomeClass(object):
            pass
        arg_name_class_mapping = injecting._new_arg_name_to_class_mapping(
            [SomeClass, _SomeClass])
        self.assertRaises(errors.AmbiguousArgNameError,
                          arg_name_class_mapping.get, 'some_class')

    def testUsesProvidedFunctionToMapClassNamesToArgNames(self):
        class SomeClass(object):
            pass
        arg_name_class_mapping = injecting._new_arg_name_to_class_mapping(
            [SomeClass], lambda unused: ['some_arg_name'])
        self.assertEqual(SomeClass, arg_name_class_mapping.get('some_arg_name'))


class InjectorTest(unittest.TestCase):

    def test_can_provide_trivial_class(self):
        class ExampleClassWithInit(object):
            def __init__(self):
                pass
        injector = injecting.NewInjector(classes=[ExampleClassWithInit])
        self.assertTrue(isinstance(injector.provide(ExampleClassWithInit),
                                   ExampleClassWithInit))

    def test_can_provide_class_without_own_init(self):
        class ExampleClassWithoutInit(object):
            pass
        injector = injecting.NewInjector(classes=[ExampleClassWithoutInit])
        self.assertTrue(isinstance(injector.provide(ExampleClassWithoutInit),
                                   ExampleClassWithoutInit))

    def test_can_directly_provide_class_with_colliding_arg_name(self):
        class _CollidingExampleClass(object):
            pass
        class CollidingExampleClass(object):
            pass
        injector = injecting.NewInjector(
            classes=[_CollidingExampleClass, CollidingExampleClass])
        self.assertTrue(isinstance(injector.provide(CollidingExampleClass),
                                   CollidingExampleClass))

    def test_can_provide_class_that_itself_requires_injection(self):
        class ClassOne(object):
            def __init__(self, class_two):
                pass
        class ClassTwo(object):
            pass
        injector = injecting.NewInjector(classes=[ClassOne, ClassTwo])
        self.assertTrue(isinstance(injector.provide(ClassOne), ClassOne))

    def test_raises_error_if_arg_is_ambiguously_injectable(self):
        class _CollidingExampleClass(object):
            pass
        class CollidingExampleClass(object):
            pass
        class AmbiguousParamClass(object):
            def __init__(self, colliding_example_class):
                pass
        injector = injecting.NewInjector(
            classes=[_CollidingExampleClass, CollidingExampleClass,
                     AmbiguousParamClass])
        self.assertRaises(errors.AmbiguousArgNameError,
                          injector.provide, AmbiguousParamClass)

    def test_raises_error_if_arg_refers_to_no_known_class(self):
        class UnknownParamClass(object):
            def __init__(self, unknown_class):
                pass
        injector = injecting.NewInjector(classes=[UnknownParamClass])
        self.assertRaises(errors.NothingInjectableForArgNameError,
                          injector.provide, UnknownParamClass)
