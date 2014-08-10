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

from pinject import provider_indirections


class ProviderIndirectionTest(unittest.TestCase):

    def test_returns_provider_fn(self):
        provide_fn = provider_indirections.INDIRECTION.StripIndirectionIfNeeded(
            lambda: 'provided-thing')
        self.assertEqual('provided-thing', provide_fn())


class NoProviderIndirectionTest(unittest.TestCase):

    def test_returns_provided_thing(self):
        self.assertEqual(
            'provided-thing',
            provider_indirections.NO_INDIRECTION.StripIndirectionIfNeeded(
                lambda: 'provided-thing'))
