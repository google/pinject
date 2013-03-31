
import inspect
import re
import threading
import types

# From http://micheles.googlecode.com/hg/decorator/documentation.html
import decorator

import errors
import scoping
import providing
import wrapping


_IS_DECORATED_ATTR = '_pinject_is_decorated'
_BOUND_TO_BINDING_KEYS_ATTR = '_pinject_bound_to_binding_keys'


# TODO(kurts): I want to avoid conflicting bindings.  If I annotate SomeClass
# as @binds_to('foo') and then, in a binding function, say bind('foo'
# to_class=SomeClass, in_scope=SOME_SCOPE), that seems like a conflicting
# binding (because the @binds_to is implicitly in whatever the default scope
# is).
#
# Maybe that's OK?  Maybe I say that that will be a conflicting binding, and,
# if you want to bind in a scope, you need to bind in a binding function
# instead of using @binds_to?
#
# But that seems obtuse.  It seems arbitrary to say, hey, if you want to bind
# a class to an arg name in the default scope, you can use @binds_to, but if
# you want it in a *non-default* scope, well then, you have to use a binding
# function.
#
# Maybe the solution is to allow bind(arg_name, in_scope) without specifying
# what it's bound to.  This would use modify whatever binding arg_name has and
# make it scoped.  On one hand, that seems like it's dividing binding
# information in two places (e.g., @binds_to at the class definition,
# bind(...) in the binding module).  On the other hand, you wouldn't have to
# specifically say what arg_name is bound to when binding it in a scope.
#
# But why shouldn't you have to say what arg_name is bound to, when binding it
# in a scope?  If you don't have to say what it's bound to, it may not be
# clear what class you're putting in the scope, or the arg_name-to-class
# binding could change later without you reconsidering whether the scope is
# appropriate for the new bound-to class.
#
# So it seems like @binds_to has to go, or else allow scoping, and since I'm
# putting scoping in only one place (the binding module), it has to go?
def binds_to(arg_name, annotated_with=None):
    def get_pinject_decorated_class(cls):
        if not hasattr(cls, _IS_DECORATED_ATTR):
            setattr(cls, _IS_DECORATED_ATTR, True)
            setattr(cls, _BOUND_TO_BINDING_KEYS_ATTR, [])
        getattr(cls, _BOUND_TO_BINDING_KEYS_ATTR).append(
            new_binding_key(arg_name, annotated_with))
        return cls
    return get_pinject_decorated_class


def _get_any_class_binding_keys(cls):
    if hasattr(cls, _IS_DECORATED_ATTR):
        return getattr(cls, _BOUND_TO_BINDING_KEYS_ATTR)
    else:
        return []


class BindingKey(object):
    """The key for a binding.

    Attributes:
      arg_name: the name of the bound arg

    TODO(kurts): think about adding behavior to BindingKey to have it fill in
    init_kwargs instead of making arg_name public.
    """

    def __repr__(self):
        return '<{0}>'.format(self)


def new_binding_key(arg_name, annotated_with=None):
    if annotated_with is not None:
        return BindingKeyWithAnnotation(arg_name, annotated_with)
    else:
        return BindingKeyWithoutAnnotation(arg_name)


class BindingKeyWithoutAnnotation(BindingKey):
    """A key with no annotation."""

    def __init__(self, arg_name):
        self.arg_name = arg_name

    def __eq__(self, other):
        return (isinstance(other, BindingKeyWithoutAnnotation) and
                self.arg_name == other.arg_name)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.arg_name)

    def __str__(self):
        return 'the arg name {0}'.format(self.arg_name)


class BindingKeyWithAnnotation(BindingKey):
    """A key with an annotation."""

    def __init__(self, arg_name, annotation):
        self.arg_name = arg_name
        self._annotation = annotation

    def __eq__(self, other):
        return (isinstance(other, BindingKeyWithAnnotation) and
                self.arg_name == other.arg_name and
                self._annotation == other._annotation)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.arg_name) ^ hash(self._annotation)

    def __str__(self):
        return 'the arg name {0} annotated with {1}'.format(
            self.arg_name, self._annotation)


class Binding(object):

    def __init__(self, binding_key, proviser_fn, scope_id=scoping.PROTOTYPE):
        self.binding_key = binding_key
        self.proviser_fn = proviser_fn
        self.scope_id = scope_id


def ProviderToProviser(provider_fn):
    return lambda binding_context, injector: provider_fn()


