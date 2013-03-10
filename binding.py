

class BindingKey(object):
    """The key for a binding."""

    pass


class BindingKeyWithoutAnnotation(BindingKey):
    """A key with no annotation."""

    def __init__(self, arg_name):
        self._arg_name = arg_name

    def __eq__(self, other):
        return (isinstance(other, BindingKeyWithoutAnnotation) and
                self._arg_name == other._arg_name)

    def __hash__(self):
        return hash(self._arg_name)


class BindingKeyWithAnnotation(BindingKey):
    """A key with an annotation."""

    def __init__(self, arg_name, annotation):
        self._arg_name = arg_name
        self._annotation = annotation

    def __eq__(self, other):
        return (isinstance(other, BindingKeyWithoutAnnotation) and
                self._arg_name == other._arg_name and
                self._annotation == other._annotation)

    def __hash__(self):
        return hash(self._arg_name) ^ hash(self._annotation)


class Binding(object):

    def __init__(self, binding_key, provider_fn):
        self._binding_key = binding_key
        self._provider_fn = provider_fn

    def has_key(self, binding_key):
        return self._binding_key == binding_key


class BindingSet(object):

    def __init__(self, bindings=None):
        if bindings:
            self._bindings = list(bindings)
        else:
            self._bindings = []


class Binder(object):

    def bind(self, arg_name, annotated_with=None,
             to_class=None, to_provider=None, to_instance=None,
             in_scope=None):
        # to_provider, in Guice, gives "a class where an instance of the class
        # is resolved in the regular way".  I think that's going to change if
        # to_provider takes a function.  Is that bad?  It seems bad only if
        # the function itself can't have its args injected.  But as long as
        # the function can have its args injected, it's just like a provider
        # class that's instantiated with injected constructor args.  It does
        # mean that Binder has to have a way to say "this function gets
        # injected params".
        raise NotImplementedError()

    def wrap_injecting_params(self, fn):
        raise NotImplementedError()


class BindingsBuilder(Binder):

    def __init__(self, injector, preexisting_bindings):
        self._preexisting_bindings = []  # TODO(kurts): or ask injector?
        self._injector = injector

        # TODO(kurts): separate out mutable fields.
        self._bindings = []
        self._lock = threading.Lock()

    def _is_key_bound(self, binding_key):
        for binding in (self._preexisting_bindings + self._bindings):
            if binding.has_key(binding_key):
                return True
        return False

    def bind(self, arg_name, annotated_with=None,
             to_class=None, to_provider=None, to_instance=None,
             in_scope=None):
        if not isinstance(arg_name, str) or not arg_name:
            raise InvalidArgNameError(arg_name)
        if annotated_with is not None:
            binding_key = BindingKeyWithAnnotation(arg_name, annotated_with)
        else:
            binding_key = BindingKeyWithoutAnnotation(arg_name)
        specified_to_params = ['to_class' if to_class is not None else None,
                               'to_provider' if to_provider is not None else None,
                               'to_instance' if to_instance is not None else None]
        specified_to_params = [x for x in specified_to_params if x is not None]
        if not specified_to_params:
            # TODO(kurts): is "binding target" the best name here?
            raise NoBindingTargetError()
        elif len(specified_to_params) > 1:
            raise MultipleBindingTargetsError(specified_to_params)
        if to_class is not None:
            if not isinstance(to_class, type):
                raise InvalidBindingTargetError(to_class)
            provider_fn = lambda: self._injector.provide(to_class, annotated_with)
        elif to_provider is not None:
            if not callable(to_provider):
                raise InvalidBindingTargetError(to_provider)
            provider_fn = to_provider
        elif to_instance is not None:
            provider_fn = lambda: to_instance

        with self._lock:
            if self._is_key_bound(binding_key):
                raise AlreadyBoundError(binding_key)
            self._bindings.append(Binding(binding_key, provider_fn))

    def wrap_injecting_params(self, fn):
        return self._injector.wrap_injecting_params(fn)

    def get_bindings(self):
        with self._lock:
            return list(self._bindings)
