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
from pinject import required_bindings


class RequiredBindingsTest(unittest.TestCase):

    def setUp(self):
        self.required_bindings = required_bindings.RequiredBindings()

    def test_initialized_empty(self):
        self.assertEqual([], self.required_bindings.get())

    def test_returns_required_binding(self):
        self.required_bindings.require('an-arg-name', annotated_with='annot')
        [required_binding] = self.required_bindings.get()
        self.assertEqual(
            binding_keys.new('an-arg-name', annotated_with='annot'),
            required_binding.binding_key)
        self.assertIn('required_bindings_test.py', required_binding.require_loc)
