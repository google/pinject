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

import binding_keys
import bindings
import injection_contexts
import errors


class InjectionContextTest(unittest.TestCase):

    def setUp(self):
        self.binding_key = binding_keys.new('foo')
        injection_context_factory = injection_contexts.InjectionContextFactory(
            lambda to_scope, from_scope: to_scope != 'unusable-scope')
        top_injection_context = injection_context_factory.new()
        self.injection_context = top_injection_context.get_child(
            bindings.Binding(self.binding_key, 'unused-proviser-fn',
                             'curr-scope', 'unused-desc'))

    def test_get_child_successfully(self):
        other_binding_key = binding_keys.new('bar')
        new_injection_context = self.injection_context.get_child(
            bindings.Binding(other_binding_key, 'unused-proviser-fn',
                             'new-scope', 'unused-desc'))

    def test_get_child_raises_error_when_binding_key_already_seen(self):
        self.assertRaises(
            errors.CyclicInjectionError, self.injection_context.get_child,
            bindings.Binding(self.binding_key, 'unused-proviser-fn',
                             'new-scope', 'unused-desc'))

    def test_get_child_raises_error_when_scope_not_usable(self):
        other_binding_key = binding_keys.new('bar')
        self.assertRaises(
            errors.BadDependencyScopeError, self.injection_context.get_child,
            bindings.Binding(other_binding_key, 'unused-proviser-fn',
                             'unusable-scope', 'unused-desc'))
