
import inspect

# From http://micheles.googlecode.com/hg/decorator/documentation.html
import decorator

import binding
import errors
import scoping


_ARG_BINDING_KEYS_ATTR = '_pinject_arg_binding_keys'
_IS_WRAPPER_ATTR = '_pinject_is_wrapper'
_ORIG_FN_ATTR = '_pinject_orig_fn'
_PROVIDED_BINDINGS_ATTR = '_pinject_provided_bindings'


def annotate(arg_name, annotation):
    binding_key = binding.BindingKeyWithAnnotation(arg_name, annotation)
    return _get_pinject_wrapper(arg_binding_key=binding_key)


def inject(fn):
    if not inspect.isfunction(fn):
        raise errors.InjectDecoratorAppliedToNonInitError(fn)
    if fn.__name__ != '__init__':
        raise errors.InjectDecoratorAppliedToNonInitError(fn)
    return _get_pinject_decorated_fn(fn)


def provides(arg_name, annotated_with=None, in_scope=scoping.PROTOTYPE):
    binding_key = binding.new_binding_key(arg_name, annotated_with)
    return _get_pinject_wrapper(provided_binding_key=binding_key,
                                provided_in_scope=in_scope)


def _get_pinject_decorated_fn(fn):
    if hasattr(fn, _IS_WRAPPER_ATTR):
        pinject_decorated_fn = fn
    else:
        def _pinject_decorated_fn(fn_to_wrap, *pargs, **kwargs):
            return fn_to_wrap(*pargs, **kwargs)
        pinject_decorated_fn = decorator.decorator(_pinject_decorated_fn, fn)
        setattr(pinject_decorated_fn, _IS_WRAPPER_ATTR, True)
        setattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR, [])
        setattr(pinject_decorated_fn, _ORIG_FN_ATTR, fn)
        setattr(pinject_decorated_fn, _PROVIDED_BINDINGS_ATTR, [])
    return pinject_decorated_fn


def _get_pinject_wrapper(arg_binding_key=None,
                         provided_binding_key=None, provided_in_scope=None):
    def get_pinject_decorated_fn_with_additions(fn):
        pinject_decorated_fn = _get_pinject_decorated_fn(fn)
        if arg_binding_key is not None:
            arg_names, unused_varargs, unused_keywords, unused_defaults = (
                inspect.getargspec(getattr(pinject_decorated_fn, _ORIG_FN_ATTR)))
            if arg_binding_key.arg_name not in arg_names:
                raise errors.NoSuchArgToInjectError(arg_binding_key.arg_name, fn)
            bound_arg_names = [binding_key.arg_name
                               for binding_key in getattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR)]
            if arg_binding_key.arg_name in bound_arg_names:
                raise errors.MultipleAnnotationsForSameArgError(
                    arg_binding_key.arg_name)
            getattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR).append(arg_binding_key)
        if provided_binding_key is not None:
            proviser_fn = binding.create_proviser_fn(
                provided_binding_key, to_provider=pinject_decorated_fn)
            provided_binding = binding.Binding(
                provided_binding_key, proviser_fn, provided_in_scope)
            getattr(pinject_decorated_fn, _PROVIDED_BINDINGS_ATTR).append(
                provided_binding)
        return pinject_decorated_fn
    return get_pinject_decorated_fn_with_additions


def get_any_class_binding_keys(cls, get_arg_names_from_class_name):
    if (hasattr(cls, '__init__') and hasattr(cls.__init__, _IS_WRAPPER_ATTR)):
        return [binding.BindingKeyWithoutAnnotation(arg_name)
                for arg_name in get_arg_names_from_class_name(cls.__name__)]
    else:
        return []


def get_arg_binding_keys_and_remaining_args(fn):
    if hasattr(fn, _IS_WRAPPER_ATTR):
        arg_binding_keys = getattr(fn, _ARG_BINDING_KEYS_ATTR)
        prebound_arg_names = [binding_key.arg_name for binding_key in arg_binding_keys]
        arg_names, unused_varargs, unused_keywords, unused_defaults = (
            inspect.getargspec(getattr(fn, _ORIG_FN_ATTR)))
        arg_names_to_inject = [
            arg_name for arg_name in _remove_self_if_exists(arg_names)
            if arg_name not in prebound_arg_names]
    else:
        arg_binding_keys = []
        arg_names, unused_varargs, unused_keywords, unused_defaults = (
            inspect.getargspec(fn))
        arg_names_to_inject = _remove_self_if_exists(arg_names)
    return arg_binding_keys, arg_names_to_inject


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
