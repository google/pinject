
import inspect
import re
import threading
import types

# From http://micheles.googlecode.com/hg/decorator/documentation.html
import decorator

import annotation as annotation_lib
import errors
import scoping
import providing
import wrapping


class BindingKey(object):
    """The key for a binding."""

    def __init__(self, arg_name, annotation):
        self._arg_name = arg_name
        self._annotation = annotation

    def __repr__(self):
        return '<{0}>'.format(self)

    def __str__(self):
        return 'the arg name "{0}" {1}'.format(
            self._arg_name, self._annotation.as_adjective())

    def __eq__(self, other):
        return (isinstance(other, BindingKey) and
                self._arg_name == other._arg_name and
                self._annotation == other._annotation)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self._arg_name) ^ hash(self._annotation)

    def can_apply_to_one_of_arg_names(self, arg_names):
        return self._arg_name in arg_names

    def conflicts_with_any_binding_key(self, binding_keys):
        return self._arg_name in [bk._arg_name for bk in binding_keys]

    def put_provided_value_in_kwargs(self, value, kwargs):
        kwargs[self._arg_name] = value


# TODO(kurts): Get a second opinion on module-level methods operating on
# internal state of classes.  In another language, this would be a static
# member and so allowed access to internals.
def get_unbound_arg_names(arg_names, arg_binding_keys):
    bound_arg_names = [bk._arg_name for bk in arg_binding_keys]
    return [arg_name for arg_name in arg_names
            if arg_name not in bound_arg_names]


def new_binding_key(arg_name, annotated_with=None):
    if annotated_with is not None:
        annotation = annotation_lib.Annotation(annotated_with)
    else:
        annotation = annotation_lib._NO_ANNOTATION
    return BindingKey(arg_name, annotation)


def new_binding_in_default_scope(binding_key, proviser_fn):
    return Binding(binding_key, proviser_fn, scoping.DEFAULT_SCOPE, desc='unknown')


class Binding(object):

    def __init__(self, binding_key, proviser_fn, scope_id, desc):
        self.binding_key = binding_key
        self.proviser_fn = proviser_fn
        self.scope_id = scope_id
        self._desc = desc

    def __str__(self):
        return 'the binding from {0} to {1}'.format(self.binding_key, self._desc)


def _handle_explicit_binding_collision(
        colliding_binding, binding_key_to_binding, *pargs):
    other_binding = binding_key_to_binding[colliding_binding.binding_key]
    raise errors.ConflictingBindingsError([colliding_binding, other_binding])


def _handle_implicit_binding_collision(
        colliding_binding, binding_key_to_binding,
        collided_binding_key_to_bindings):
    binding_key = colliding_binding.binding_key
    bindings = collided_binding_key_to_bindings.setdefault(
        binding_key, set())
    bindings.add(binding_key_to_binding[binding_key])
    del binding_key_to_binding[binding_key]


def _get_binding_key_to_binding_maps(bindings, handle_binding_collision_fn):
    binding_key_to_binding = {}
    collided_binding_key_to_bindings = {}
    for binding_ in bindings:
        binding_key = binding_.binding_key
        if binding_key in binding_key_to_binding:
            handle_binding_collision_fn(
                binding_, binding_key_to_binding,
                collided_binding_key_to_bindings)
        if binding_key in collided_binding_key_to_bindings:
            collided_binding_key_to_bindings[binding_key].add(binding_)
        else:
            binding_key_to_binding[binding_key] = binding_
    return binding_key_to_binding, collided_binding_key_to_bindings


def get_overall_binding_key_to_binding_maps(bindings_lists):
    """bindings_lists from lowest to highest priority.  Last item in
    bindings_lists is assumed explicit.

    """
    binding_key_to_binding = {}
    collided_binding_key_to_bindings = {}

    for index, bindings in enumerate(bindings_lists):
        is_final_index = (index == (len(bindings_lists) - 1))
        handle_binding_collision_fn = {
            True: _handle_explicit_binding_collision,
            False: _handle_implicit_binding_collision}[is_final_index]
        this_binding_key_to_binding, this_collided_binding_key_to_bindings = (
            _get_binding_key_to_binding_maps(bindings, handle_binding_collision_fn))
        for good_binding_key in this_binding_key_to_binding:
            collided_binding_key_to_bindings.pop(good_binding_key, None)
        binding_key_to_binding.update(this_binding_key_to_binding)
        collided_binding_key_to_bindings.update(
            this_collided_binding_key_to_bindings)

    return binding_key_to_binding, collided_binding_key_to_bindings


class BindingMapping(object):

    def __init__(self, binding_key_to_binding,
                 collided_binding_key_to_bindings):
        self._binding_key_to_binding = binding_key_to_binding
        self._collided_binding_key_to_bindings = (
            collided_binding_key_to_bindings)

    def get(self, binding_key):
        if binding_key in self._binding_key_to_binding:
            return self._binding_key_to_binding[binding_key]
        elif binding_key in self._collided_binding_key_to_bindings:
            raise errors.AmbiguousArgNameError(
                binding_key,
                self._collided_binding_key_to_bindings[binding_key])
        else:
            raise errors.NothingInjectableForArgError(binding_key)


def new_binding_context():
    return BindingContext(binding_key_stack=[], scope_id=scoping.UNSCOPED)


