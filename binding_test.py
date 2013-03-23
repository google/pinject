
import unittest

import binding
import errors
import injecting
import wrapping


class NewBindingKeyTest(unittest.TestCase):

    def test_without_annotation(self):
        binding_key = binding.new_binding_key('an-arg-name')
        self.assertEqual('the arg name an-arg-name', str(binding_key))

    def test_with_annotation(self):
        binding_key = binding.new_binding_key('an-arg-name', 'an-annotation')
        self.assertEqual('the arg name an-arg-name annotated with an-annotation',
                         str(binding_key))


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


class BindingKeyWithAnnotationTest(unittest.TestCase):

    def test_equal_if_same_arg_name_and_annotation(self):
        binding_key_one = binding.BindingKeyWithAnnotation(
            'an-arg-name', 'an-annotation')
        binding_key_two = binding.BindingKeyWithAnnotation(
            'an-arg-name', 'an-annotation')
        self.assertEqual(binding_key_one, binding_key_two)
        self.assertEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertEqual(str(binding_key_one), str(binding_key_two))

    def test_unequal_if_not_same_arg_name(self):
        binding_key_one = binding.BindingKeyWithAnnotation(
            'arg-name-one', 'an-annotation')
        binding_key_two = binding.BindingKeyWithAnnotation(
            'arg-name-two', 'an-annotation')
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))

    def test_unequal_if_not_same_annotation(self):
        binding_key_one = binding.BindingKeyWithAnnotation(
            'arg-name-one', 'an-annotation')
        binding_key_two = binding.BindingKeyWithAnnotation(
            'arg-name-two', 'another-annotation')
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))

    def test_str(self):
        binding_key = binding.BindingKeyWithAnnotation(
            'an-arg-name', 'an-annotation')
        self.assertEqual('the arg name an-arg-name annotated with an-annotation',
                         str(binding_key))


class NewBindingMappingTest(unittest.TestCase):

    def test_no_input_bindings_returns_empty_mapping(self):
        binding_mapping = binding.new_binding_mapping([], [])
        self.assertRaises(errors.NothingInjectableForArgError,
                          binding_mapping.get_instance,
                          binding.BindingKeyWithoutAnnotation('anything'),
                          binding_key_stack=[], injector=None)

    def test_unknown_binding_raises_error(self):
        class SomeClass(object):
            pass
        binding_key = binding.BindingKeyWithoutAnnotation('some_class')
        binding_mapping = binding.new_binding_mapping(
            [], [binding.Binding(binding_key, SomeClass)])
        unknown_binding_key = binding.BindingKeyWithoutAnnotation(
            'unknown_class')
        self.assertRaises(errors.NothingInjectableForArgError,
                          binding_mapping.get_instance, unknown_binding_key,
                          binding_key_stack=[], injector=None)

    def test_single_implicit_class_gets_mapped(self):
        class SomeClass(object):
            pass
        binding_key = binding.BindingKeyWithoutAnnotation('some_class')
        binding_mapping = binding.new_binding_mapping(
            [], [binding.Binding(binding_key, binding.ProviderToProviser(SomeClass))])
        self.assertIsInstance(
            binding_mapping.get_instance(
                binding_key, binding_key_stack=[], injector=None),
            SomeClass)

    def test_multiple_noncolliding_implicit_classes_get_mapped(self):
        class ClassOne(object):
            pass
        class ClassTwo(object):
            pass
        binding_key_one = binding.BindingKeyWithoutAnnotation('class_one')
        binding_key_two = binding.BindingKeyWithoutAnnotation('class_two')
        binding_mapping = binding.new_binding_mapping(
            [], [binding.Binding(binding_key_one, binding.ProviderToProviser(ClassOne)),
                 binding.Binding(binding_key_two, binding.ProviderToProviser(ClassTwo))])
        self.assertIsInstance(
            binding_mapping.get_instance(
                binding_key_one, binding_key_stack=[], injector=None),
            ClassOne)
        self.assertIsInstance(
            binding_mapping.get_instance(
                binding_key_two, binding_key_stack=[], injector=None),
            ClassTwo)

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
                          binding_mapping.get_instance,
                          binding_key, binding_key_stack=[], injector=None)


class DefaultGetArgNamesFromClassNameTest(unittest.TestCase):

    def test_single_word_lowercased(self):
        self.assertEqual(['foo'], binding.default_get_arg_names_from_class_name('Foo'))

    def test_leading_underscore_stripped(self):
        self.assertEqual(['foo'], binding.default_get_arg_names_from_class_name('_Foo'))

    def test_multiple_words_lowercased_with_underscores(self):
        self.assertEqual(['foo_bar_baz'], binding.default_get_arg_names_from_class_name('FooBarBaz'))

    def test_malformed_class_name_raises_error(self):
        self.assertEqual([], binding.default_get_arg_names_from_class_name('notAllCamelCase'))


class FakeInjector(object):

    def provide(self, cls):
        return self._provide_class(cls, binding_key_stack=[])

    def _provide_class(self, cls, binding_key_stack):
        return 'a-provided-{0}'.format(cls.__name__)

    def _call_with_injection(self, provider_fn, binding_key_stack):
        return provider_fn()


_UNUSED_BINDING_KEY_STACK = []
def call_provisor_fn(a_binding):
    return a_binding.proviser_fn(_UNUSED_BINDING_KEY_STACK, FakeInjector())


