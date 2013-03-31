
import functools
import inspect
import types

import binding
import errors
import finding
import providing
import scoping
import wrapping


def new_injector(
    modules=None, classes=None, provider_fns=None,
    get_arg_names_from_class_name=(
        binding.default_get_arg_names_from_class_name),
    get_arg_names_from_provider_fn_name=(
        providing.default_get_arg_names_from_provider_fn_name),
    binding_fns=None, id_to_scope=None,
    is_scope_usable_from_scope_fn=lambda _1, _2: True):

    id_to_scope = scoping.get_id_to_scope_with_defaults(id_to_scope)
    bindable_scopes = scoping.BindableScopes(
        id_to_scope, is_scope_usable_from_scope_fn)
    known_scope_ids = id_to_scope.keys()

    classes = finding.find_classes(modules, classes, provider_fns)
    functions = finding.find_functions(modules, classes, provider_fns)
    implicit_bindings = binding.get_implicit_bindings(
        classes, functions, get_arg_names_from_class_name,
        get_arg_names_from_provider_fn_name)
    explicit_bindings = binding.get_explicit_bindings(
        classes, functions, known_scope_ids)
    binder = binding.Binder(explicit_bindings, known_scope_ids)
    if binding_fns is not None:
        for binding_fn in binding_fns:
            binding_fn(bind=binder.bind)

    binding_key_to_binding, collided_binding_key_to_bindings = (
        binding.get_binding_key_to_binding_maps(
            explicit_bindings, implicit_bindings))
    binding_mapping = binding.BindingMapping(
        binding_key_to_binding, collided_binding_key_to_bindings)
    injector = _Injector(binding_mapping, bindable_scopes)
    return injector


class _Injector(object):

    def __init__(self, binding_mapping, bindable_scopes):
        self._binding_mapping = binding_mapping
        self._bindable_scopes = bindable_scopes

    def provide(self, cls):
        return self._provide_class(cls, binding.new_binding_context())

    def _provide_from_binding_key(self, binding_key, binding_context):
        binding_ = self._binding_mapping.get(binding_key)
        scope = self._bindable_scopes.get_sub_scope(binding_, binding_context)
        return scope.provide(
            binding_key,
            lambda: binding_.proviser_fn(binding_context.get_child(binding_key, scope), self))

    def _provide_class(self, cls, binding_context):
        if type(cls.__init__) is types.MethodType:
            init_kwargs = self._get_injection_kwargs(
                cls.__init__, binding_context)
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
                        binding.new_binding_context())
            return fn(*pargs, **kwargs)
        return WrappedFn

    def _call_with_injection(self, provider_fn, binding_context):
        kwargs = self._get_injection_kwargs(provider_fn, binding_context)
        return provider_fn(**kwargs)

    def _get_injection_kwargs(self, fn, binding_context):
        kwargs = {}
        prebound_bindings, arg_names_to_inject = wrapping.get_prebindings_and_remaining_args(fn)
        for prebound_binding in prebound_bindings:
            kwargs[prebound_binding.binding_key.arg_name] = (
                prebound_binding.proviser_fn(binding_context, self))
        for arg_name in arg_names_to_inject:
            binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
            kwargs[arg_name] = self._provide_from_binding_key(
                binding_key, binding_context)
        return kwargs
