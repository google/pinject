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
from pinject import bindings
from pinject import binding_keys
from pinject import decorators
from pinject import errors
from pinject import injection_contexts
from pinject import scoping


# TODO(kurts): have only one FakeObjectProvider for tests.
class FakeObjectProvider(object):

    def provide_class(self, cls, injection_context,
                      direct_init_pargs, direct_init_kwargs):
        return 'a-provided-{0}'.format(cls.__name__)

    def provide_from_binding_key(self, binding_key, injection_context):
        return 'provided with {0}'.format(binding_key)

    def call_with_injection(self, provider_fn, injection_context):
        return provider_fn()


class AnnotateArgTest(unittest.TestCase):

    def test_adds_binding_in_pinject_decorated_fn(self):
        @decorators.annotate_arg('foo', 'an-annotation')
        def some_function(foo):
            return foo
        self.assertEqual([arg_binding_keys.new('foo', 'an-annotation')],
                         [binding_key for binding_key in getattr(
                             some_function, decorators._ARG_BINDING_KEYS_ATTR)])


class InjectTest(unittest.TestCase):

    def test_can_set_injectable_arg_names(self):
        @decorators.inject(['foo', 'bar'])
        def some_function(foo, bar):
            pass
        self.assertEqual(
            [],
            getattr(some_function, decorators._NON_INJECTABLE_ARG_NAMES_ATTR))

    def test_can_set_non_injectable_arg_names(self):
        @decorators.inject(all_except=['foo'])
        def some_function(foo, bar):
            pass
        self.assertEqual(
            ['foo'],
            getattr(some_function, decorators._NON_INJECTABLE_ARG_NAMES_ATTR))

    def test_cannot_set_injectable_and_non_injectable_arg_names(self):
        def do_bad_inject():
            @decorators.inject(['foo'], all_except=['bar'])
            def some_function(foo, bar):
                pass
        self.assertRaises(errors.TooManyArgsToInjectDecoratorError,
                          do_bad_inject)

    def test_cannot_set_all_args_non_injectable(self):
        def do_bad_inject():
            @decorators.inject(all_except=['foo', 'bar'])
            def some_function(foo, bar):
                pass
        self.assertRaises(errors.NoRemainingArgsToInjectError, do_bad_inject)

    def test_no_args_means_all_args_are_injectable(self):
        @decorators.inject()
        def some_function(foo, bar):
            pass
        self.assertEqual(
            [],
            getattr(some_function, decorators._NON_INJECTABLE_ARG_NAMES_ATTR))

    def test_arg_names_must_be_sequence(self):
        def do_bad_inject():
            @decorators.inject(arg_names='foo')
            def some_function(foo, bar):
                pass
        self.assertRaises(errors.WrongArgTypeError, do_bad_inject)

    def test_all_except_arg_names_must_be_sequence(self):
        def do_bad_inject():
            @decorators.inject(all_except='foo')
            def some_function(foo, bar):
                pass
        self.assertRaises(errors.WrongArgTypeError, do_bad_inject)

    def test_arg_names_must_be_non_empty_if_specified(self):
        def do_bad_inject():
            @decorators.inject(arg_names=[])
            def some_function(foo, bar):
                pass
        self.assertRaises(errors.EmptySequenceArgError, do_bad_inject)

    def test_all_except_arg_names_must_be_non_empty_if_specified(self):
        def do_bad_inject():
            @decorators.inject(all_except=[])
            def some_function(foo, bar):
                pass
        self.assertRaises(errors.EmptySequenceArgError, do_bad_inject)

    def test_arg_names_must_reference_existing_args(self):
        def do_bad_inject():
            @decorators.inject(arg_names=['bar'])
            def some_function(foo):
                pass
        self.assertRaises(errors.NoSuchArgError, do_bad_inject)

    def test_all_except_arg_names_must_reference_existing_args(self):
        def do_bad_inject():
            @decorators.inject(all_except=['bar'])
            def some_function(foo):
                pass
        self.assertRaises(errors.NoSuchArgError, do_bad_inject)

    def test_cannot_be_applied_twice_to_same_fn(self):
        def do_bad_inject():
            @decorators.inject(['foo'])
            @decorators.inject(['foo'])
            def some_function(foo, bar):
                pass
        self.assertRaises(errors.DuplicateDecoratorError, do_bad_inject)


