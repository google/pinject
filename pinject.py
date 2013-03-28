import sys

import errors
Error = errors.Error
for thing in dir(errors):
    if isinstance(thing, errors.Error):
        setattr(sys.modules(__name__), thing.__name__, thing)

import injecting
new_injector = injecting.new_injector

# TODO:
# - allow field injection
#     (lack of field docstrings is OK because they're the appropriate instances of that type)
#     (but get a second opinion on whether it decreases testability)
#
# - only inject if a class is marked as injectable
# - safe vs. unsafe mode
# - find modules on PYTHONPATH instead of having to import them
#
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
# - don't allow broader scopes to inject stuff from narrower scopes
# - check that scopes exist when processing binding functions
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
# - Why does Guice allow provider bindings and @provider functions, both in
#     modules?  @provider is convenient?
# - Is there any reason not to allow @provider functions to be located
#     anywhere, instead of just in binding modules?
# - Should "singleton" be the default scope?  It's what I use most often.  And
#     it seems like having "prototype" be the default scope means that I'll
#     accidentally create multiple objects where I should have used just one
#     more often, because the code will work, albeit slower (e.g., with RPC
#     connections).
# - TODO above @binds_to.
# - Should I allow bind(arg_name, to_scope) without saying what it's bound to?
# - Should I allow users to override the default scope?  (I'm assuming not.)
# - How should I deal with someone wanting to instantiate a class in a scope,
#     without using an arg name in between?  Scopes apply to binding keys,
#     which are arg names, not classes.  Is it going to be harmful if you
#     can't instantiate a class directly in a scope?  I don't think so, but
#     I'm not sure.
