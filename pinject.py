# - why use @Inject instead of assuming all classes are eligible for JIT binding?
# - why prefer provider methods to binding instances when instances are complicated to create?
#     http://code.google.com/p/google-guice/wiki/InstanceBindings
# - where should Real Work go, when creating an instance?
#     http://code.google.com/p/google-guice/wiki/ModulesShouldBeFastAndSideEffectFree
# - should modules install other modules?
#     - assuming not, how do you update all consumers?  all main modules manually?!
# - why is it so bad to have providers throw exceptions?
#     - it is just the java crap with checked exceptions?

import errors
Error = errors.Error
AmbiguousArgNameError = errors.AmbiguousArgNameError
NothingInjectableForArgNameError = errors.NothingInjectableForArgNameError
ConflictingBindingsError = errors.ConflictingBindingsError

import injecting
NewInjector = injecting.NewInjector


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
# - move human-readable error strings into Error subclasses
# - allow explicit declared bindings
# - provider functions
# - instance bindings
# - allow declared bindings at initializer sites
# - only inject if a class is marked as injectable
# - safe vs. unsafe mode
# - annotations
# - automatically instantiate the concrete subclass of an interface?
#     (it is possible to determine that something is abstract?)
# - find modules on PYTHONPATH instead of having to import them
# - allow named bindings
# - scopes
#   - when providing (highest priority)
#   - in module
#   - annotated on provider
#   - annotated on class (lowest priority)
#   - eager singletons
#   - error-checking for deps from one scope to another
# - untargetted bindings?  http://code.google.com/p/google-guice/wiki/UntargettedBindings
# - @ImplementedBy, @ProvidedBy  http://code.google.com/p/google-guice/wiki/JustInTimeBindings
# - other stuff: http://code.google.com/p/google-guice/wiki/Motivation
# - refuse to inject None
# - graph of created objects

# http://code.google.com/p/google-guice/wiki/Motivation

# source:
# http://code.google.com/p/google-guice/source/browse/#git%2Fcore%2Fsrc%2Fcom%2Fgoogle%2Finject%253Fstate%253Dclosed

# The two things that straight Guice-to-python ports miss are:
#   - python has first-class functions (with which Guice does nothing); and
#   - python has no static type info (without which straight ports mandate explicit substitutes).