class InjectableTest(unittest.TestCase):

    def test_adds_wrapper_to_init(self):
        class SomeClass(object):
            @decorators.injectable
            def __init__(self, foo):
                return foo
        self.assertTrue(
            hasattr(SomeClass.__init__, decorators._IS_WRAPPER_ATTR))


class ProvidesTest(unittest.TestCase):

    def test_sets_arg_values(self):
        @decorators.provides('an-arg-name', annotated_with='an-annotation',
                           in_scope='a-scope-id')
        def provide_foo():
            pass
        [provider_fn_binding] = bindings.get_provider_fn_bindings(
            provide_foo, ['foo'])
        self.assertEqual(binding_keys.new('an-arg-name', 'an-annotation'),
                         provider_fn_binding.binding_key)
        self.assertEqual('a-scope-id', provider_fn_binding.scope_id)

    def test_at_least_one_arg_must_be_specified(self):
        def do_bad_annotated_with():
            @decorators.provides()
            def provide_foo():
                pass
        self.assertRaises(errors.EmptyProvidesDecoratorError,
                          do_bad_annotated_with)

    def test_uses_default_binding_when_arg_name_and_annotation_omitted(self):
        @decorators.provides(in_scope='unused')
        def provide_foo(self):
            pass
        [provider_fn_binding] = bindings.get_provider_fn_bindings(
            provide_foo, ['foo'])
        self.assertEqual(binding_keys.new('foo'),
                         provider_fn_binding.binding_key)

    def test_uses_default_scope_when_not_specified(self):
        @decorators.provides('unused')
        def provide_foo(self):
            pass
        [provider_fn_binding] = bindings.get_provider_fn_bindings(
            provide_foo, ['foo'])
        self.assertEqual(scoping.DEFAULT_SCOPE, provider_fn_binding.scope_id)

    def test_multiple_provides_gives_multiple_bindings(self):
        @decorators.provides('foo', annotated_with='foo-annot')
        @decorators.provides('bar', annotated_with='bar-annot')
        def provide_something(self):
            pass
        provider_fn_bindings = bindings.get_provider_fn_bindings(
            provide_something, ['something'])
        self.assertEqual(
            set([binding_keys.new('foo', annotated_with='foo-annot'),
                 binding_keys.new('bar', annotated_with='bar-annot')]),
            set([provider_fn_binding.binding_key
                 for provider_fn_binding in provider_fn_bindings]))


class GetProviderFnDecorationsTest(unittest.TestCase):

    def test_returns_defaults_for_undecorated_fn(self):
        def provide_foo():
            pass
        provider_decorations = decorators.get_provider_fn_decorations(
            provide_foo, ['default-arg-name'])
        self.assertEqual(
            [decorators.ProviderDecoration(
                'default-arg-name', None, scoping.DEFAULT_SCOPE)],
            provider_decorations)

    def test_returns_defaults_if_no_values_set(self):
        @decorators.annotate_arg('bar', 'unused')
        def provide_foo(bar):
            pass
        provider_decorations = decorators.get_provider_fn_decorations(
            provide_foo, ['default-arg-name'])
        self.assertEqual(
            [decorators.ProviderDecoration(
                'default-arg-name', None, scoping.DEFAULT_SCOPE)],
            provider_decorations)

    def test_returns_set_values_if_set(self):
        @decorators.provides('foo', annotated_with='an-annotation',
                             in_scope='a-scope-id')
        def provide_foo():
            pass
        provider_decorations = decorators.get_provider_fn_decorations(
            provide_foo, ['default-arg-name'])
        self.assertEqual(
            [decorators.ProviderDecoration(
                'foo', 'an-annotation', 'a-scope-id')],
            provider_decorations)


