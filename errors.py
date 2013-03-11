

class Error(Exception):
    pass


class AmbiguousArgNameError(Error):
    pass


class NothingInjectableForArgNameError(Error):
    pass


class UnknownProvideIdentifierError(Error):  # TODO(kurts): delete?
    pass


class ConflictingBindingsError(Error):
    pass
