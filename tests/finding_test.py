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


import inspect
import mock
import sys
import unittest

from pinject import finding


cvar = "Mock SWIG cvar attribute."
foo = "some other mock attribute"

class FindClassesTest(unittest.TestCase):

    def test_finds_passed_in_classes(self):
        class SomeClass(object):
            pass
        self.assertIn(SomeClass,
                      finding.find_classes(modules=None, classes=[SomeClass]))

    def test_finds_classes_in_passed_in_modules(self):
        this_module = sys.modules[FindClassesTest.__module__]
        self.assertIn(FindClassesTest,
                      finding.find_classes(modules=[this_module], classes=None))

    def test_returns_class_once_even_if_passed_in_multiple_times(self):
        this_module = sys.modules[FindClassesTest.__module__]
        self.assertIn(
            FindClassesTest,
            finding.find_classes(modules=[this_module, this_module],
                                 classes=[FindClassesTest, FindClassesTest]))

    def test_reads_sys_modules_for_all_imported_modules(self):
        self.assertIn(
            FindClassesTest,
            finding.find_classes(modules=finding.ALL_IMPORTED_MODULES,
                                 classes=None))

    def test_swig_cvar_nameerror(self):
        this_module = sys.modules[FindClassesTest.__module__]
        # This tests a special case exception that find_classes silences, which
        # originates from calling isinstance on SWIG's global cvar raises a
        # NameError in python 3. To avoid recursion from mocking the builtin,
        # we mock inspect.isclass while holding onto a reference to the actual
        # function.
        isclass = inspect.isclass

        # Tests that the right error is silenced.
        def cvar_raises_nameerror(value):
            if value == cvar:
                raise NameError()
            return isclass(value)
        with mock.patch.object(inspect, 'isclass') as mock_isclass:
            mock_isclass.side_effect = cvar_raises_nameerror
            self.assertNotIn(cvar,
                    finding.find_classes(modules=[this_module], classes=None))

        # Tests that the wrong error type is let through.
        def cvar_raises_valueerror(value):
            if value == cvar:
                raise ValueError()
            return isclass(value)
        with mock.patch.object(inspect, 'isclass') as mock_isclass:
            mock_isclass.side_effect = cvar_raises_valueerror
            with self.assertRaises(ValueError):
                finding.find_classes(modules=[this_module], classes=None)

        # Tests that an error relating to another attribute is let through.
        def foo_raises_nameerror(value):
            if value == foo:
                raise NameError()
            return isclass(value)
        with mock.patch.object(inspect, 'isclass') as mock_isclass:
            mock_isclass.side_effect = foo_raises_nameerror
            with self.assertRaises(NameError):
                finding.find_classes(modules=[this_module], classes=None)
