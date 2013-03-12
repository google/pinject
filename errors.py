

class Error(Exception):
    pass


class AmbiguousArgNameError(Error):

    def __init__(self, binding_key, provider_fns):
        Error.__init__(
            self, '{0} ambiguously refers to any of {1}'.format(
                binding_key, provider_fns))


class ConflictingBindingsError(Error):

    def __init__(self, binding_key):
        Error.__init__(
            self, 'multiple conflicting bindings for {0}'.format(binding_key))


class InjectorNotYetInstantiatedError(Error):
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


class NothingInjectableForArgNameError(Error):

    def __init__(self, binding_key):
        Error.__init__(
            self, 'there is no injectable class for {0}'.format(binding_key))
