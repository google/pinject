
import unittest

import binding
import errors
import scoping


class PrototypeScopeTest(unittest.TestCase):

    def test_always_calls_provider_fn(self):
        next_provided = [0]
        def provider_fn():
            provided = next_provided[0]
            next_provided[0] += 1
            return provided
        scope = scoping.PrototypeScope()
        binding_key = binding.BindingKeyWithoutAnnotation('unused')
        self.assertEqual(
            range(10),
            [scope.provide(binding_key, provider_fn) for _ in xrange(10)])


class SingletonScopeTest(unittest.TestCase):

    def setUp(self):
        self.scope = scoping.SingletonScope()
        self.binding_key_one = binding.BindingKeyWithoutAnnotation('one')
        self.binding_key_two = binding.BindingKeyWithoutAnnotation('two')
        self.provider_fn = lambda: object()

    def test_calls_provider_fn_just_once_for_same_binding_key(self):
        self.assertEqual(
            self.scope.provide(self.binding_key_one, self.provider_fn),
            self.scope.provide(self.binding_key_one, self.provider_fn))

    def test_calls_provider_fn_multiple_tiems_for_different_binding_keys(self):
        self.assertNotEqual(
            self.scope.provide(self.binding_key_one, self.provider_fn),
            self.scope.provide(self.binding_key_two, self.provider_fn))

    def test_can_call_provider_fn_that_calls_back_to_singleton_scope(self):
        def provide_from_singleton_scope():
            return self.scope.provide(self.binding_key_two, lambda: 'provided')
        self.assertEqual('provided',
                         self.scope.provide(self.binding_key_one,
                                            provide_from_singleton_scope))


class GetIdToScopeWithDefaultsTest(unittest.TestCase):

    def test_adds_default_scopes_to_given_scopes(self):
        orig_id_to_scope = {'a-scope-id': 'a-scope'}
        id_to_scope = scoping.get_id_to_scope_with_defaults(orig_id_to_scope)
        self.assertEqual('a-scope', id_to_scope['a-scope-id'])
        self.assertIn(scoping.SINGLETON, id_to_scope)
        self.assertIn(scoping.PROTOTYPE, id_to_scope)

    def test_returns_default_scopes_if_none_given(self):
        id_to_scope = scoping.get_id_to_scope_with_defaults()
        self.assertEqual(set([scoping.SINGLETON, scoping.PROTOTYPE]),
                         set(id_to_scope.keys()))

    def test_does_not_allow_overriding_prototype_scope(self):
        self.assertRaises(errors.OverridingDefaultScopeError,
                          scoping.get_id_to_scope_with_defaults,
                          id_to_scope={scoping.PROTOTYPE: 'unused'})

    def test_does_not_allow_overriding_singleton_scope(self):
        self.assertRaises(errors.OverridingDefaultScopeError,
                          scoping.get_id_to_scope_with_defaults,
                          id_to_scope={scoping.SINGLETON: 'unused'})


class BindableScopesTest(unittest.TestCase):

    def setUp(self):
        def is_scope_usable_from_scope(child_scope_id, parent_scope_id):
            return child_scope_id == 'usable-scope-id'
        self.bindable_scopes = scoping.BindableScopes(
            {'usable-scope-id': 'usable-scope'}, is_scope_usable_from_scope)

    def test_get_sub_scope_successfully(self):
        usable_binding = binding.Binding(
            binding.BindingKeyWithoutAnnotation('foo'),
            'unused-proviser-fn', 'usable-scope-id')
        self.assertEqual(
            'usable-scope',
            self.bindable_scopes.get_sub_scope(
                usable_binding, binding.new_binding_context()))

    def test_sub_scope_not_usable_from_scope_raises_error(self):
        unusable_binding = binding.Binding(
            binding.BindingKeyWithoutAnnotation('foo'),
            'unused-proviser-fn', 'unusable-scope-id')
        self.assertRaises(errors.BadDependencyScopeError,
                          self.bindable_scopes.get_sub_scope, unusable_binding,
                          binding.new_binding_context())
