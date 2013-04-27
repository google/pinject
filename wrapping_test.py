
import inspect
import unittest

import binding
import errors
import scoping
import wrapping


# TODO(kurts): have only one FakeInjector for tests.
class FakeInjector(object):

    def provide(self, cls):
        return self._provide_class(cls, _UNUSED_BINDING_CONTEXT)

    def _provide_class(self, cls, binding_context):
        return 'a-provided-{0}'.format(cls.__name__)

    def _provide_from_binding_key(self, binding_key, binding_context):
        return 'provided with {0}'.format(binding_key)

    def _call_with_injection(self, provider_fn, binding_context):
        return provider_fn()


# TODO(kurts): have only one call_provisor_fn() for tests.
_UNUSED_BINDING_CONTEXT = binding.BindingContext('unused', 'unused')
def call_provisor_fn(a_binding):
    return a_binding.proviser_fn(_UNUSED_BINDING_CONTEXT, FakeInjector())


class AnnotateArgTest(unittest.TestCase):

    def test_adds_binding_in_pinject_decorated_fn(self):
        @wrapping.annotate_arg('foo', 'an-annotation')
        def some_function(foo):
            return foo
        self.assertEqual([binding.new_binding_key('foo', 'an-annotation')],
                         [binding_key for binding_key in getattr(some_function,
                                                                 wrapping._ARG_BINDING_KEYS_ATTR)])


class InjectableTest(unittest.TestCase):

    def test_adds_wrapper_to_init(self):
        class SomeClass(object):
            @wrapping.injectable
            def __init__(self, foo):
                return foo
        self.assertTrue(hasattr(SomeClass.__init__, wrapping._IS_WRAPPER_ATTR))

    def test_cannot_be_applied_to_non_init_method(self):
        def do_bad_injectable():
            class SomeClass(object):
                @wrapping.injectable
                def regular_fn(self, foo):
                    return foo
        self.assertRaises(errors.InjectableDecoratorAppliedToNonInitError,
                          do_bad_injectable)

    def test_cannot_be_applied_to_regular_function(self):
        def do_bad_injectable():
            @wrapping.injectable
            def regular_fn(foo):
                return foo
        self.assertRaises(errors.InjectableDecoratorAppliedToNonInitError,
                          do_bad_injectable)


class AnnotatedWithTest(unittest.TestCase):

    def test_sets_annotated_with(self):
        @wrapping.annotated_with('an-annotation')
        def new_foo():
            pass
        provider_fn_binding = wrapping.get_provider_fn_binding(new_foo, 'foo')
        self.assertEqual(binding.new_binding_key('foo', 'an-annotation'),
                         provider_fn_binding.binding_key)

    def test_omitted_leaves_unannotated(self):
        def new_foo():
            pass
        provider_fn_binding = wrapping.get_provider_fn_binding(new_foo, 'foo')
        self.assertEqual(binding.new_binding_key('foo'),
                         provider_fn_binding.binding_key)


class InScopeTest(unittest.TestCase):

    def test_sets_in_scope_id(self):
        @wrapping.in_scope('a-scope-id')
        def new_foo():
            pass
        provider_fn_binding = wrapping.get_provider_fn_binding(new_foo, 'foo')
        self.assertEqual('a-scope-id', provider_fn_binding.scope_id)

    def test_omitted_leaves_unannotated(self):
        def new_foo():
            pass
        provider_fn_binding = wrapping.get_provider_fn_binding(new_foo, 'foo')
        self.assertEqual(scoping.DEFAULT_SCOPE, provider_fn_binding.scope_id)


class GetProviderFnBindingTest(unittest.TestCase):

    def test_proviser_calls_provider_fn(self):
        def new_foo():
            return 'a-foo'
        provider_fn_binding = wrapping.get_provider_fn_binding(new_foo, 'foo')
        self.assertEqual('a-foo', call_provisor_fn(provider_fn_binding))

    # The rest of get_provider_fn_binding() is tested above in conjuction with
    # @annotated_with() and @in_scope().


