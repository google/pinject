
import inspect
import re

import binding
import errors
import finding


# def inject(arg_name, to_class=None, to_instance=None, to_provider=None):
#     binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
#     def get_decorated_initializer(initializer_fn):
#         return initializer_fn
#     return get_decorated_initializer



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
