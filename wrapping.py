
import inspect

# From http://micheles.googlecode.com/hg/decorator/documentation.html
import decorator

import binding
import errors


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


# def provides(arg_name, annotated_with=None):
#     binding_key = binding.new_binding_key(arg_name, annotated_with)


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


def get_prebindings_and_remaining_args(fn):
    if hasattr(fn, _IS_DECORATOR_ATTR):
        prebound_bindings = getattr(fn, _BINDINGS_ATTR)
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
