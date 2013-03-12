
import unittest

import binding
import errors


class BindingKeyWithoutAnnotationTest(unittest.TestCase):

    def test_equal_if_same_arg_name(self):
        binding_key_one = binding.BindingKeyWithoutAnnotation('an-arg-name')
        binding_key_two = binding.BindingKeyWithoutAnnotation('an-arg-name')
        self.assertEqual(binding_key_one, binding_key_two)
        self.assertEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertEqual(str(binding_key_one), str(binding_key_two))

    def test_unequal_if_not_same_arg_name(self):
        binding_key_one = binding.BindingKeyWithoutAnnotation('arg-name-one')
        binding_key_two = binding.BindingKeyWithoutAnnotation('arg-name-two')
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))

    def test_str(self):
        binding_key = binding.BindingKeyWithoutAnnotation('an-arg-name')
        self.assertEqual('the arg name an-arg-name', str(binding_key))


class NewBindingMappingTest(unittest.TestCase):

    def test_no_input_bindings_returns_empty_mapping(self):
        binding_mapping = binding.new_binding_mapping([], [])
        self.assertRaises(errors.NothingInjectableForArgNameError,
                          binding_mapping.get_class,
                          binding.BindingKeyWithoutAnnotation('anything'))

    def test_unknown_binding_raises_error(self):
        class SomeClass(object):
            pass
        binding_key = binding.BindingKeyWithoutAnnotation('some_class')
        binding_mapping = binding.new_binding_mapping(
            [], [binding.Binding(binding_key, SomeClass)])
        unknown_binding_key = binding.BindingKeyWithoutAnnotation(
            'unknown_class')
        self.assertRaises(errors.NothingInjectableForArgNameError,
                          binding_mapping.get_class, unknown_binding_key)

    def test_single_implicit_class_gets_mapped(self):
        class SomeClass(object):
            pass
        binding_key = binding.BindingKeyWithoutAnnotation('some_class')
        binding_mapping = binding.new_binding_mapping(
            [], [binding.Binding(binding_key, SomeClass)])
        self.assertEqual(SomeClass, binding_mapping.get_class(binding_key))

    def test_multiple_noncolliding_implicit_classes_get_mapped(self):
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

    def test_multiple_colliding_classes_raises_error(self):
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

    def test_returns_no_bindings_for_no_input(self):
        self.assertEqual([], binding.get_implicit_bindings([]))

    def test_returns_binding_for_input_class(self):
        class SomeClass(object):
            pass
        binding_key = binding.BindingKeyWithoutAnnotation('some_class')
        self.assertEqual([binding.Binding(binding_key, SomeClass)],
                         binding.get_implicit_bindings([SomeClass]))

    def test_uses_provided_fn_to_map_class_names_to_arg_names(self):
        class SomeClass(object):
            pass
        binding_key = binding.BindingKeyWithoutAnnotation('foo')
        self.assertEqual(
            [binding.Binding(binding_key, SomeClass)],
            binding.get_implicit_bindings(
                [SomeClass], get_arg_names_from_class_name=lambda _: ['foo']))
