
import functools
import inspect
import re
import types

# From http://micheles.googlecode.com/hg/decorator/documentation.html
import decorator

import binding
import errors
import finding


_BINDINGS_ATTR = '_pinject_bindings'
_IS_DECORATOR_ATTR = '_pinject_is_decorator'
_ORIG_FN_ATTR = '_pinject_orig_fn'


def annotate(arg_name, annotation):
    binding_key = binding.BindingKeyWithAnnotation(arg_name, annotation)
    proviser_fn = lambda binding_key_stack, injector: (
        injector._provide_from_binding_key(binding_key, binding_key_stack))
    return _get_pinject_decorator(binding_key, proviser_fn)


def inject(arg_name, with_class=None, with_instance=None, with_provider=None):
    binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
    proviser_fn = binding.create_proviser_fn(
        binding_key, with_class, with_instance, with_provider)
    return _get_pinject_decorator(binding_key, proviser_fn)


def _get_pinject_decorator(binding_key, proviser_fn):
    def get_pinject_decorated_fn(fn):
        if hasattr(fn, _IS_DECORATOR_ATTR):
            pinject_decorated_fn = fn
        else:
            def _pinject_decorated_fn(fn_to_wrap, *pargs, **kwargs):
                return fn_to_wrap(*pargs, **kwargs)
            pinject_decorated_fn = decorator.decorator(_pinject_decorated_fn, fn)
            setattr(pinject_decorated_fn, _IS_DECORATOR_ATTR, True)
            setattr(pinject_decorated_fn, _BINDINGS_ATTR, [])
            setattr(pinject_decorated_fn, _ORIG_FN_ATTR, fn)

        arg_names, unused_varargs, unused_keywords, unused_defaults = (
            inspect.getargspec(getattr(pinject_decorated_fn, _ORIG_FN_ATTR)))
        if binding_key.arg_name not in arg_names:
            raise errors.NoSuchArgToInjectError(binding_key.arg_name, fn)

        getattr(pinject_decorated_fn, _BINDINGS_ATTR).append(
            binding.Binding(binding_key, proviser_fn))
        return pinject_decorated_fn
    return get_pinject_decorated_fn


def new_injector(modules=None, classes=None,
                 get_arg_names_from_class_name=binding.default_get_arg_names_from_class_name,
                 binding_fns=None):
    explicit_bindings = []
    binder = binding.Binder(explicit_bindings)
    if binding_fns is not None:
        for binding_fn in binding_fns:
            binding_fn(bind=binder.bind)

    classes = finding.FindClasses(modules, classes)
    implicit_bindings = binding.get_implicit_bindings(
        classes, get_arg_names_from_class_name)
    binding_mapping = binding.new_binding_mapping(
        explicit_bindings, implicit_bindings)

    injector = _Injector(binding_mapping)
    return injector


class _Injector(object):

    def __init__(self, binding_mapping):
        self._binding_mapping = binding_mapping

    def provide(self, cls):
        return self._provide_class(cls, binding_key_stack=[])

    def _provide_from_binding_key(self, binding_key, binding_key_stack):
        binding_key_stack.append(binding_key)
        if binding_key in binding_key_stack[:-1]:
            raise errors.CyclicInjectionError(binding_key_stack)
        try:
            # TODO(kurts): make a reasonable error message if the mapping raises.
            return self._binding_mapping.get_instance(binding_key, binding_key_stack, self)
        finally:
            binding_key_stack.pop()

    def _provide_class(self, cls, binding_key_stack):
        if type(cls.__init__) is types.MethodType:
            init_kwargs = self._get_injection_kwargs(
                cls.__init__, binding_key_stack)
        else:
            init_kwargs = {}
        return cls(**init_kwargs)

    # TODO(kurts): what's the use case for this, really?  Provider functions
    # are already injected by default.  Functional programming?
    def wrap(self, fn):
        # This has to return a function with a different signature (and can't
        # use @decorator) since otherwise python would require the caller to
        # pass in all positional args that have no defaults, instead of
        # letting those be injected if they're not passed in.
        arg_names, unused_varargs, unused_keywords, defaults = inspect.getargspec(fn)
        if defaults is None:
            defaults = []
        injectable_arg_names = arg_names[:(len(arg_names) - len(defaults))]
        @functools.wraps(fn)
        def WrappedFn(*pargs, **kwargs):
            injected_arg_names = [
                arg_name for index, arg_name in enumerate(injectable_arg_names)
                if index >= len(pargs) and arg_name not in kwargs]
            if injected_arg_names:
                kwargs = dict(kwargs)
                for arg_name in injected_arg_names:
                    kwargs[arg_name] = self._provide_from_binding_key(
                        binding.BindingKeyWithoutAnnotation(arg_name),
                        binding_key_stack=[])
            return fn(*pargs, **kwargs)
        return WrappedFn

    def _call_with_injection(self, provider_fn, binding_key_stack):
        kwargs = self._get_injection_kwargs(provider_fn, binding_key_stack)
        return provider_fn(**kwargs)

    def _get_injection_kwargs(self, fn, binding_key_stack):
        kwargs = {}
        # TODO(kurts): extract all this pinject-decorated fn stuff to a
        # common place.
        if hasattr(fn, _IS_DECORATOR_ATTR):
            arg_names, unused_varargs, unused_keywords, unused_defaults = (
                inspect.getargspec(getattr(fn, _ORIG_FN_ATTR)))
            prebound_bindings = getattr(fn, _BINDINGS_ATTR)
            for prebound_binding in prebound_bindings:
                kwargs[prebound_binding.binding_key.arg_name] = (
                    prebound_binding.proviser_fn(binding_key_stack, self))
            prebound_arg_names = [b.binding_key.arg_name for b in prebound_bindings]
            arg_names_to_inject = [
                arg_name for arg_name in _remove_self_if_exists(arg_names)
                if arg_name not in prebound_arg_names]
        else:
            arg_names, unused_varargs, unused_keywords, unused_defaults = (
                inspect.getargspec(fn))
            arg_names_to_inject = _remove_self_if_exists(arg_names)
        for arg_name in arg_names_to_inject:
            binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
            kwargs[arg_name] = self._provide_from_binding_key(
                binding_key, binding_key_stack)
        return kwargs


# TODO(kurts): this feels icky.  Is there no way around this, because
# cls.__init__() takes self but instance.__init__() doesn't, and python is
# awkward here?
def _remove_self_if_exists(args):
    if args and args[0] == 'self':
        return args[1:]
    else:
        return args
