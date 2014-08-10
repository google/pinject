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
import types
import inspect

from pinject import support
from pinject import bindings
from pinject import errors


class VerifyTypeTest(unittest.TestCase):

    def test_verifies_correct_type_ok(self):
        support._verify_type(inspect.ismodule, types, 'unused', 'module')

    def test_raises_exception_if_incorrect_type(self):
        self.assertRaises(errors.WrongArgTypeError, support._verify_type,
                          inspect.ismodule, 'not-a-module',
                          'an-arg-name', 'module')


class VerifyTypesTest(unittest.TestCase):

    def test_verifies_empty_sequence_ok(self):
        def fn_checker(elt):
            return True
        support._verify_types(fn_checker, [], 'unused', 'no_type')

    def test_verifies_correct_type_ok(self):
        support._verify_types(inspect.ismodule, [types], 'unused', 'module')

    def test_raises_exception_if_not_sequence(self):
        self.assertRaises(errors.WrongArgTypeError, support._verify_types,
                          inspect.ismodule, 42, 'an-arg-name', 'module')

    def test_raises_exception_if_element_is_incorrect_type(self):
        self.assertRaises(errors.WrongArgElementTypeError,
                          support._verify_types, inspect.ismodule,
                          ['not-a-module'], 'an-arg-name', 'module')


class VerifySubclassesTest(unittest.TestCase):

    def test_verifies_empty_sequence_ok(self):
        support.verify_subclasses([], bindings.BindingSpec, 'unused')

    def test_verifies_correct_type_ok(self):
        class SomeBindingSpec(bindings.BindingSpec):
            pass
        support.verify_subclasses(
            [SomeBindingSpec()], bindings.BindingSpec, 'unused')

    def test_raises_exception_if_not_sequence(self):
        self.assertRaises(errors.WrongArgTypeError,
                          support.verify_subclasses,
                          42, bindings.BindingSpec, 'an-arg-name')

    def test_raises_exception_if_element_is_not_subclass(self):
        class NotBindingSpec(object):
            pass
        self.assertRaises(
            errors.WrongArgElementTypeError, support.verify_subclasses,
            [NotBindingSpec()], bindings.BindingSpec, 'an-arg-name')


class VerifyCallableTest(unittest.TestCase):

    def test_verifies_callable_ok(self):
        support.verify_callable(lambda: None, 'unused')

    def test_raises_exception_if_not_callable(self):
        self.assertRaises(errors.WrongArgTypeError,
                          support.verify_callable, 42, 'an-arg-name')


class VerifyModuleTypesTest(unittest.TestCase):

    def test_verifies_module_types_ok(self):
        support.verify_module_types([types], 'unused')

    def test_raises_exception_if_not_module_types(self):
        self.assertRaises(errors.WrongArgTypeError,
                          support.verify_module_types, 42, 'an-arg-name')


class VerifyClassTypesTest(unittest.TestCase):

    def test_verifies_module_types_ok(self):
        class Foo(object):
            pass
        support.verify_class_types([Foo], 'unused')

    def test_raises_exception_if_not_class_types(self):
        self.assertRaises(errors.WrongArgTypeError,
                          support.verify_class_types, 42, 'an-arg-name')


class IsSequenceTest(unittest.TestCase):

    def test_argument_identified_as_sequence_instance(self):
        self.assertTrue(support.is_sequence(list()))

    def test_argument_identified_as_not_sequence_instance(self):
        self.assertFalse(support.is_sequence(None))


class IsStringTest(unittest.TestCase):

    def test_argument_identified_as_string_instance(self):
        self.assertTrue(support.is_string('some string'))

    def test_argument_identified_as_not_string_instance(self):
        self.assertFalse(support.is_string(None))


class IsConstructorDefinedTest(unittest.TestCase):

    def test_constructor_present_detection(self):
        class Foo(object):
            def __init__(self):
                pass
        self.assertTrue(support.is_constructor_defined(Foo))

    def test_constructor_not_present_detection(self):
        class Foo(object):
            pass
        self.assertFalse(support.is_constructor_defined(Foo))