class AnnotatedWithTest(unittest.TestCase):

    def test_sets_annotated_with(self):
        @wrapping.annotated_with('an-annotation')
        def new_foo():
            pass
        provider_fn_binding = wrapping.get_provider_fn_binding(new_foo, 'foo')
        self.assertEqual(binding.new_binding_key('foo', 'an-annotation'),
                         provider_fn_binding.binding_key)


class GetPinjectWrapperTest(unittest.TestCase):

    def test_sets_recognizable_wrapper_attribute(self):
        @wrapping.annotate_arg('foo', 'an-annotation')
        def some_function(foo):
            return foo
        self.assertTrue(hasattr(some_function, wrapping._IS_WRAPPER_ATTR))

    def test_raises_error_if_referencing_nonexistent_arg(self):
        def do_bad_annotate():
            @wrapping.annotate_arg('foo', 'an-annotation')
            def some_function(bar):
                return bar
        self.assertRaises(errors.NoSuchArgToInjectError, do_bad_annotate)

    def test_reuses_wrapper_fn_when_multiple_wrapping_decorators(self):
        @wrapping.annotate_arg('foo', 'an-annotation')
        @wrapping.annotate_arg('bar', 'an-annotation')
        def some_function(foo, bar):
            return foo + bar
        self.assertEqual([binding.new_binding_key('bar', 'an-annotation'),
                          binding.new_binding_key('foo', 'an-annotation')],
                         [binding_key
                          for binding_key in getattr(some_function,
                                                     wrapping._ARG_BINDING_KEYS_ATTR)])

    def test_raises_error_if_annotating_arg_twice(self):
        def do_bad_annotate():
            @wrapping.annotate_arg('foo', 'an-annotation')
            @wrapping.annotate_arg('foo', 'an-annotation')
            def some_function(foo):
                return foo
        self.assertRaises(errors.MultipleAnnotationsForSameArgError,
                          do_bad_annotate)

    def test_can_call_wrapped_fn_normally(self):
        @wrapping.annotate_arg('foo', 'an-annotation')
        def some_function(foo):
            return foo
        self.assertEqual('an-arg', some_function('an-arg'))

    def test_can_introspect_wrapped_fn(self):
        @wrapping.annotate_arg('foo', 'an-annotation')
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
        self.assertFalse(wrapping.is_explicitly_injectable(SomeClass))

    def test_injectable_class(self):
        class SomeClass(object):
            @wrapping.injectable
            def __init__(self):
                pass
        self.assertTrue(wrapping.is_explicitly_injectable(SomeClass))


class GetInjectableArgBindingKeysTest(unittest.TestCase):

    def assert_fn_has_injectable_arg_binding_keys(self, fn, arg_binding_keys):
        self.assertEqual(
            arg_binding_keys, wrapping.get_injectable_arg_binding_keys(fn))

    def test_fn_with_no_args_returns_nothing(self):
        self.assert_fn_has_injectable_arg_binding_keys(lambda: None, [])

    def test_fn_with_unannotated_arg_returns_unannotated_binding_key(self):
        self.assert_fn_has_injectable_arg_binding_keys(
            lambda foo: None, [binding.new_binding_key('foo')])

    def test_fn_with_annotated_arg_returns_annotated_binding_key(self):
        @wrapping.annotate_arg('foo', 'an-annotation')
        def fn(foo):
            pass
        self.assert_fn_has_injectable_arg_binding_keys(
            fn, [binding.new_binding_key('foo', 'an-annotation')])

    def test_fn_with_arg_with_default_returns_nothing(self):
        self.assert_fn_has_injectable_arg_binding_keys(lambda foo=42: None, [])

    def test_fn_with_mixed_args_returns_mixed_binding_keys(self):
        @wrapping.annotate_arg('foo', 'an-annotation')
        def fn(foo, bar, baz='baz'):
            pass
        self.assert_fn_has_injectable_arg_binding_keys(
            fn, [binding.new_binding_key('foo', 'an-annotation'),
                 binding.new_binding_key('bar')])
