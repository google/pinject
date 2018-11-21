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

from pinject import locations


class ExternalObject(object):
    def a_method(self):
        pass


class GetTypeLocTest(unittest.TestCase):

    def test_known(self):
        class SomeObject(object):
            pass
        self.assertIn('locations_test.py', locations.get_loc(SomeObject))

    def test_unknown(self):
        unknown_class = type('UnknownClass', (object,), {})
        self.assertEqual('unknown location', locations.get_loc(unknown_class))


class GetClassNameAndLocTest(unittest.TestCase):

    def test_known(self):
        class OtherObject(object):
            pass
        class_name_and_loc = locations.get_name_and_loc(OtherObject)
        self.assertIn('OtherObject', class_name_and_loc)
        self.assertIn('locations_test.py', class_name_and_loc)

    def test_known_external(self):
        class_name_and_loc = locations.get_name_and_loc(ExternalObject)
        self.assertIn('ExternalObject', class_name_and_loc)
        self.assertIn('locations_test.py', class_name_and_loc)

    def test_known_unbound_method_as_part_of_class(self):
        class OtherObject(object):
            def a_method(self):
                pass
        class_name_and_loc = locations.get_name_and_loc(OtherObject.a_method)
        self.assertIn('OtherObject.a_method', class_name_and_loc)
        self.assertIn('locations_test.py', class_name_and_loc)

    def test_known_external_unbound_method_as_part_of_class(self):
        class_name_and_loc = locations.get_name_and_loc(ExternalObject.a_method)
        self.assertIn('ExternalObject.a_method', class_name_and_loc)
        self.assertIn('locations_test.py', class_name_and_loc)

    def test_known_bound_method_as_part_of_class(self):
        class OtherObject(object):
            def a_method(self):
                pass
        class_name_and_loc = locations.get_name_and_loc(OtherObject().a_method)
        self.assertIn('OtherObject.a_method', class_name_and_loc)
        self.assertIn('locations_test.py', class_name_and_loc)

    def test_known_external_bound_method_as_part_of_class(self):
        class_name_and_loc = locations.get_name_and_loc(ExternalObject().a_method)
        self.assertIn('ExternalObject.a_method', class_name_and_loc)
        self.assertIn('locations_test.py', class_name_and_loc)

    def test_unknown(self):
        unknown_class = type('UnknownClass', (object,), {})
        class_name_and_loc = locations.get_name_and_loc(unknown_class)
        self.assertEqual('tests.locations_test.UnknownClass', class_name_and_loc)


class GetTypeName(unittest.TestCase):

    def test_get_type_name_unbound_method(self):
        class SomeObject(object):
            def a_method(self):
                pass
        self.assertEqual('SomeObject', locations._get_type_name(SomeObject.a_method))

    def test_get_type_name_external_unbound_method(self):
        self.assertEqual('ExternalObject', locations._get_type_name(ExternalObject.a_method))

    def test_get_type_name_bound_method(self):
        class SomeObject(object):
            def a_method(self):
                pass
        self.assertEqual('SomeObject', locations._get_type_name(SomeObject().a_method))

    def test_get_type_name_external_bound_method(self):
        self.assertEqual('ExternalObject', locations._get_type_name(ExternalObject().a_method))

    def test_get_type_name_function(self):
        def method():
            pass
        self.assertEqual('tests.locations_test', locations._get_type_name(method))


class GetBackFrameLocTest(unittest.TestCase):

    def test_correct_file_and_line(self):
        def get_loc():
            return locations.get_back_frame_loc()
        self.assertIn('locations_test.py', get_loc())