class BindingContext(object):

    def __init__(self, binding_key_stack, scope_id):
        self._binding_key_stack = binding_key_stack
        self._scope_id = scope_id

    def get_child(self, binding_key, scope_id):
        new_binding_key_stack = list(self._binding_key_stack)
        new_binding_key_stack.append(binding_key)
        if binding_key in self._binding_key_stack:
            raise errors.CyclicInjectionError(new_binding_key_stack)
        return BindingContext(new_binding_key_stack, scope_id)

    # TODO(kurts): this smells like a public attribute.  Maybe move
    # BindableScopes in here?
    def does_scope_id_match(self, does_scope_id_match_fn):
        return does_scope_id_match_fn(self._scope_id)

    def __str__(self):
        return 'the scope "{0}"'.format(self._scope_id)


def default_get_arg_names_from_class_name(class_name):
    """Converts normal class names into normal arg names.

    Normal class names are assumed to be CamelCase with an optional leading
    underscore.  Normal arg names are assumed to be lower_with_underscores.

    Args:
      class_name: a class name, e.g., "FooBar"
    Returns:
      all likely corresponding param names, e.g., ["foo_bar"]
    """
    parts = []
    rest = class_name
    if rest.startswith('_'):
        rest = rest[1:]
    while True:
        m = re.match(r'([A-Z][a-z]+)(.*)', rest)
        if m is None:
            break
        parts.append(m.group(1))
        rest = m.group(2)
    if not parts:
        return []
    return ['_'.join(part.lower() for part in parts)]


def get_explicit_class_bindings(
        classes,
        get_arg_names_from_class_name=default_get_arg_names_from_class_name):
    explicit_bindings = []
    for cls in classes:
        if wrapping.is_explicitly_injectable(cls):
            for arg_name in get_arg_names_from_class_name(cls.__name__):
                binding_key = new_binding_key(arg_name)
                proviser_fn = create_proviser_fn(binding_key, to_class=cls)
                explicit_bindings.append(Binding(
                    binding_key, proviser_fn, scoping.DEFAULT_SCOPE,
                    desc='the explicitly injectable class {0}'.format(cls)))
    return explicit_bindings


def get_provider_bindings(
        binding_module,
        get_arg_names_from_provider_fn_name=(
            providing.default_get_arg_names_from_provider_fn_name)):
    provider_bindings = []
    fns = inspect.getmembers(binding_module, lambda x: type(x) == types.FunctionType)
    for _, fn in fns:
        arg_names = get_arg_names_from_provider_fn_name(fn.__name__)
        for arg_name in arg_names:
            provider_bindings.append(
                wrapping.get_provider_fn_binding(fn, arg_name))
    return provider_bindings


def get_implicit_class_bindings(
        classes,
        get_arg_names_from_class_name=(
            default_get_arg_names_from_class_name)):
    implicit_bindings = []
    for cls in classes:
        arg_names = get_arg_names_from_class_name(cls.__name__)
        for arg_name in arg_names:
            binding_key = new_binding_key(arg_name)
            proviser_fn = create_proviser_fn(binding_key, to_class=cls)
            implicit_bindings.append(Binding(
                binding_key, proviser_fn, scoping.DEFAULT_SCOPE,
                desc='the implicitly bound class {0}'.format(cls)))
    return implicit_bindings


class Binder(object):

    def __init__(self, collected_bindings, scope_ids):
        self._collected_bindings = collected_bindings
        self._scope_ids = scope_ids
        self._lock = threading.Lock()

    def bind(self, arg_name, annotated_with=None,
             to_class=None, to_instance=None, in_scope=scoping.PROTOTYPE):
        if in_scope not in self._scope_ids:
            raise errors.UnknownScopeError(in_scope)
        binding_key = new_binding_key(arg_name, annotated_with)
        proviser_fn = create_proviser_fn(binding_key, to_class, to_instance)
        with self._lock:
            back_frame = inspect.currentframe().f_back
            self._collected_bindings.append(Binding(
                binding_key, proviser_fn, in_scope,
                desc='the explicit binding target at line {0} of {1}'.format(
                    back_frame.f_lineno, back_frame.f_code.co_filename)))


def create_proviser_fn(binding_key, to_class=None, to_instance=None):
    specified_to_params = ['to_class' if to_class is not None else None,
                           'to_instance' if to_instance is not None else None]
    specified_to_params = [x for x in specified_to_params if x is not None]
    if not specified_to_params:
        raise errors.NoBindingTargetError(binding_key)
    elif len(specified_to_params) > 1:
        raise errors.MultipleBindingTargetsError(
            binding_key, specified_to_params)

    if to_class is not None:
        if not inspect.isclass(to_class):
            raise errors.InvalidBindingTargetError(
                binding_key, to_class, 'class')
        # TODO(kurts): don't call private method of obj_graph.
        proviser_fn = lambda binding_context, obj_graph: obj_graph._provide_class(
            to_class, binding_context)
        proviser_fn._pinject_desc = 'the class {0!r}'.format(to_class)
    else:  # to_instance is not None:
        proviser_fn = lambda binding_context, obj_graph: to_instance
        proviser_fn._pinject_desc = 'the instance {0!r}'.format(to_instance)
    return proviser_fn


class FakeBindingModule(object):

    def __init__(self, *pargs):
        self.__dict__.update({x.__name__: x for x in pargs})
