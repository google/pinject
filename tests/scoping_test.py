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


import unittest

from pinject import bindings
from pinject import binding_keys
from pinject import errors
from pinject import scoping


class PrototypeScopeTest(unittest.TestCase):

    def test_always_calls_provider_fn(self):
        next_provided = [0]
        def provider_fn():
            provided = next_provided[0]
            next_provided[0] += 1
            return provided
        scope = scoping.PrototypeScope()
        binding_key = binding_keys.new('unused')
        self.assertEqual(
            range(10),
            [scope.provide(binding_key, provider_fn) for _ in xrange(10)])


class SingletonScopeTest(unittest.TestCase):

    def setUp(self):
        self.scope = scoping.SingletonScope()
        self.binding_key_one = binding_keys.new('one')
        self.binding_key_two = binding_keys.new('two')
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
        self.bindable_scopes = scoping.BindableScopes(
            {'usable-scope-id': 'usable-scope'})

    def test_get_sub_scope_successfully(self):
        usable_binding = bindings.new_binding_to_instance(
            binding_keys.new('foo'), 'unused-instance', 'usable-scope-id',
            lambda: 'unused-desc')
        self.assertEqual(
            'usable-scope', self.bindable_scopes.get_sub_scope(usable_binding))
