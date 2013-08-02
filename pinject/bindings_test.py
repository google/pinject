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


import threading
import unittest

from pinject import bindings as bindings_lib
from pinject import binding_keys
from pinject import decorators
from pinject import errors
from pinject import injection_contexts
from pinject import required_bindings
from pinject import scoping


def new_in_default_scope(binding_key):
    """Returns a new Binding in the default scope.

    Args:
      binding_key: a BindingKey
      proviser_fn: a function taking a InjectionContext and ObjectGraph and
          returning an instance of the bound value
    Returns:
      a Binding
    """
    return bindings_lib.new_binding_to_instance(
        binding_key, 'unused', scoping.DEFAULT_SCOPE,
        get_binding_loc_fn=lambda: 'unknown')


class GetBindingKeyToBindingMapsTest(unittest.TestCase):

    def setUp(self):
        class SomeClass(object):
            pass
        self.some_binding_key = binding_keys.new('some_class')
        self.some_binding = new_in_default_scope(self.some_binding_key)
        self.another_some_binding = new_in_default_scope(self.some_binding_key)

    def assertBindingsReturnMaps(
            self, bindings, binding_key_to_binding,
            collided_binding_key_to_bindings,
            handle_binding_collision_fn='unused-handle-binding-collision'):
        self.assertEqual(
            (binding_key_to_binding, collided_binding_key_to_bindings),
            bindings_lib._get_binding_key_to_binding_maps(
                bindings, handle_binding_collision_fn))

    def assertBindingsRaise(
            self, bindings, error_type,
            handle_binding_collision_fn='unused-handle-binding-collision'):
        self.assertRaises(error_type,
                          bindings_lib._get_binding_key_to_binding_maps,
                          bindings, handle_binding_collision_fn)

    def test_no_input_bindings_returns_empty_maps(self):
        self.assertBindingsReturnMaps(
            bindings=[],
            binding_key_to_binding={}, collided_binding_key_to_bindings={})

    def test_single_binding_gets_returned(self):
        self.assertBindingsReturnMaps(
            bindings=[self.some_binding],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_colliding_classes_calls_handler(self):
        was_called = threading.Event()
        def handle_binding_collision_fn(
                colliding_binding, binding_key_to_binding,
                collided_binding_key_to_bindings):
            binding_key = colliding_binding.binding_key
            self.assertEqual(self.another_some_binding.binding_key, binding_key)
            self.assertEqual({self.some_binding_key: self.some_binding},
                             binding_key_to_binding)
            self.assertEqual({}, collided_binding_key_to_bindings)
            was_called.set()
        self.assertBindingsReturnMaps(
            bindings=[self.some_binding, self.another_some_binding],
            handle_binding_collision_fn=handle_binding_collision_fn,
            binding_key_to_binding={
                self.some_binding_key: self.another_some_binding},
            collided_binding_key_to_bindings={})
        self.assertTrue(was_called.is_set())


class GetOverallBindingKeyToBindingMapsTest(unittest.TestCase):

    def setUp(self):
        class SomeClass(object):
            pass
        self.some_binding_key = binding_keys.new('some_class')
        self.some_binding = new_in_default_scope(self.some_binding_key)
        self.another_some_binding = new_in_default_scope(self.some_binding_key)

    def assertBindingsListsReturnMaps(
            self, bindings_lists,
            binding_key_to_binding, collided_binding_key_to_bindings):
        self.assertEqual(
            (binding_key_to_binding, collided_binding_key_to_bindings),
            bindings_lib.get_overall_binding_key_to_binding_maps(
                bindings_lists))

    def assertBindingsListsRaise(self, bindings_lists, error_type):
        self.assertRaises(error_type,
                          bindings_lib.get_overall_binding_key_to_binding_maps,
                          bindings_lists)

    def test_no_input_bindings_returns_empty_maps(self):
        self.assertBindingsListsReturnMaps(
            bindings_lists=[],
            binding_key_to_binding={}, collided_binding_key_to_bindings={})

    def test_single_binding_gets_returned(self):
        self.assertBindingsListsReturnMaps(
            bindings_lists=[[self.some_binding]],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_higher_priority_binding_overrides_lower(self):
        self.assertBindingsListsReturnMaps(
            bindings_lists=[[self.another_some_binding], [self.some_binding]],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_higher_priority_binding_removes_collided_lower_priority(self):
        self.assertBindingsListsReturnMaps(
            bindings_lists=[[self.some_binding, self.another_some_binding],
                            [self.some_binding]],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_colliding_highest_priority_bindings_raises_error(self):
        self.assertBindingsListsRaise(
            bindings_lists=[[self.some_binding, self.another_some_binding]],
            error_type=errors.ConflictingExplicitBindingsError)


class BindingMappingTest(unittest.TestCase):

    def test_success(self):
        binding_mapping = bindings_lib.BindingMapping(
            {'a-binding-key': 'a-binding'}, {})
        self.assertEqual(
            'a-binding',
            binding_mapping.get('a-binding-key', 'injection-site-desc'))

    def test_unknown_binding_raises_error(self):
        binding_mapping = bindings_lib.BindingMapping(
            {'a-binding-key': 'a-binding'}, {})
        self.assertRaises(errors.NothingInjectableForArgError,
                          binding_mapping.get,
                          'unknown-binding-key', 'injection-site-desc')

    def test_colliding_bindings_raises_error(self):
        binding_key = binding_keys.new('unused')
        binding_one = new_in_default_scope(binding_key)
        binding_two = new_in_default_scope(binding_key)
        binding_mapping = bindings_lib.BindingMapping(
            {}, {'colliding-binding-key': [binding_one, binding_two]})
        self.assertRaises(errors.AmbiguousArgNameError, binding_mapping.get,
                          'colliding-binding-key', 'injection-site-desc')

    def test_verifying_ok_bindings_passes(self):
        binding_mapping = bindings_lib.BindingMapping(
            {'a-binding-key': 'a-binding'}, {})
        binding_mapping.verify_requirements([required_bindings.RequiredBinding(
            'a-binding-key', 'unused-require-loc')])

    def test_verifying_conflicting_required_binding_raises_error(self):
        binding_mapping = bindings_lib.BindingMapping(
            {}, {'conflicting-binding-key': ['a-binding', 'another-binding']})
        self.assertRaises(errors.ConflictingRequiredBindingError,
                          binding_mapping.verify_requirements,
                          [required_bindings.RequiredBinding(
                              'conflicting-binding-key', 'unused-require-loc')])

    def test_verifying_missing_required_binding_raises_error(self):
        binding_mapping = bindings_lib.BindingMapping({}, {})
        self.assertRaises(errors.MissingRequiredBindingError,
                          binding_mapping.verify_requirements,
                          [required_bindings.RequiredBinding(
                              'unknown-binding-key', 'a-require-loc')])


class DefaultGetArgNamesFromClassNameTest(unittest.TestCase):

    def test_single_word_lowercased(self):
        self.assertEqual(
            ['foo'], bindings_lib.default_get_arg_names_from_class_name('Foo'))

    def test_leading_underscore_stripped(self):
        self.assertEqual(
            ['foo'], bindings_lib.default_get_arg_names_from_class_name('_Foo'))

    def test_multiple_words_lowercased_with_underscores(self):
        self.assertEqual(
            ['foo_bar_baz'],
            bindings_lib.default_get_arg_names_from_class_name('FooBarBaz'))

    def test_malformed_class_name_raises_error(self):
        self.assertEqual(
            [], bindings_lib.default_get_arg_names_from_class_name(
                'notAllCamelCase'))


class FakeObjectProvider(object):

    def provide_class(self, cls, injection_context,
                      direct_init_pargs, direct_init_kwargs):
        return 'a-provided-{0}'.format(cls.__name__)

    def call_with_injection(self, provider_fn, injection_context,
                            direct_pargs, direct_kwargs):
        return provider_fn()


_UNUSED_INJECTION_SITE_FN = lambda: None
_UNUSED_INJECTION_CONTEXT = (
    injection_contexts.InjectionContextFactory('unused').new(
        _UNUSED_INJECTION_SITE_FN))
def call_provisor_fn(a_binding):
    return a_binding.proviser_fn(
        _UNUSED_INJECTION_CONTEXT, FakeObjectProvider(), pargs=[], kwargs={})


class GetExplicitClassBindingsTest(unittest.TestCase):

    def test_returns_no_bindings_for_no_input(self):
        self.assertEqual([], bindings_lib.get_explicit_class_bindings([]))

    def test_returns_binding_for_input_explicitly_injected_class(self):
        class SomeClass(object):
            @decorators.injectable
            def __init__(self):
                pass
        [explicit_binding] = bindings_lib.get_explicit_class_bindings(
            [SomeClass])
        self.assertEqual(binding_keys.new('some_class'),
                         explicit_binding.binding_key)
        self.assertEqual('a-provided-SomeClass',
                         call_provisor_fn(explicit_binding))

    def test_uses_provided_fn_to_map_class_names_to_arg_names(self):
        class SomeClass(object):
            @decorators.injectable
            def __init__(self):
                pass
        [explicit_binding] = bindings_lib.get_explicit_class_bindings(
            [SomeClass], get_arg_names_from_class_name=lambda _: ['foo'])
        self.assertEqual(binding_keys.new('foo'),
                         explicit_binding.binding_key)


class GetProviderBindingsTest(unittest.TestCase):

    def test_returns_no_bindings_for_non_binding_spec(self):
        class SomeClass(object):
            pass
        self.assertEqual([], bindings_lib.get_provider_bindings(
            SomeClass(), scoping._BUILTIN_SCOPES))

    def test_returns_binding_for_provider_fn(self):
        class SomeBindingSpec(bindings_lib.BindingSpec):
            def provide_foo(self):
                return 'a-foo'
        [implicit_binding] = bindings_lib.get_provider_bindings(
            SomeBindingSpec(), scoping._BUILTIN_SCOPES)
        self.assertEqual(binding_keys.new('foo'),
                         implicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(implicit_binding))

    def test_uses_provided_fn_to_map_provider_fn_names_to_arg_names(self):
        class SomeBindingSpec(bindings_lib.BindingSpec):
            def some_foo():
                return 'a-foo'
        def get_arg_names(fn_name):
            return ['foo'] if fn_name == 'some_foo' else []
        [implicit_binding] = bindings_lib.get_provider_bindings(
            SomeBindingSpec(), scoping._BUILTIN_SCOPES,
            get_arg_names_from_provider_fn_name=get_arg_names)
        self.assertEqual(binding_keys.new('foo'),
                         implicit_binding.binding_key)

    def test_raises_exception_if_scope_unknown(self):
        class SomeBindingSpec(bindings_lib.BindingSpec):
            def provide_foo(self):
                return 'a-foo'
        self.assertRaises(errors.UnknownScopeError,
                          bindings_lib.get_provider_bindings,
                          SomeBindingSpec(), known_scope_ids=[])


class GetImplicitClassBindingsTest(unittest.TestCase):

    def test_returns_no_bindings_for_no_input(self):
        self.assertEqual([], bindings_lib.get_implicit_class_bindings([]))

    def test_returns_binding_for_input_class(self):
        class SomeClass(object):
            pass
        [implicit_binding] = bindings_lib.get_implicit_class_bindings(
            [SomeClass])
        self.assertEqual(binding_keys.new('some_class'),
                         implicit_binding.binding_key)
        self.assertEqual('a-provided-SomeClass',
                         call_provisor_fn(implicit_binding))

    def test_returns_binding_for_correct_input_class(self):
        class ClassOne(object):
            pass
        class ClassTwo(object):
            pass
        implicit_bindings = bindings_lib.get_implicit_class_bindings(
            [ClassOne, ClassTwo])
        for implicit_binding in implicit_bindings:
            if (implicit_binding.binding_key ==
                binding_keys.new('class_one')):
                self.assertEqual(
                    'a-provided-ClassOne', call_provisor_fn(implicit_binding))
            else:
                self.assertEqual(implicit_binding.binding_key,
                                 binding_keys.new('class_two'))
                self.assertEqual(
                    'a-provided-ClassTwo', call_provisor_fn(implicit_binding))

    def test_uses_provided_fn_to_map_class_names_to_arg_names(self):
        class SomeClass(object):
            pass
        [implicit_binding] = bindings_lib.get_implicit_class_bindings(
            [SomeClass], get_arg_names_from_class_name=lambda _: ['foo'])
        self.assertEqual(binding_keys.new('foo'),
                         implicit_binding.binding_key)


class BinderTest(unittest.TestCase):

    def setUp(self):
        self.collected_bindings = []
        self.binder = bindings_lib.Binder(
            self.collected_bindings,
            scope_ids=[scoping.DEFAULT_SCOPE, 'known-scope'])

    def test_can_bind_to_class(self):
        class SomeClass(object):
            pass
        self.binder.bind('an-arg-name', to_class=SomeClass)
        [expected_binding] = [
            b for b in self.collected_bindings
            if b.binding_key == binding_keys.new('an-arg-name')]
        # TODO(kurts): test the proviser fn after the dust settles on how
        # exactly to do class bindings.

    def test_can_bind_to_instance(self):
        an_instance = object()
        self.binder.bind('an-arg-name', to_instance=an_instance)
        [only_binding] = self.collected_bindings
        self.assertEqual(binding_keys.new('an-arg-name'),
                         only_binding.binding_key)
        self.assertIs(an_instance, call_provisor_fn(only_binding))

    def test_can_bind_with_annotation(self):
        self.binder.bind('an-arg-name', annotated_with='an-annotation',
                         to_instance='an-instance')
        [only_binding] = self.collected_bindings
        self.assertEqual(
            binding_keys.new('an-arg-name', 'an-annotation'),
            only_binding.binding_key)

    def test_can_bind_with_scope(self):
        self.binder.bind('an-arg-name', to_instance='an-instance',
                         in_scope='known-scope')
        [only_binding] = self.collected_bindings
        self.assertEqual('known-scope', only_binding.scope_id)

    def test_binding_to_unknown_scope_raises_error(self):
        self.assertRaises(
            errors.UnknownScopeError, self.binder.bind, 'unused-arg-name',
            to_instance='unused-instance', in_scope='unknown-scope')

    def test_binding_to_nothing_raises_error(self):
        self.assertRaises(errors.NoBindingTargetArgsError,
                          self.binder.bind, 'unused-arg-name')

    def test_binding_to_multiple_things_raises_error(self):
        class SomeClass(object):
            pass
        self.assertRaises(errors.MultipleBindingTargetArgsError,
                          self.binder.bind, 'unused-arg-name',
                          to_class=SomeClass, to_instance=object())

    def test_binding_to_non_class_raises_error(self):
        self.assertRaises(errors.InvalidBindingTargetError,
                          self.binder.bind, 'unused-arg-name',
                          to_class='not-a-class')


class BindingSpecTest(unittest.TestCase):

    def test_equal_if_same_type(self):
        class SomeBindingSpec(bindings_lib.BindingSpec):
            pass
        self.assertEqual(SomeBindingSpec(), SomeBindingSpec())

    def test_not_equal_if_not_same_type(self):
        class BindingSpecOne(bindings_lib.BindingSpec):
            pass
        class BindingSpecTwo(bindings_lib.BindingSpec):
            pass
        self.assertNotEqual(BindingSpecOne(), BindingSpecTwo())

    def test_hash_equal_if_same_type(self):
        class SomeBindingSpec(bindings_lib.BindingSpec):
            pass
        self.assertEqual(hash(SomeBindingSpec()), hash(SomeBindingSpec()))

    def test_hash_not_equal_if_not_same_type(self):
        class BindingSpecOne(bindings_lib.BindingSpec):
            pass
        class BindingSpecTwo(bindings_lib.BindingSpec):
            pass
        self.assertNotEqual(hash(BindingSpecOne()), hash(BindingSpecTwo()))


class GetProviderFnBindingsTest(unittest.TestCase):

    def test_proviser_calls_provider_fn(self):
        def provide_foo():
            return 'a-foo'
        [provider_fn_binding] = bindings_lib.get_provider_fn_bindings(
            provide_foo, ['foo'])
        self.assertEqual('a-foo', call_provisor_fn(provider_fn_binding))

    # The rest of get_provider_fn_binding() is tested in
    # GetProviderFnDecorationsTest in conjection with @annotated_with() and
    # @in_scope().
