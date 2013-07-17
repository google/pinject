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
from pinject import arg_binding_keys
from pinject import binding_keys
from pinject import provider_indirections


class ArgBindingKeyTest(unittest.TestCase):

    def test_repr(self):
        arg_binding_key = arg_binding_keys.ArgBindingKey(
            'an-arg-name', binding_keys.new('an-arg-name', 'an-annotation'),
            provider_indirections.INDIRECTION)
        self.assertEqual(
            '<the arg named "an-arg-name" annotated with "an-annotation">',
            repr(arg_binding_key))

    def test_str(self):
        arg_binding_key = arg_binding_keys.ArgBindingKey(
            'an-arg-name', binding_keys.new('an-arg-name', 'an-annotation'),
            provider_indirections.INDIRECTION)
        self.assertEqual(
            'the arg named "an-arg-name" annotated with "an-annotation"',
            str(arg_binding_key))

    def test_equal_if_same_field_values(self):
        arg_binding_key_one = arg_binding_keys.ArgBindingKey(
            'an-arg-name', binding_keys.new('an-arg-name', 'an-annotation'),
            provider_indirections.INDIRECTION)
        arg_binding_key_two = arg_binding_keys.ArgBindingKey(
            'an-arg-name', binding_keys.new('an-arg-name', 'an-annotation'),
            provider_indirections.INDIRECTION)
        self.assertEqual(arg_binding_key_one, arg_binding_key_two)
        self.assertEqual(hash(arg_binding_key_one), hash(arg_binding_key_two))
        self.assertEqual(str(arg_binding_key_one), str(arg_binding_key_two))

    def test_unequal_if_not_same_arg_name(self):
        arg_binding_key_one = arg_binding_keys.ArgBindingKey(
            'an-arg-name', binding_keys.new('an-arg-name', 'an-annotation'),
            provider_indirections.INDIRECTION)
        arg_binding_key_two = arg_binding_keys.ArgBindingKey(
            'other-arg-name',
            binding_keys.new('other-arg-name', 'an-annotation'),
            provider_indirections.INDIRECTION)
        self.assertNotEqual(arg_binding_key_one, arg_binding_key_two)
        self.assertNotEqual(hash(arg_binding_key_one),
                            hash(arg_binding_key_two))
        self.assertNotEqual(str(arg_binding_key_one), str(arg_binding_key_two))

    def test_unequal_if_not_same_annotation(self):
        arg_binding_key_one = arg_binding_keys.ArgBindingKey(
            'an-arg-name', binding_keys.new('an-arg-name', 'an-annotation'),
            provider_indirections.INDIRECTION)
        arg_binding_key_two = arg_binding_keys.ArgBindingKey(
            'an-arg-name', binding_keys.new('an-arg-name', 'other-annotation'),
            provider_indirections.INDIRECTION)
        self.assertNotEqual(arg_binding_key_one, arg_binding_key_two)
        self.assertNotEqual(hash(arg_binding_key_one),
                            hash(arg_binding_key_two))
        self.assertNotEqual(str(arg_binding_key_one), str(arg_binding_key_two))

    def test_unequal_if_not_same_indirection(self):
        arg_binding_key_one = arg_binding_keys.ArgBindingKey(
            'an-arg-name', binding_keys.new('an-arg-name', 'an-annotation'),
            provider_indirections.INDIRECTION)
        arg_binding_key_two = arg_binding_keys.ArgBindingKey(
            'an-arg-name', binding_keys.new('an-arg-name', 'an-annotation'),
            provider_indirections.NO_INDIRECTION)
        self.assertNotEqual(arg_binding_key_one, arg_binding_key_two)
        self.assertNotEqual(hash(arg_binding_key_one),
                            hash(arg_binding_key_two))
        # Strings will be equal, since indirection isn't part of the string.
        self.assertEqual(str(arg_binding_key_one), str(arg_binding_key_two))

    def test_can_apply_to_one_of_arg_names(self):
        arg_binding_key = arg_binding_keys.new(
            'an-arg-name', 'unused-binding-key')
        self.assertTrue(arg_binding_key.can_apply_to_one_of_arg_names(
            ['foo', 'an-arg-name', 'bar']))

    def test_cannot_apply_to_one_of_arg_names(self):
        arg_binding_key = arg_binding_keys.new(
            'an-arg-name', 'unused-binding-key')
        self.assertFalse(arg_binding_key.can_apply_to_one_of_arg_names(
            ['foo', 'other-arg-name', 'bar']))

    def test_conflicts_with_some_arg_binding_key(self):
        arg_binding_key = arg_binding_keys.new(
            'an-arg-name', 'unused-binding-key')
        non_conflicting_arg_binding_key = arg_binding_keys.new(
            'other-arg-name', 'unused-binding-key')
        conflicting_arg_binding_key = arg_binding_keys.new(
            'an-arg-name', 'unused-binding-key')
        self.assertTrue(arg_binding_key.conflicts_with_any_arg_binding_key(
            [non_conflicting_arg_binding_key, conflicting_arg_binding_key]))

    def test_doesnt_conflict_with_any_binding_key(self):
        arg_binding_key = arg_binding_keys.new(
            'an-arg-name', 'unused-binding-key')
        non_conflicting_arg_binding_key = arg_binding_keys.new(
            'other-arg-name', 'unused-binding-key')
        self.assertFalse(arg_binding_key.conflicts_with_any_arg_binding_key(
            [non_conflicting_arg_binding_key]))


class GetUnboundArgNamesTest(unittest.TestCase):

    def test_all_arg_names_bound(self):
        self.assertEqual(
            [],
            arg_binding_keys.get_unbound_arg_names(
                ['bound1', 'bound2'],
                [arg_binding_keys.new('bound1'),
                 arg_binding_keys.new('bound2')]))

    def test_some_arg_name_unbound(self):
        self.assertEqual(
            ['unbound'],
            arg_binding_keys.get_unbound_arg_names(
                ['bound', 'unbound'], [arg_binding_keys.new('bound')]))


class CreateKwargsTest(unittest.TestCase):

    def test_returns_nothing_for_no_input(self):
        self.assertEqual(
            {}, arg_binding_keys.create_kwargs([], provider_fn=None))

    def test_returns_provided_value_for_arg(self):
        def ProviderFn(arg_binding_key):
            return ('an-arg-value'
                    if arg_binding_key == arg_binding_keys.new('an-arg')
                    else None)
        self.assertEqual(
            {'an-arg': 'an-arg-value'},
            arg_binding_keys.create_kwargs([arg_binding_keys.new('an-arg')],
                                           ProviderFn))


class NewArgBindingKeyTest(unittest.TestCase):

    def test_with_no_bells_or_whistles(self):
        arg_binding_key = arg_binding_keys.new('an-arg-name')
        self.assertEqual('the arg named "an-arg-name" unannotated',
                         str(arg_binding_key))

    def test_with_annotation(self):
        arg_binding_key = arg_binding_keys.new('an-arg-name', 'an-annotation')
        self.assertEqual(
            'the arg named "an-arg-name" annotated with "an-annotation"',
            str(arg_binding_key))

    def test_as_provider_fn(self):
        arg_binding_key = arg_binding_keys.new('provide_foo')
        self.assertEqual('the arg named "provide_foo" unannotated',
                         str(arg_binding_key))
