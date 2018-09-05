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

from pinject import arg_binding_keys
from pinject import binding_keys
from pinject import bindings
from pinject import decorators
from pinject import errors
from pinject import injection_contexts
from pinject import object_providers
from pinject import scoping


def new_test_obj_provider(arg_binding_key, instance, allow_injecting_none=True):
    binding_key = arg_binding_key.binding_key
    binding = bindings.new_binding_to_instance(
        binding_key, instance, 'a-scope', lambda: 'unused-desc')
    binding_mapping = bindings.BindingMapping({binding_key: binding}, {})
    bindable_scopes = scoping.BindableScopes(
        {'a-scope': scoping.PrototypeScope()})
    return object_providers.ObjectProvider(
        binding_mapping, bindable_scopes, allow_injecting_none)


def new_injection_context():
    return injection_contexts.InjectionContextFactory(lambda _1, _2: True).new(
        lambda: None)


_UNUSED_INJECTION_SITE_FN = lambda: None


class ObjectProviderTest(unittest.TestCase):

    def test_provides_from_arg_binding_key_successfully(self):
        arg_binding_key = arg_binding_keys.new('an-arg-name')
        obj_provider = new_test_obj_provider(arg_binding_key, 'an-instance')
        self.assertEqual('an-instance',
                         obj_provider.provide_from_arg_binding_key(
                             _UNUSED_INJECTION_SITE_FN,
                             arg_binding_key, new_injection_context()))

    def test_provides_provider_fn_from_arg_binding_key_successfully(self):
        arg_binding_key = arg_binding_keys.new('provide_foo')
        obj_provider = new_test_obj_provider(arg_binding_key, 'an-instance')
        provide_fn = obj_provider.provide_from_arg_binding_key(
            _UNUSED_INJECTION_SITE_FN,
            arg_binding_key, new_injection_context())
        self.assertEqual('an-instance', provide_fn())

    def test_can_provide_none_from_arg_binding_key_when_allowed(self):
        arg_binding_key = arg_binding_keys.new('an-arg-name')
        obj_provider = new_test_obj_provider(arg_binding_key, None)
        self.assertIsNone(obj_provider.provide_from_arg_binding_key(
            _UNUSED_INJECTION_SITE_FN,
            arg_binding_key, new_injection_context()))

    def test_cannot_provide_none_from_binding_key_when_disallowed(self):
        arg_binding_key = arg_binding_keys.new('an-arg-name')
        obj_provider = new_test_obj_provider(arg_binding_key, None,
                                             allow_injecting_none=False)
        self.assertRaises(errors.InjectingNoneDisallowedError,
                          obj_provider.provide_from_arg_binding_key,
                          _UNUSED_INJECTION_SITE_FN,
                          arg_binding_key, new_injection_context())

    def test_provides_class_with_init_as_method_injects_args_successfully(self):
        class Foo(object):
            def __init__(self, bar):
                self.bar = bar
        arg_binding_key = arg_binding_keys.new('bar')
        obj_provider = new_test_obj_provider(arg_binding_key, 'a-bar')
        foo = obj_provider.provide_class(Foo, new_injection_context(), [], {})
        self.assertEqual('a-bar', foo.bar)

    def test_provides_class_with_direct_pargs_and_kwargs(self):
        class SomeClass(object):
            @decorators.inject(['baz'])
            def __init__(self, foo, bar, baz):
                self.foobarbaz = foo + bar + baz
        obj_provider = new_test_obj_provider(arg_binding_keys.new('baz'), 'baz')
        some_class = obj_provider.provide_class(
            SomeClass, new_injection_context(), ['foo'], {'bar': 'bar'})
        self.assertEqual('foobarbaz', some_class.foobarbaz)

    def test_provides_class_with_init_as_method_wrapper_successfully(self):
        class Foo(object):
            pass
        arg_binding_key = arg_binding_keys.new('unused')
        obj_provider = new_test_obj_provider(arg_binding_key, 'unused')
        self.assertIsInstance(
            obj_provider.provide_class(Foo, new_injection_context(), [], {}),
            Foo)

    def test_calls_with_injection_successfully(self):
        def foo(bar):
            return 'a-foo-and-' + bar
        arg_binding_key = arg_binding_keys.new('bar')
        obj_provider = new_test_obj_provider(arg_binding_key, 'a-bar')
        self.assertEqual('a-foo-and-a-bar',
                         obj_provider.call_with_injection(
                             foo, new_injection_context(), [], {}))

    def test_gets_injection_kwargs_successfully(self):
        def foo(bar):
            pass
        arg_binding_key = arg_binding_keys.new('bar')
        obj_provider = new_test_obj_provider(arg_binding_key, 'a-bar')
        pargs, kwargs = obj_provider.get_injection_pargs_kwargs(
            foo, new_injection_context(), [], {})
        self.assertEqual([], pargs)
        self.assertEqual({'bar': 'a-bar'}, kwargs)
