
# TODO(kurts): make all errors be named the same part(s) of speech.


class Error(Exception):
    pass


class AmbiguousArgNameError(Error):

    def __init__(self, binding_key, bindings):
        Error.__init__(
            self, '{0} ambiguously refers to any of {1}'.format(
                binding_key, bindings))


class BadDependencyScopeError(Error):

    def __init__(self, to_scope, from_scope, binding_key_stack):
        Error.__init__(
            self, 'scope {0} is not usable from scope {1} when injecting'
            ' {2}'.format(to_scope, from_scope, binding_key_stack))


class CannotOverrideDefaultScopeError(Error):

    def __init__(self, scope_id):
        Error.__init__(
            self, 'cannot override default scope {0}'.format(scope_id))


class ConflictingBindingsError(Error):

    def __init__(self, binding_key):
        Error.__init__(
            self, 'multiple conflicting bindings for {0}'.format(binding_key))


class CyclicInjectionError(Error):
    pass


class InvalidBindingTargetError(Error):

    def __init__(self, binding_key, binding_target, expected_type_str):
        Error.__init__(
            self, '{0} cannot be bound to {1} because the latter is not a'
            ' {2}'.format(binding_key, binding_target, expected_type_str))


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


class NothingInjectableForArgError(Error):

    def __init__(self, binding_key):
        Error.__init__(
            self, 'there is no injectable class for {0}'.format(binding_key))


class UnknownScopeError(Error):

    def __init__(self, scope_id):
        Error.__init__(self, 'no such scope with ID {0}'.format(scope_id))