class GetExplicitBindingsTest(unittest.TestCase):

    def test_returns_no_bindings_for_no_input(self):
        self.assertEqual([], binding.get_explicit_bindings([], []))

    def test_returns_binding_for_input_provider_fn(self):
        @wrapping.provides('foo')
        def some_function():
            return 'a-foo'
        [explicit_binding] = binding.get_explicit_bindings([], [some_function])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         explicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(explicit_binding))

    def test_returns_binding_for_provider_fn_on_input_class(self):
        class SomeClass(object):
            @staticmethod
            @wrapping.provides('foo')
            # TODO(kurts): figure out why the decorator order cannot be reversed.
            def some_function():
                return 'a-foo'
        [explicit_binding] = binding.get_explicit_bindings([SomeClass], [])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         explicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(explicit_binding))


class GetImplicitBindingsTest(unittest.TestCase):

    def test_returns_no_bindings_for_no_input(self):
        self.assertEqual([], binding.get_implicit_bindings([], []))

    def test_returns_binding_for_input_class(self):
        class SomeClass(object):
            pass
        [implicit_binding] = binding.get_implicit_bindings([SomeClass], functions=[])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('some_class'),
                         implicit_binding.binding_key)
        self.assertEqual('a-provided-SomeClass', call_provisor_fn(implicit_binding))

    def test_returns_binding_for_correct_input_class(self):
        class ClassOne(object):
            pass
        class ClassTwo(object):
            pass
        implicit_bindings = binding.get_implicit_bindings(
            [ClassOne, ClassTwo], functions=[])
        for implicit_binding in implicit_bindings:
            if (implicit_binding.binding_key ==
                binding.BindingKeyWithoutAnnotation('class_one')):
                self.assertEqual(
                    'a-provided-ClassOne', call_provisor_fn(implicit_binding))
            else:
                self.assertEqual(
                    implicit_binding.binding_key,
                    binding.BindingKeyWithoutAnnotation('class_two'))
                self.assertEqual(
                    'a-provided-ClassTwo', call_provisor_fn(implicit_binding))

    def test_uses_provided_fn_to_map_class_names_to_arg_names(self):
        class SomeClass(object):
            pass
        [implicit_binding] = binding.get_implicit_bindings(
            [SomeClass], functions=[],
            get_arg_names_from_class_name=lambda _: ['foo'])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         implicit_binding.binding_key)

    def test_returns_binding_for_input_provider_fn(self):
        def new_foo():
            return 'a-foo'
        [implicit_binding] = binding.get_implicit_bindings(
            classes=[], functions=[new_foo])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         implicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(implicit_binding))

    def test_returns_binding_for_staticmethod_provider_fn(self):
        class SomeClass(object):
            @staticmethod
            def new_foo():
                return 'a-foo'
        implicit_bindings = binding.get_implicit_bindings(
            classes=[SomeClass], functions=[])
        self.assertEqual([binding.BindingKeyWithoutAnnotation('some_class'),
                          binding.BindingKeyWithoutAnnotation('foo')],
                         [b.binding_key for b in implicit_bindings])
        self.assertEqual('a-foo', call_provisor_fn(implicit_bindings[1]))

    def test_returns_no_binding_for_input_non_provider_fn(self):
        def some_fn():
            pass
        self.assertEqual([], binding.get_implicit_bindings(
            classes=[], functions=[some_fn]))

    def test_uses_provided_fn_to_map_provider_fn_names_to_arg_names(self):
        def some_foo():
            return 'a-foo'
        [implicit_binding] = binding.get_implicit_bindings(
            classes=[], functions=[some_foo],
            get_arg_names_from_provider_fn_name=lambda _: ['foo'])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         implicit_binding.binding_key)


class BinderTest(unittest.TestCase):

    def setUp(self):
        self.collected_bindings = []
        self.binder = binding.Binder(self.collected_bindings)

    def test_can_bind_to_class(self):
        class SomeClass(object):
            pass
        self.binder.bind('an-arg-name', to_class=SomeClass)
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.BindingKeyWithoutAnnotation('an-arg-name'),
                         only_binding.binding_key)
        self.assertEqual('a-provided-SomeClass', call_provisor_fn(only_binding))

    def test_can_bind_to_instance(self):
        an_instance = object()
        self.binder.bind('an-arg-name', to_instance=an_instance)
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.BindingKeyWithoutAnnotation('an-arg-name'),
                         only_binding.binding_key)
        self.assertIs(an_instance, call_provisor_fn(only_binding))

    def test_can_bind_to_provider(self):
        self.binder.bind('an-arg-name', to_provider=lambda: 'a-provided-thing')
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.BindingKeyWithoutAnnotation('an-arg-name'),
                         only_binding.binding_key)
        self.assertEqual('a-provided-thing', call_provisor_fn(only_binding))

    def test_can_bind_with_annotation(self):
        self.binder.bind('an-arg-name', annotated_with='an-annotation',
                         to_provider=lambda: 'a-provided-thing')
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.BindingKeyWithAnnotation('an-arg-name',
                                                          'an-annotation'),
                         only_binding.binding_key)
        self.assertEqual('a-provided-thing', call_provisor_fn(only_binding))

    def test_binding_to_nothing_raises_error(self):
        self.assertRaises(errors.NoBindingTargetError,
                          self.binder.bind, 'unused-arg-name')

    def test_binding_to_multiple_things_raises_error(self):
        self.assertRaises(errors.MultipleBindingTargetsError,
                          self.binder.bind, 'unused-arg-name',
                          to_instance=object(), to_provider=lambda: None)

    def test_binding_to_non_class_raises_error(self):
        self.assertRaises(errors.InvalidBindingTargetError,
                          self.binder.bind, 'unused-arg-name',
                          to_class='not-a-class')

    def test_binding_to_non_provider_raises_error(self):
        self.assertRaises(errors.InvalidBindingTargetError,
                          self.binder.bind, 'unused-arg-name',
                          to_provider='not-a-provider')