class GetPinjectWrapperTest(unittest.TestCase):

    def test_sets_recognizable_wrapper_attribute(self):
        @decorators.annotate_arg('foo', 'an-annotation')
        def some_function(foo):
            return foo
        self.assertTrue(hasattr(some_function, decorators._IS_WRAPPER_ATTR))

    def test_raises_error_if_referencing_nonexistent_arg(self):
        def do_bad_annotate():
            @decorators.annotate_arg('foo', 'an-annotation')
            def some_function(bar):
                return bar
        self.assertRaises(errors.NoSuchArgToInjectError, do_bad_annotate)

    def test_reuses_wrapper_fn_when_multiple_decorators_decorators(self):
        @decorators.annotate_arg('foo', 'an-annotation')
        @decorators.annotate_arg('bar', 'an-annotation')
        def some_function(foo, bar):
            return foo + bar
        self.assertEqual(
            [arg_binding_keys.new('bar', 'an-annotation'),
             arg_binding_keys.new('foo', 'an-annotation')],
            [binding_key
             for binding_key in getattr(some_function,
                                        decorators._ARG_BINDING_KEYS_ATTR)])

    def test_raises_error_if_annotating_arg_twice(self):
        def do_bad_annotate():
            @decorators.annotate_arg('foo', 'an-annotation')
            @decorators.annotate_arg('foo', 'an-annotation')
            def some_function(foo):
                return foo
        self.assertRaises(errors.MultipleAnnotationsForSameArgError,
                          do_bad_annotate)

    def test_can_call_wrapped_fn_normally(self):
        @decorators.annotate_arg('foo', 'an-annotation')
        def some_function(foo):
            return foo
        self.assertEqual('an-arg', some_function('an-arg'))

    def test_can_introspect_wrapped_fn(self):
        @decorators.annotate_arg('foo', 'an-annotation')
        def some_function(foo, bar='BAR', *pargs, **kwargs):
            pass
        arg_names, varargs, keywords, defaults = inspect.getargspec(
            some_function)
        self.assertEqual(['foo', 'bar'], arg_names)
        self.assertEqual('pargs', varargs)
        self.assertEqual('kwargs', keywords)
        self.assertEqual(('BAR',), defaults)


class IsExplicitlyInjectableTest(unittest.TestCase):

    def test_non_injectable_class(self):
        class SomeClass(object):
            pass
        self.assertFalse(decorators.is_explicitly_injectable(SomeClass))

    def test_injectable_class(self):
        class SomeClass(object):
            @decorators.injectable
            def __init__(self):
                pass
        self.assertTrue(decorators.is_explicitly_injectable(SomeClass))


class GetInjectableArgBindingKeysTest(unittest.TestCase):

    def assert_fn_has_injectable_arg_binding_keys(self, fn, arg_binding_keys):
        self.assertEqual(
            arg_binding_keys,
            decorators.get_injectable_arg_binding_keys(fn, [], {}))

    def test_fn_with_no_args_returns_nothing(self):
        self.assert_fn_has_injectable_arg_binding_keys(lambda: None, [])

    def test_fn_with_unannotated_arg_returns_unannotated_binding_key(self):
        self.assert_fn_has_injectable_arg_binding_keys(
            lambda foo: None, [arg_binding_keys.new('foo')])

    def test_fn_with_annotated_arg_returns_annotated_binding_key(self):
        @decorators.annotate_arg('foo', 'an-annotation')
        def fn(foo):
            pass
        self.assert_fn_has_injectable_arg_binding_keys(
            fn, [arg_binding_keys.new('foo', 'an-annotation')])

    def test_fn_with_arg_with_default_returns_nothing(self):
        self.assert_fn_has_injectable_arg_binding_keys(lambda foo=42: None, [])

    def test_fn_with_mixed_args_returns_mixed_binding_keys(self):
        @decorators.annotate_arg('foo', 'an-annotation')
        def fn(foo, bar, baz='baz'):
            pass
        self.assert_fn_has_injectable_arg_binding_keys(
            fn, [arg_binding_keys.new('foo', 'an-annotation'),
                 arg_binding_keys.new('bar')])
