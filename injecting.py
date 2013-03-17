
import inspect
import re
import types

import binding
import errors
import finding


_BINDINGS_ATTR = '_pinject_bindings'
_IS_DECORATOR_ATTR = '_pinject_is_decorator'


def inject(arg_name, with_class=None, with_instance=None, with_provider=None):
    binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
    proviser_fn = binding.create_proviser_fn(
        binding_key, with_class, with_instance, with_provider)
    def get_pinject_decorated_fn(fn):
        if hasattr(fn, _IS_DECORATOR_ATTR):
            pinject_decorated_fn = fn
        else:
            def pinject_decorated_fn(*pargs, **kwargs):
                # TODO(kurts): use functools.update_wrapper
                return fn(*pargs, **kwargs)
            setattr(pinject_decorated_fn, _IS_DECORATOR_ATTR, True)
            setattr(pinject_decorated_fn, _BINDINGS_ATTR, [])
            # TODO(kurts): extract a _pinject_orig_fn constant.
            pinject_decorated_fn._pinject_orig_fn = fn

        arg_names, unused_varargs, unused_keywords, unused_defaults = (
            inspect.getargspec(pinject_decorated_fn._pinject_orig_fn))
        if arg_name not in arg_names:
            raise errors.NoSuchArgToInjectError(arg_name, fn)

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

    # TODO(kurts): inline _provide_class().
    def _provide_class(self, cls, binding_key_stack):
        init_kwargs = {}
        if type(cls.__init__) is types.MethodType:
            if hasattr(cls.__init__, _IS_DECORATOR_ATTR):
                arg_names, unused_varargs, unused_keywords, unused_defaults = (
                    inspect.getargspec(cls.__init__._pinject_orig_fn))
                prebound_bindings = getattr(cls.__init__, _BINDINGS_ATTR)
                for prebound_binding in prebound_bindings:
                    # TODO(kurts): don't peek in BindingKey
                    init_kwargs[prebound_binding.binding_key._arg_name] = (
                        prebound_binding.proviser_fn(binding_key_stack, self))
                prebound_binding_keys = [b.binding_key for b in prebound_bindings]
                arg_names_to_inject = [
                    arg_name for arg_name in _arg_names_without_self(arg_names)
                    if binding.BindingKeyWithoutAnnotation(arg_name) not in prebound_binding_keys]
            else:
                arg_names, unused_varargs, unused_keywords, unused_defaults = (
                    inspect.getargspec(cls.__init__))
                arg_names_to_inject = _arg_names_without_self(arg_names)
            for arg_name in arg_names_to_inject:
                binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
                init_kwargs[arg_name] = self._provide_from_binding_key(
                    binding_key, binding_key_stack)
        return cls(**init_kwargs)

    def wrap(self, fn):
        # TODO(kurts): use functools.update_wrapper().
        # TODO(kurts): use http://micheles.googlecode.com/hg/decorator/documentation.html
        arg_names, unused_varargs, unused_keywords, defaults = inspect.getargspec(fn)
        if defaults is None:
            defaults = []
        injectable_arg_names = arg_names[:(len(arg_names) - len(defaults))]
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


def _arg_names_without_self(args):
    return args[1:]
