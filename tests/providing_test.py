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

from pinject import providing


class DefaultGetArgNamesFromProviderFnNameTest(unittest.TestCase):

    def test_non_provider_prefix_returns_nothing(self):
        self.assertEqual([],
                         providing.default_get_arg_names_from_provider_fn_name(
                             'some_foo'))

    def test_single_part_name_returned_as_is(self):
        self.assertEqual(['foo'],
                         providing.default_get_arg_names_from_provider_fn_name(
                             'provide_foo'))

    def test_multiple_part_name_returned_as_is(self):
        self.assertEqual(['foo_bar'],
                         providing.default_get_arg_names_from_provider_fn_name(
                             'provide_foo_bar'))
