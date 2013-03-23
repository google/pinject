import sys

import errors
Error = errors.Error
for thing in dir(errors):
    if isinstance(thing, errors.Error):
        setattr(sys.modules(__name__), thing.__name__, thing)

import injecting
new_injector = injecting.new_injector


# class Scope(object):
#     """The interface for a scope."""

#     # Guice returns a provider
#     # http://code.google.com/p/google-guice/source/browse/core/src/com/google/inject/Scope.java
#     # Why?
#     def provide(self, arg_name, annotation):
#         raise NotImplementedError()

#     # def enter_scope(self, name, scope):
#     #     """Enters an injection scope.

#     #     Args:
#     #       name: the scope name
#     #       scope: a concrete Scope implementation
#     #     Raises:
#     #       AlreadyInScopeError: there is already an entered-but-not-left scope
#     #           with the same name
#     #     """
#     #     pass

#     # def leave_scope(self, name):
#     #     """Leaves an injection scope.

#     #     Args:
#     #       name: the scope name
#     #     Raises:
#     #       NotInScopeError: there is no entered-but-not-left scope with that
#     #           name
#     #     """
#     #     pass


# class MapBackedScope(Scope):

#     def __init__(self):
#         pass

#     def provide_from_arg_name(self, arg_name, class_name):
#         pass


# TODO:
# - allow field injection
#     (lack of field docstrings is OK because they're the appropriate instances of that type)
#     (but get a second opinion on whether it decreases testability)
#
# - only inject if a class is marked as injectable
# - safe vs. unsafe mode
# - find modules on PYTHONPATH instead of having to import them
#
# - auto-inject into provider functions (already done?)
# - allow classes to be annotated so that they only inject into annotated args
# - automatically instantiate the concrete subclass of an interface?
#     (it is possible to determine that something is abstract?)
#
# - scopes
#   - when providing (highest priority)
#   - in module
#   - annotated on provider
#   - annotated on class (lowest priority)
#   - eager singletons
#   - error-checking for deps from one scope to another
#
# - untargetted bindings?  http://code.google.com/p/google-guice/wiki/UntargettedBindings
# - @ImplementedBy, @ProvidedBy  http://code.google.com/p/google-guice/wiki/JustInTimeBindings
# - other stuff: http://code.google.com/p/google-guice/wiki/Motivation
# - refuse to inject None
# - visual graph of created objects

# http://code.google.com/p/google-guice/wiki/Motivation

# source:
# http://code.google.com/p/google-guice/source/browse/#git%2Fcore%2Fsrc%2Fcom%2Fgoogle%2Finject%253Fstate%253Dclosed

# Questions:
# - Why does Guice allow provider bindings and @provider functions, both in modules?  @provider is convenient?
# - Is there any reason not to allow @provider functions to be located anywhere, instead of just in modules?
