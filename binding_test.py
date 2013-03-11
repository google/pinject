
import unittest

import binding
import errors


class BindingKeyWithoutAnnotationTest(unittest.TestCase):

    def testEqualIfSameArgName(self):
        binding_key_one = binding.BindingKeyWithoutAnnotation('an-arg-name')
        binding_key_two = binding.BindingKeyWithoutAnnotation('an-arg-name')
        self.assertEqual(binding_key_one, binding_key_two)
        self.assertEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertEqual(str(binding_key_one), str(binding_key_two))

    def testUnequalIfNotSameArgName(self):
        binding_key_one = binding.BindingKeyWithoutAnnotation('arg-name-one')
        binding_key_two = binding.BindingKeyWithoutAnnotation('arg-name-two')
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))

    def testStr(self):
        binding_key = binding.BindingKeyWithoutAnnotation('an-arg-name')
        self.assertEqual('the arg name an-arg-name', str(binding_key))


class NewBindingMappingTest(unittest.TestCase):

    def testNoInputBindingsReturnsEmptyMapping(self):
        binding_mapping = binding.new_binding_mapping([], [])
        self.assertRaises(errors.NothingInjectableForArgNameError,
                          binding_mapping.get_class,
                          binding.BindingKeyWithoutAnnotation('anything'))

    def testUnknownBindingRaisesError(self):
        class SomeClass(object):
            pass
        binding_key = binding.BindingKeyWithoutAnnotation('some_class')
        binding_mapping = binding.new_binding_mapping(
            [], [binding.Binding(binding_key, SomeClass)])
        unknown_binding_key = binding.BindingKeyWithoutAnnotation(
            'unknown_class')
        self.assertRaises(errors.NothingInjectableForArgNameError,
                          binding_mapping.get_class, unknown_binding_key)

    def testSingleImplicitClassGetsMapped(self):
        class SomeClass(object):
            pass
        binding_key = binding.BindingKeyWithoutAnnotation('some_class')
        binding_mapping = binding.new_binding_mapping(
            [], [binding.Binding(binding_key, SomeClass)])
        self.assertEqual(SomeClass, binding_mapping.get_class(binding_key))

    def testMultipleNoncollidingImplicitClassesGetMapped(self):
        class ClassOne(object):
            pass
        class ClassTwo(object):
            pass
        binding_key_one = binding.BindingKeyWithoutAnnotation('class_one')
        binding_key_two = binding.BindingKeyWithoutAnnotation('class_two')
        binding_mapping = binding.new_binding_mapping(
            [], [binding.Binding(binding_key_one, ClassOne),
                 binding.Binding(binding_key_two, ClassTwo)])
        self.assertEqual(ClassOne, binding_mapping.get_class(binding_key_one))
        self.assertEqual(ClassTwo, binding_mapping.get_class(binding_key_two))

    def testMultipleCollidingClassesRaisesError(self):
        class SomeClass(object):
            pass
        class _SomeClass(object):
            pass
        binding_key = binding.BindingKeyWithoutAnnotation('some_class')
        binding_mapping = binding.new_binding_mapping(
            [], [binding.Binding(binding_key, SomeClass),
                 binding.Binding(binding_key, _SomeClass)])
        self.assertRaises(errors.AmbiguousArgNameError,
                          binding_mapping.get_class, binding_key)


class DefaultGetArgNamesFromClassNameTest(unittest.TestCase):

    def test_single_word_lowercased(self):
        self.assertEqual(['foo'], binding.default_get_arg_names_from_class_name('Foo'))

    def test_leading_underscore_stripped(self):
        self.assertEqual(['foo'], binding.default_get_arg_names_from_class_name('_Foo'))

    def test_multiple_words_lowercased_with_underscores(self):
        self.assertEqual(['foo_bar_baz'], binding.default_get_arg_names_from_class_name('FooBarBaz'))

    def test_malformed_class_name_raises_error(self):
        self.assertEqual([], binding.default_get_arg_names_from_class_name('notAllCamelCase'))


class GetImplicitBindingsTest(unittest.TestCase):

    # TODO(kurts): test this
    pass

    # def testUsesProvidedFunctionToMapClassNamesToArgNames(self):
    #     class SomeClass(object):
    #         pass
    #     binding_mapping = binding.new_binding_mapping(
    #         [SomeClass], lambda unused: ['some_arg_name'])
    #     self.assertEqual(SomeClass, binding_mapping.get_class('some_arg_name'))
