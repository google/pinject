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

from pinject import binding_keys
from pinject import bindings
from pinject import errors
from pinject import injection_contexts


_UNUSED_INJECTION_SITE_FN = lambda: None


class InjectionContextTest(unittest.TestCase):

    def setUp(self):
        self.binding_key = binding_keys.new('foo')
        self.binding = bindings.new_binding_to_instance(
            self.binding_key, 'an-instance', 'curr-scope',
            lambda: 'unused-desc')
        injection_context_factory = injection_contexts.InjectionContextFactory(
            lambda to_scope, from_scope: to_scope != 'unusable-scope')
        top_injection_context = injection_context_factory.new(
            _UNUSED_INJECTION_SITE_FN)
        self.injection_context = top_injection_context.get_child(
            _UNUSED_INJECTION_SITE_FN, self.binding)

    def test_get_child_successfully(self):
        other_binding_key = binding_keys.new('bar')
        new_injection_context = self.injection_context.get_child(
            _UNUSED_INJECTION_SITE_FN,
            bindings.new_binding_to_instance(
                other_binding_key, 'unused-instance', 'new-scope',
                lambda: 'unused-desc'))

    def test_get_child_raises_error_when_binding_already_seen(self):
        self.assertRaises(errors.CyclicInjectionError,
                          self.injection_context.get_child,
                          _UNUSED_INJECTION_SITE_FN, self.binding)

    def test_get_child_raises_error_when_scope_not_usable(self):
        other_binding_key = binding_keys.new('bar')
        self.assertRaises(
            errors.BadDependencyScopeError, self.injection_context.get_child,
            _UNUSED_INJECTION_SITE_FN,
            bindings.new_binding_to_instance(
                other_binding_key, 'unused-instance', 'unusable-scope',
                lambda: 'unused-desc'))

    def test_get_injection_site_desc(self):
        injection_context_factory = injection_contexts.InjectionContextFactory(
            lambda _1, _2: True)
        def InjectionSite(foo):
            pass
        injection_context = injection_context_factory.new(InjectionSite)
        injection_site_desc = injection_context.get_injection_site_desc()
        self.assertIn('InjectionSite', injection_site_desc)
        self.assertIn('injection_contexts_test.py', injection_site_desc)
