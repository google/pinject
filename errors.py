

class Error(Exception):
    pass


class AmbiguousArgNameError(Error):

    def __init__(self, binding_key, class_names):
        Error.__init__(
            self, '{0} ambiguously refers to any of the classes {1}'.format(
                binding_key, class_names))


class NothingInjectableForArgNameError(Error):

    def __init__(self, binding_key):
        Error.__init__(
            self, 'there is no injectable class for {0}'.format(binding_key))


class ConflictingBindingsError(Error):

    def __init__(self, binding_key):
        Error.__init__(
            self, 'multiple conflicting bindings for {0}'.format(binding_key))
