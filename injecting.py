
import inspect
import re

import binding
import errors
import finding


def inject(arg_name, with_class=None, with_instance=None, with_provider=None):
    binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
    proviser_fn = binding.create_proviser_fn(
        binding_key, with_class, with_instance, with_provider)
    def get_pinject_decorated_fn(fn):
        if hasattr(fn, '_pinject_is_decorator'):
            pinject_decorated_fn = fn
        else:
            def pinject_decorated_fn(*pargs, **kwargs):
                # TODO(kurts): use functools.update_wrapper
                return fn(*pargs, **kwargs)
            pinject_decorated_fn._pinject_is_decorator = True
            pinject_decorated_fn._pinject_bindings = []
            pinject_decorated_fn._pinject_orig_fn = fn

        arg_names, unused_varargs, unused_keywords, unused_defaults = (
            inspect.getargspec(pinject_decorated_fn._pinject_orig_fn))
        if arg_name not in arg_names:
            raise errors.NoSuchArgToInjectError(arg_name, fn)

        pinject_decorated_fn._pinject_bindings.append(
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

    def _provide_arg(self, arg_name, binding_key_stack):
        binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
        binding_key_stack.append(binding_key)
        if binding_key in binding_key_stack[:-1]:
            raise errors.CyclicInjectionError(binding_key_stack)
        try:
            # TODO(kurts): make a reasonable error message if the mapping raises.
            return self._binding_mapping.get_instance(binding_key, binding_key_stack, self)
        finally:
            binding_key_stack.pop()

    def _provide_class(self, cls, binding_key_stack):
        init_kwargs = {}
        # TODO(kurts): this hard-coding feels strange.  Is there any way to
        # get all such cases?
        if cls.__init__ not in (object.__init__, Exception.__init__):
            arg_names, unused_varargs, unused_keywords, unused_defaults = inspect.getargspec(cls.__init__)
            for arg_name in _arg_names_without_self(arg_names):
                init_kwargs[arg_name] = self._provide_arg(arg_name, binding_key_stack)
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
                    kwargs[arg_name] = self._provide_arg(
                        arg_name, binding_key_stack=[])
            return fn(*pargs, **kwargs)
        return WrappedFn


def _arg_names_without_self(args):
    return args[1:]
