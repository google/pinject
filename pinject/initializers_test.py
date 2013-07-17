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
import unittest

from pinject import errors
from pinject import initializers


class CopyArgsToInternalFieldsTest(unittest.TestCase):

    def test_does_nothing_extra_for_zero_arg_initializer(self):
        class SomeClass(object):
            @initializers.copy_args_to_internal_fields
            def __init__(self):
                self.forty_two = 42
        self.assertEqual(42, SomeClass().forty_two)

    def test_copies_positional_arg_to_internal_field(self):
        class SomeClass(object):
            @initializers.copy_args_to_internal_fields
            def __init__(self, foo):
                pass
        self.assertEqual('foo', SomeClass('foo')._foo)

    def test_copies_keyword_arg_to_internal_field(self):
        class SomeClass(object):
            @initializers.copy_args_to_internal_fields
            def __init__(self, foo):
                pass
        self.assertEqual('foo', SomeClass(foo='foo')._foo)

    def test_copies_kwargs_to_internal_fields(self):
        class SomeClass(object):
            @initializers.copy_args_to_internal_fields
            def __init__(self, **kwargs):
                pass
        self.assertEqual('foo', SomeClass(foo='foo')._foo)

    def test_raises_exception_if_keyword_arg_unknown(self):
        class SomeClass(object):
            @initializers.copy_args_to_internal_fields
            def __init__(self, bar):
                pass
        self.assertRaises(TypeError, SomeClass, foo='foo')

    def test_maintains_signature(self):
        class SomeClass(object):
            @initializers.copy_args_to_internal_fields
            def __init__(self, foo):
                pass
        self.assertEqual('__init__', SomeClass.__init__.__name__)
        arg_names, unused_varargs, unused_keywords, unused_defaults = (
            inspect.getargspec(SomeClass.__init__))
        self.assertEqual(['self', 'foo'], arg_names)

    def test_raises_exception_if_init_takes_pargs(self):
        def do_bad_initializer():
            class SomeClass(object):
                @initializers.copy_args_to_internal_fields
                def __init__(self, *pargs):
                    pass
        self.assertRaises(errors.PargsDisallowedWhenCopyingArgsError,
                          do_bad_initializer)

    def test_raises_exception_if_not_applied_to_init(self):
        def do_bad_decorated_fn():
            @initializers.copy_args_to_internal_fields
            def some_function(foo, bar):
                pass
        self.assertRaises(errors.DecoratorAppliedToNonInitError,
                          do_bad_decorated_fn)


class CopyArgsToPublicFieldsTest(unittest.TestCase):

    def test_uses_no_field_prefix(self):
        class SomeClass(object):
            @initializers.copy_args_to_public_fields
            def __init__(self, foo):
                pass
        self.assertEqual('foo', SomeClass('foo').foo)

    # Other functionality is tested as part of testing
    # copy_args_to_internal_fields().
