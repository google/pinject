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

import annotations
import binding_keys


class BindingKeyTest(unittest.TestCase):

    def test_repr(self):
        binding_key = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('an-annotation'))
        self.assertEqual('<the arg name "an-arg-name" annotated with "an-annotation">',
                         repr(binding_key))

    def test_str(self):
        binding_key = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('an-annotation'))
        self.assertEqual('the arg name "an-arg-name" annotated with "an-annotation"',
                         str(binding_key))

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

    def test_can_apply_to_one_of_arg_names(self):
        binding_key = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('unused'))
        self.assertTrue(binding_key.can_apply_to_one_of_arg_names(
            ['foo', 'an-arg-name', 'bar']))

    def test_cannot_apply_to_one_of_arg_names(self):
        binding_key = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('unused'))
        self.assertFalse(binding_key.can_apply_to_one_of_arg_names(
            ['foo', 'other-arg-name', 'bar']))

    def test_conflicts_with_some_binding_key(self):
        binding_key = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('ann1'))
        non_conflicting_binding_key = binding_keys.BindingKey(
            'other-arg-name', annotations.Annotation('unused'))
        conflicting_binding_key = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('ann2'))
        self.assertTrue(binding_key.conflicts_with_any_binding_key(
            [non_conflicting_binding_key, conflicting_binding_key]))

    def test_doesnt_conflict_with_any_binding_key(self):
        binding_key = binding_keys.BindingKey(
            'an-arg-name', annotations.Annotation('ann1'))
        non_conflicting_binding_key = binding_keys.BindingKey(
            'other-arg-name', annotations.Annotation('unused'))
        self.assertFalse(binding_key.conflicts_with_any_binding_key(
            [non_conflicting_binding_key]))


class GetUnboundArgNamesTest(unittest.TestCase):

    def test_all_arg_names_bound(self):
        self.assertEqual(
            [],
            binding_keys.get_unbound_arg_names(
                ['bound1', 'bound2'],
                [binding_keys.new('bound1'), binding_keys.new('bound2')]))

    def test_some_arg_name_unbound(self):
        self.assertEqual(
            ['unbound'],
            binding_keys.get_unbound_arg_names(
                ['bound', 'unbound'], [binding_keys.new('bound')]))


class CreateKwargsTest(unittest.TestCase):

    def test_returns_nothing_for_no_input(self):
        self.assertEqual({}, binding_keys.create_kwargs([], provider_fn=None))

    def test_returns_provided_value_for_arg(self):
        def ProviderFn(binding_key):
            return ('an-arg-value' if binding_key == binding_keys.new('an-arg')
                    else None)
        self.assertEqual(
            {'an-arg': 'an-arg-value'},
            binding_keys.create_kwargs([binding_keys.new('an-arg')],
                                       ProviderFn))


class NewBindingKeyTest(unittest.TestCase):

    def test_without_annotation(self):
        binding_key = binding_keys.new('an-arg-name')
        self.assertEqual('the arg name "an-arg-name" unannotated', str(binding_key))

    def test_with_annotation(self):
        binding_key = binding_keys.new('an-arg-name', 'an-annotation')
        self.assertEqual('the arg name "an-arg-name" annotated with "an-annotation"',
                         str(binding_key))
