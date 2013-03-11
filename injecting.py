
import inspect
import re

import binding
import errors
import finding


def NewInjector(modules=None, classes=None,
                get_arg_names_from_class_name=binding.default_get_arg_names_from_class_name,
                # binding_fns=None,
                # binding_modules=None
                ):
    classes = finding.FindClasses(modules, classes)
    implicit_bindings = binding.get_implicit_bindings(
        classes, get_arg_names_from_class_name)
    binding_mapping = binding.new_binding_mapping([], implicit_bindings)
    return _Injector(binding_mapping)


class _Injector(object):

    def __init__(self, binding_mapping):
        self._binding_mapping = binding_mapping

    def provide(self, thing):
        if isinstance(thing, type):
            return self._provide_class(thing)
        else:
            raise errors.UnknownProvideIdentifierError(
                'cannot provide thing identified by {0}'.format(thing))

    def _provide_arg(self, arg_name):
        binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
        # TODO(kurts): make a reasonable error message if the mapping raises.
        arg_class = self._binding_mapping.get_class(binding_key)
        return self._provide_class(arg_class)

    def _provide_class(self, cls):
        init_kwargs = {}
        if cls.__init__ is not object.__init__:
            arg_names, unused_varargs, unused_keywords, unused_defaults = inspect.getargspec(cls.__init__)
            for arg_name in _ArgNamesWithoutSelf(arg_names):
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


def _ArgNamesWithoutSelf(args):
    return args[1:]


# class InjectorNotYetInstantiated(object):

#     def __getattribute__(self, unused_name):
#         def RaiseError(*pargs, **kwargs):
#             raise InjectorNotYetInstantiatedError()
#         return RaiseError


# class FutureInjector(object):

#     def __init__(self):
#         self._injector = InjectorNotYetInstantiated()

#     def __getattribute__(self, name):
#         return getattr(self._injector, name)

#     def set_injector(self, injector):
#         if isinstance(self._injector, InjectorNotYetInstantiated):
#             raise ProgrammerError('set_injector() should not be called twice')
#         self._injector = injector
