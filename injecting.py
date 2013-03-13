
import inspect
import re

import binding
import errors
import finding


def new_injector(modules=None, classes=None,
                 get_arg_names_from_class_name=binding.default_get_arg_names_from_class_name,
                 binding_fns=None,
                 # binding_modules=None
                 ):
    future_injector = _FutureInjector()

    explicit_bindings = []
    binder = binding.Binder(future_injector, explicit_bindings)
    if binding_fns is not None:
        for binding_fn in binding_fns:
            binding_fn(binder)

    classes = finding.FindClasses(modules, classes)
    implicit_bindings = binding.get_implicit_bindings(
        classes, future_injector, get_arg_names_from_class_name)
    binding_mapping = binding.new_binding_mapping(
        explicit_bindings, implicit_bindings)

    injector = _Injector(binding_mapping)
    future_injector.set_injector(injector)
    return injector


class _Injector(object):

    def __init__(self, binding_mapping):
        self._binding_mapping = binding_mapping

    def provide(self, cls):
        return self._provide_class(cls)

    def _provide_arg(self, arg_name):
        binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
        # TODO(kurts): make a reasonable error message if the mapping raises.
        return self._binding_mapping.get_instance(binding_key)

    def _provide_class(self, cls):
        init_kwargs = {}
        if cls.__init__ is not object.__init__:
            arg_names, unused_varargs, unused_keywords, unused_defaults = inspect.getargspec(cls.__init__)
            for arg_name in _arg_names_without_self(arg_names):
                init_kwargs[arg_name] = self._provide_arg(arg_name)
        return cls(**init_kwargs)

    def wrap(self, fn):
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
                    kwargs[arg_name] = self._provide_arg(arg_name)
            return fn(*pargs, **kwargs)
        return WrappedFn


def _arg_names_without_self(args):
    return args[1:]


class _InjectorNotYetInstantiated(object):

    def __getattribute__(self, unused_name):
        def RaiseError(*pargs, **kwargs):
            raise errors.InjectorNotYetInstantiatedError()
        return RaiseError


class _FutureInjector(object):

    def __init__(self):
        self._injector = _InjectorNotYetInstantiated()

    def __getattr__(self, name):
        return getattr(self._injector, name)

    def set_injector(self, injector):
        if not isinstance(self._injector, _InjectorNotYetInstantiated):
            raise ProgrammerError('set_injector() should not be called twice')
        self._injector = injector
