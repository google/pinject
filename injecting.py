
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
        modules=finding.ALL_IMPORTED_MODULES, classes=None, binding_modules=None,
        only_use_explicit_bindings=False, allow_injecting_none=False,
        get_arg_names_from_class_name=(
            binding.default_get_arg_names_from_class_name),
        get_arg_names_from_provider_fn_name=(
            providing.default_get_arg_names_from_provider_fn_name),
        id_to_scope=None, is_scope_usable_from_scope=lambda _1, _2: True):

    id_to_scope = scoping.get_id_to_scope_with_defaults(id_to_scope)
    bindable_scopes = scoping.BindableScopes(
        id_to_scope, is_scope_usable_from_scope)
    known_scope_ids = id_to_scope.keys()

    found_classes = finding.find_classes(modules, classes)
    if only_use_explicit_bindings:
        implicit_class_bindings = []
    else:
        implicit_class_bindings = binding.get_implicit_class_bindings(
            found_classes, get_arg_names_from_class_name)
    explicit_bindings = binding.get_explicit_class_bindings(
        found_classes, get_arg_names_from_class_name)
    binder = binding.Binder(explicit_bindings, known_scope_ids)
    if binding_modules is not None:
        for binding_module in binding_modules:
            if (hasattr(binding_module, 'pinject_configure') and
                callable(binding_module.pinject_configure)):
                binding_module.pinject_configure(binder.bind)
                has_pinject_configure = True
            else:
                has_pinject_configure = False
            provider_bindings = binding.get_provider_bindings(
                binding_module, get_arg_names_from_provider_fn_name)
            if not has_pinject_configure and not provider_bindings:
                raise errors.EmptyExplicitBindingModuleError(binding_module)
            explicit_bindings.extend(provider_bindings)

    binding_key_to_binding, collided_binding_key_to_bindings = (
        binding.get_overall_binding_key_to_binding_maps(
            [implicit_class_bindings, explicit_bindings]))
    binding_mapping = binding.BindingMapping(
        binding_key_to_binding, collided_binding_key_to_bindings)

    is_injectable_fn = {
        True: (lambda cls: bool(wrapping.get_any_class_binding_keys(
            cls, get_arg_names_from_class_name))),
        False: (lambda cls: True)
    }[only_use_explicit_bindings]
    injector = _Injector(binding_mapping, bindable_scopes, is_injectable_fn,
                         allow_injecting_none)
    return injector


class _Injector(object):

    def __init__(self, binding_mapping, bindable_scopes, is_injectable_fn,
                 allow_injecting_none):
        self._binding_mapping = binding_mapping
        self._bindable_scopes = bindable_scopes
        self._is_injectable_fn = is_injectable_fn
        self._allow_injecting_none = allow_injecting_none

    def provide(self, cls):
        if not self._is_injectable_fn(cls):
            raise errors.NonExplicitlyBoundClassError(cls)
        return self._provide_class(cls, binding.new_binding_context())

    def _provide_from_binding_key(self, binding_key, binding_context):
        binding_ = self._binding_mapping.get(binding_key)
        scope = self._bindable_scopes.get_sub_scope(binding_, binding_context)
        provided = scope.provide(
            binding_key,
            lambda: binding_.proviser_fn(binding_context.get_child(binding_key, binding_.scope_id), self))
        if (provided is None) and not self._allow_injecting_none:
            raise errors.InjectingNoneDisallowedError()
        return provided

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
                        binding.new_binding_key(arg_name),
                        binding.new_binding_context())
            return fn(*pargs, **kwargs)
        return WrappedFn

    def _call_with_injection(self, provider_fn, binding_context):
        kwargs = self._get_injection_kwargs(provider_fn, binding_context)
        return provider_fn(**kwargs)

    def _get_injection_kwargs(self, fn, binding_context):
        kwargs = {}
        arg_binding_keys, arg_names_to_inject = (
            wrapping.get_arg_binding_keys_and_remaining_args(fn))
        for arg_binding_key in arg_binding_keys:
            arg_binding_key.put_provided_value_in_kwargs(
                self._provide_from_binding_key(arg_binding_key, binding_context),
                kwargs)
        for arg_name in arg_names_to_inject:
            binding_key = binding.new_binding_key(arg_name)
            kwargs[arg_name] = self._provide_from_binding_key(
                binding_key, binding_context)
        return kwargs
