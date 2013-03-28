
import inspect

# From http://micheles.googlecode.com/hg/decorator/documentation.html
import decorator

import binding
import errors
import scoping


_ARG_BINDINGS_ATTR = '_pinject_arg_bindings'
_IS_WRAPPER_ATTR = '_pinject_is_wrapper'
_ORIG_FN_ATTR = '_pinject_orig_fn'
_PROVIDED_BINDINGS_ATTR = '_pinject_provided_bindings'


def annotate(arg_name, annotation):
    binding_key = binding.BindingKeyWithAnnotation(arg_name, annotation)
    proviser_fn = lambda binding_key_stack, in_scope, injector: (
        injector._provide_from_binding_key(binding_key, binding_key_stack, in_scope))
    return _get_pinject_wrapper(
        arg_binding=binding.Binding(binding_key, proviser_fn))


# TODO(kurts): probably remove @inject, except as a marker for explicit-only mode.
def inject(arg_name, with_class=None, with_instance=None, with_provider=None):
    binding_key = binding.BindingKeyWithoutAnnotation(arg_name)
    proviser_fn = binding.create_proviser_fn(
        binding_key, with_class, with_instance, with_provider)
    return _get_pinject_wrapper(
        arg_binding=binding.Binding(binding_key, proviser_fn))


def provides(arg_name, annotated_with=None, in_scope=scoping.PROTOTYPE):
    binding_key = binding.new_binding_key(arg_name, annotated_with)
    return _get_pinject_wrapper(provided_binding_key=binding_key,
                                provided_in_scope=in_scope)


def _get_pinject_wrapper(arg_binding=None,
                         provided_binding_key=None, provided_in_scope=None):
    def get_pinject_decorated_fn(fn):
        if hasattr(fn, _IS_WRAPPER_ATTR):
            pinject_decorated_fn = fn
        else:
            def _pinject_decorated_fn(fn_to_wrap, *pargs, **kwargs):
                return fn_to_wrap(*pargs, **kwargs)
            pinject_decorated_fn = decorator.decorator(_pinject_decorated_fn, fn)
            setattr(pinject_decorated_fn, _IS_WRAPPER_ATTR, True)
            setattr(pinject_decorated_fn, _ARG_BINDINGS_ATTR, [])
            setattr(pinject_decorated_fn, _ORIG_FN_ATTR, fn)
            setattr(pinject_decorated_fn, _PROVIDED_BINDINGS_ATTR, [])

        if arg_binding is not None:
            arg_names, unused_varargs, unused_keywords, unused_defaults = (
                inspect.getargspec(getattr(pinject_decorated_fn, _ORIG_FN_ATTR)))
            if arg_binding.binding_key.arg_name not in arg_names:
                raise errors.NoSuchArgToInjectError(arg_binding.binding_key.arg_name, fn)
            getattr(pinject_decorated_fn, _ARG_BINDINGS_ATTR).append(arg_binding)
        if provided_binding_key is not None:
            proviser_fn = binding.create_proviser_fn(
                provided_binding_key, to_provider=pinject_decorated_fn)
            provided_binding = binding.Binding(
                provided_binding_key, proviser_fn, provided_in_scope)
            getattr(pinject_decorated_fn, _PROVIDED_BINDINGS_ATTR).append(
                provided_binding)

        return pinject_decorated_fn
    return get_pinject_decorated_fn


def get_prebindings_and_remaining_args(fn):
    if hasattr(fn, _IS_WRAPPER_ATTR):
        prebound_bindings = getattr(fn, _ARG_BINDINGS_ATTR)
        prebound_arg_names = [b.binding_key.arg_name for b in prebound_bindings]
        arg_names, unused_varargs, unused_keywords, unused_defaults = (
            inspect.getargspec(getattr(fn, _ORIG_FN_ATTR)))
        arg_names_to_inject = [
            arg_name for arg_name in _remove_self_if_exists(arg_names)
            if arg_name not in prebound_arg_names]
    else:
        prebound_bindings = []
        arg_names, unused_varargs, unused_keywords, unused_defaults = (
            inspect.getargspec(fn))
        arg_names_to_inject = _remove_self_if_exists(arg_names)
    return prebound_bindings, arg_names_to_inject


# TODO(kurts): this feels icky.  Is there no way around this, because
# cls.__init__() takes self but instance.__init__() doesn't, and python is
# awkward here?
def _remove_self_if_exists(args):
    if args and args[0] == 'self':
        return args[1:]
    else:
        return args


def get_any_provider_bindings(fn):
    if hasattr(fn, _IS_WRAPPER_ATTR):
        return getattr(fn, _PROVIDED_BINDINGS_ATTR)
    else:
        return []
