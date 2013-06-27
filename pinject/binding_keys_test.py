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

from pinject import annotations
from pinject import binding_keys


class BindingKeyTest(unittest.TestCase):

    def test_repr(self):
        binding_key = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('an-annotation'))
        self.assertEqual(
            '<the binding name "an-arg-name" (annotated with "an-annotation")>',
            repr(binding_key))

    def test_str(self):
        binding_key = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('an-annotation'))
        self.assertEqual(
            'the binding name "an-arg-name" (annotated with "an-annotation")',
            str(binding_key))

    def test_annotation_as_adjective(self):
        binding_key = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('an-annotation'))
        self.assertEqual('annotated with "an-annotation"',
                         binding_key.annotation_as_adjective())

    def test_equal_if_same_arg_name_and_annotation(self):
        binding_key_one = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('an-annotation'))
        binding_key_two = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('an-annotation'))
        self.assertEqual(binding_key_one, binding_key_two)
        self.assertEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertEqual(str(binding_key_one), str(binding_key_two))

    def test_unequal_if_not_same_arg_name(self):
        binding_key_one = binding_keys.BindingKey(
            'arg-name-one', annotations.Annotation('an-annotation'))
        binding_key_two = binding_keys.BindingKey(
            'arg-name-two', annotations.Annotation('an-annotation'))
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))

    def test_unequal_if_not_same_annotation(self):
        binding_key_one = binding_keys.BindingKey(
            'arg-name-one', annotations.Annotation('an-annotation'))
        binding_key_two = binding_keys.BindingKey(
            'arg-name-two', annotations.Annotation('another-annotation'))
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))


class NewBindingKeyTest(unittest.TestCase):

    def test_without_annotation(self):
        binding_key = binding_keys.new('an-arg-name')
        self.assertEqual('the binding name "an-arg-name" (unannotated)',
                         str(binding_key))

    def test_with_annotation(self):
        binding_key = binding_keys.new('an-arg-name', 'an-annotation')
        self.assertEqual(
            'the binding name "an-arg-name" (annotated with "an-annotation")',
            str(binding_key))
