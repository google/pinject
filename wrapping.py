
import inspect

# From http://micheles.googlecode.com/hg/decorator/documentation.html
import decorator

import binding
import errors
import scoping


_ARG_BINDING_KEYS_ATTR = '_pinject_arg_binding_keys'
_IS_WRAPPER_ATTR = '_pinject_is_wrapper'
_ORIG_FN_ATTR = '_pinject_orig_fn'
_PROVIDER_ANNOTATED_WITH_ATTR = '_pinject_provider_annotated_with'
_PROVIDER_IN_SCOPE_ID_ATTR = '_pinject_in_scope_id'


def annotate_arg(arg_name, with_annotation):
    binding_key = binding.new_binding_key(arg_name, with_annotation)
    return _get_pinject_wrapper(arg_binding_key=binding_key)


def injectable(fn):
    if not inspect.isfunction(fn):
        raise errors.InjectableDecoratorAppliedToNonInitError(fn)
    if fn.__name__ != '__init__':
        raise errors.InjectableDecoratorAppliedToNonInitError(fn)
    return _get_pinject_decorated_fn(fn)


def annotated_with(annotation):
    return _get_pinject_wrapper(provider_annotated_with=annotation)


def in_scope(scope_id):
    return _get_pinject_wrapper(provider_in_scope_id=scope_id)


def get_provider_fn_binding(provider_fn, arg_name):
    if hasattr(provider_fn, _IS_WRAPPER_ATTR):
        annotated_with = getattr(provider_fn, _PROVIDER_ANNOTATED_WITH_ATTR)
        in_scope_id = getattr(provider_fn, _PROVIDER_IN_SCOPE_ID_ATTR)
        if in_scope_id is None:
            in_scope_id = scoping.DEFAULT_SCOPE
    else:
        annotated_with = None
        in_scope_id = scoping.DEFAULT_SCOPE
    binding_key = binding.new_binding_key(arg_name, annotated_with)
    # TODO(kurts): don't call private method of obj_graph.
    proviser_fn = lambda binding_context, obj_graph: obj_graph._call_with_injection(
        provider_fn, binding_context)
    proviser_fn._pinject_desc = 'the provider {0!r}'.format(provider_fn)
    return binding.Binding(
        binding_key, proviser_fn, in_scope_id,
        desc='the provider function {0} from module {1}'.format(
            provider_fn, provider_fn.__module__))


def _get_pinject_decorated_fn(fn):
    if hasattr(fn, _IS_WRAPPER_ATTR):
        pinject_decorated_fn = fn
    else:
        def _pinject_decorated_fn(fn_to_wrap, *pargs, **kwargs):
            return fn_to_wrap(*pargs, **kwargs)
        pinject_decorated_fn = decorator.decorator(_pinject_decorated_fn, fn)
        setattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR, [])
        setattr(pinject_decorated_fn, _IS_WRAPPER_ATTR, True)
        setattr(pinject_decorated_fn, _ORIG_FN_ATTR, fn)
        setattr(pinject_decorated_fn, _PROVIDER_ANNOTATED_WITH_ATTR, None)
        setattr(pinject_decorated_fn, _PROVIDER_IN_SCOPE_ID_ATTR, None)
    return pinject_decorated_fn


def _get_pinject_wrapper(arg_binding_key=None,
                         provider_annotated_with=None, provider_in_scope_id=None):
    def get_pinject_decorated_fn_with_additions(fn):
        pinject_decorated_fn = _get_pinject_decorated_fn(fn)
        if arg_binding_key is not None:
            arg_names, unused_varargs, unused_keywords, unused_defaults = (
                inspect.getargspec(getattr(pinject_decorated_fn, _ORIG_FN_ATTR)))
            if not arg_binding_key.can_apply_to_one_of_arg_names(arg_names):
                raise errors.NoSuchArgToInjectError(arg_binding_key, fn)
            if arg_binding_key.conflicts_with_any_binding_key(
                    getattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR)):
                raise errors.MultipleAnnotationsForSameArgError(arg_binding_key)
            getattr(pinject_decorated_fn, _ARG_BINDING_KEYS_ATTR).append(arg_binding_key)
        if provider_annotated_with is not None:
            if getattr(pinject_decorated_fn, _PROVIDER_ANNOTATED_WITH_ATTR) is not None:
                raise errors.DuplicateDecoratorError(
                    '@annotated_with', getattr(pinject_decorated_fn, _ORIG_FN_ATTR))
            setattr(pinject_decorated_fn, _PROVIDER_ANNOTATED_WITH_ATTR,
                    provider_annotated_with)
        if provider_in_scope_id is not None:
            if getattr(pinject_decorated_fn, _PROVIDER_IN_SCOPE_ID_ATTR) is not None:
                raise errors.DuplicateDecoratorError(
                    '@in_scope', getattr(pinject_decorated_fn, _ORIG_FN_ATTR))
            setattr(pinject_decorated_fn, _PROVIDER_IN_SCOPE_ID_ATTR,
                    provider_in_scope_id)
        return pinject_decorated_fn
    return get_pinject_decorated_fn_with_additions


def is_explicitly_injectable(cls):
    return (hasattr(cls, '__init__') and
            hasattr(cls.__init__, _IS_WRAPPER_ATTR))


def get_injectable_arg_binding_keys(fn):
    if hasattr(fn, _IS_WRAPPER_ATTR):
        arg_binding_keys = getattr(fn, _ARG_BINDING_KEYS_ATTR)
        arg_names, unused_varargs, unused_keywords, defaults = (
            inspect.getargspec(getattr(fn, _ORIG_FN_ATTR)))
        num_to_keep = (len(arg_names) - len(defaults)) if defaults else len(arg_names)
        arg_names = arg_names[:num_to_keep]
        unbound_arg_names = binding.get_unbound_arg_names(
            [arg_name for arg_name in _remove_self_if_exists(arg_names)],
            arg_binding_keys)
    else:
        arg_binding_keys = []
        arg_names, unused_varargs, unused_keywords, defaults = (
            inspect.getargspec(fn))
        num_to_keep = (len(arg_names) - len(defaults)) if defaults else len(arg_names)
        arg_names = arg_names[:num_to_keep]
        unbound_arg_names = _remove_self_if_exists(arg_names)
    all_arg_binding_keys = list(arg_binding_keys)
    all_arg_binding_keys.extend([binding.new_binding_key(arg_name)
                                 for arg_name in unbound_arg_names])
    return all_arg_binding_keys


# TODO(kurts): this feels icky.  Is there no way around this, because
# cls.__init__() takes self but instance.__init__() doesn't, and python is
# awkward here?
def _remove_self_if_exists(args):
    if args and args[0] == 'self':
        return args[1:]
    else:
        return args
