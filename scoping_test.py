
import unittest

import binding
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
