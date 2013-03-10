

class Error(Exception):
    pass


class AmbiguousArgNameError(Error):
    pass


class NothingInjectableForArgNameError(Error):
    pass


class UnknownProvideIdentifierError(Error):
    pass