def get_binding_key_to_binding_maps(explicit_bindings, implicit_bindings):
    explicit_binding_key_to_binding = {}
    for binding in explicit_bindings:
        binding_key = binding.binding_key
        if binding_key in explicit_binding_key_to_binding:
            raise errors.ConflictingBindingsError(binding_key)
        explicit_binding_key_to_binding[binding_key] = binding

    implicit_binding_key_to_binding = {}
    collided_binding_key_to_bindings = {}
    for binding in implicit_bindings:
        binding_key = binding.binding_key
        if binding_key in explicit_binding_key_to_binding:
            continue
        if binding_key in implicit_binding_key_to_binding:
            existing_binding = implicit_binding_key_to_binding[binding_key]
            del implicit_binding_key_to_binding[binding_key]
            bindings = collided_binding_key_to_bindings.setdefault(
                binding_key, set())
            bindings.add(existing_binding)
        if binding_key in collided_binding_key_to_bindings:
            bindings = collided_binding_key_to_bindings[binding_key]
            bindings.add(binding)
        else:
            implicit_binding_key_to_binding[binding_key] = binding

    binding_key_to_binding = explicit_binding_key_to_binding
    binding_key_to_binding.update(implicit_binding_key_to_binding)
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
    return BindingContext(binding_key_stack=[], in_scope=scoping.UNSCOPED)


class BindingContext(object):

    def __init__(self, binding_key_stack, in_scope):
        self._binding_key_stack = binding_key_stack
        self._in_scope = in_scope

    def get_child(self, binding_key, scope):
        new_binding_key_stack = list(self._binding_key_stack)
        new_binding_key_stack.append(binding_key)
        if binding_key in self._binding_key_stack:
            raise errors.CyclicInjectionError(new_binding_key_stack)
        return BindingContext(new_binding_key_stack, scope)

    # TODO(kurts): this smells like a public attribute.  Maybe move
    # BindableScopes in here?
    def does_scope_match(self, does_scope_match_fn):
        return does_scope_match_fn(self._in_scope)


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


def get_explicit_bindings(classes, functions, scope_ids):
    explicit_bindings = []
    all_functions = list(functions)
    for cls in classes:
        for binding_key in _get_any_class_binding_keys(cls):
            proviser_fn = create_proviser_fn(binding_key, to_class=cls)
            explicit_bindings.append(Binding(binding_key, proviser_fn))
        for _, fn in inspect.getmembers(cls, lambda x: type(x) == types.FunctionType):
            all_functions.append(fn)
    for fn in all_functions:
        for provider_binding in wrapping.get_any_provider_bindings(fn):
            if provider_binding.scope_id not in scope_ids:
                raise errors.UnknownScopeError(provider_binding.scope_id)
            explicit_bindings.append(provider_binding)
    return explicit_bindings


def get_implicit_bindings(
    classes, functions,
    get_arg_names_from_class_name=(
        default_get_arg_names_from_class_name),
    get_arg_names_from_provider_fn_name=(
        providing.default_get_arg_names_from_provider_fn_name)):
    """Creates a mapping from arg names to classes.

    Args:
      classes: an iterable of classes
      get_arg_names_from_class_name: a function taking an (unqualified) class
          name and returning a (possibly empty) iterable of the arg names that
          would map to that class
    Returns:
      an _ArgNameClassMapping
    """
    implicit_bindings = []
    all_functions = list(functions)
    for cls in classes:
        if _get_any_class_binding_keys(cls):
            continue
        arg_names = get_arg_names_from_class_name(cls.__name__)
        for arg_name in arg_names:
            binding_key = BindingKeyWithoutAnnotation(arg_name)
            proviser_fn = create_proviser_fn(binding_key, to_class=cls)
            implicit_bindings.append(Binding(binding_key, proviser_fn))
        for _, fn in inspect.getmembers(cls, lambda x: type(x) == types.FunctionType):
            all_functions.append(fn)
    for fn in all_functions:
        if wrapping.get_any_provider_bindings(fn):
            continue
        arg_names = get_arg_names_from_provider_fn_name(fn.__name__)
        for arg_name in arg_names:
            binding_key = BindingKeyWithoutAnnotation(arg_name)
            proviser_fn = create_proviser_fn(binding_key, to_provider=fn)
            implicit_bindings.append(Binding(binding_key, proviser_fn))
    return implicit_bindings


class Binder(object):

    def __init__(self, collected_bindings, scope_ids):
        self._collected_bindings = collected_bindings
        self._scope_ids = scope_ids
        self._lock = threading.Lock()

    def bind(self, arg_name, annotated_with=None,
             to_class=None, to_instance=None, to_provider=None,
             in_scope=scoping.PROTOTYPE):
        if in_scope not in self._scope_ids:
            raise errors.UnknownScopeError(in_scope)
        binding_key = new_binding_key(arg_name, annotated_with)
        proviser_fn = create_proviser_fn(binding_key,
                                         to_class, to_instance, to_provider)
        with self._lock:
            self._collected_bindings.append(Binding(binding_key, proviser_fn, in_scope))


def create_proviser_fn(binding_key,
                       to_class=None, to_instance=None, to_provider=None):
    specified_to_params = ['to_class' if to_class is not None else None,
                           'to_instance' if to_instance is not None else None,
                           'to_provider' if to_provider is not None else None]
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
        return lambda binding_context, injector: injector._provide_class(
            to_class, binding_context)
    elif to_instance is not None:
        return ProviderToProviser(lambda: to_instance)
    else:  # to_provider is not None
        if not callable(to_provider):
            raise errors.InvalidBindingTargetError(
                binding_key, to_provider, 'callable')
        return lambda binding_context, injector: injector._call_with_injection(
            to_provider, binding_context)
