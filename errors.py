

class Error(Exception):
    pass


class AmbiguousArgNameError(Error):

    def __init__(self, binding_key, bindings):
        Error.__init__(
            self, '{0} ambiguously refers to any of:\n{1}'.format(
                binding_key, '\n'.join('  {0}'.format(b.proviser_fn._pinject_desc) for b in bindings)))


class BadDependencyScopeError(Error):

    def __init__(self, to_scope_id, binding_key, binding_context):
        Error.__init__(
            self, 'scope "{0}" is not usable when binding {1} from'
            ' {2}'.format(to_scope_id, binding_key, binding_context))


class ConflictingBindingsError(Error):

    def __init__(self, colliding_bindings):
        Error.__init__(
            self, 'multiple bindings for same arg name:\n{0}'.format(
                '\n'.join('  {0}'.format(b) for b in colliding_bindings)))


class CyclicInjectionError(Error):
    pass


class InjectDecoratorAppliedToNonInitError(Error):

    def __init__(self, fn):
        Error.__init__(
            self, '@inject cannot be applied to non-initializer {0}'.format(fn.__name__))


class InjectingNoneDisallowedError(Error):

    def __init__(self):
        Error.__init__(
            self, 'cannot inject None because allow_injecting_none=False')


class InvalidBindingTargetError(Error):

    def __init__(self, binding_key, binding_target, expected_type_str):
        Error.__init__(
            self, '{0} cannot be bound to {1} because the latter is not a'
            ' {2}'.format(binding_key, binding_target, expected_type_str))


class InvalidProviderFnError(Error):

    def __init__(self, fn):
        Error.__init__(
            self, 'function {0} is not a provider function, though it was'
            ' passed to new_injector() in provider_fns'.format(fn))


class MultipleAnnotationsForSameArgError(Error):

    def __init__(self, arg_name):
        Error.__init__(
            self, 'multiple annotations for arg {0}'.format(arg_name))


class MultipleBindingTargetsError(Error):

    def __init__(self, binding_key, specified_to_params):
        Error.__init__(
            self, 'multiple binding targets {0} given for {1}'.format(
                specified_to_params, binding_key))


class NoBindingTargetError(Error):

    def __init__(self, binding_key):
        Error.__init__(
            self, 'no binding target given for {0}'.format(binding_key))


class NoSuchArgToInjectError(Error):

    def __init__(self, arg_name, fn):
        Error.__init__(
            self, 'no such arg {0} to inject into {1}'.format(arg_name, fn))


class NonExplicitlyBoundClassError(Error):

    def __init__(self, cls):
        Error.__init__(
            self, 'cannot instantiate class {0}, which is not explicitly'
            ' marked as injectable, when only_use_explicit_bindings is set'
            ' to True'.format(cls.__name__))


class NothingInjectableForArgError(Error):

    def __init__(self, binding_key):
        Error.__init__(
            self, 'there is no injectable class for {0}'.format(binding_key))


class OverridingDefaultScopeError(Error):

    def __init__(self, scope_id):
        Error.__init__(
            self, 'cannot override default scope {0}'.format(scope_id))


class UnknownScopeError(Error):

    def __init__(self, scope_id):
        Error.__init__(self, 'no such scope with ID {0}'.format(scope_id))
