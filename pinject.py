import sys

import errors
Error = errors.Error
for thing in dir(errors):
    if isinstance(thing, errors.Error):
        setattr(sys.modules(__name__), thing.__name__, thing)

import injecting
new_injector = injecting.new_injector

# TODO:
# - eager singletons
# - reasonable error messages for all exceptions

# Maybe TODO:
# - allow field injection
#     (lack of field docstrings is OK because they're the appropriate instances of that type)
#     (but get a second opinion on whether it decreases testability)
# - find modules on PYTHONPATH instead of having to import them
# - automatically instantiate the concrete subclass of an interface?
#     (it is possible to determine that something is abstract?)
# - untargetted bindings?  http://code.google.com/p/google-guice/wiki/UntargettedBindings
# - @ImplementedBy, @ProvidedBy  http://code.google.com/p/google-guice/wiki/JustInTimeBindings
# - other stuff: http://code.google.com/p/google-guice/wiki/Motivation
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
#     I'm not sure.  It makes some things awkward, like a special scope from
#     which it's OK to inject objects from any scope.  Maybe the main
#     _Injector method should be wrap() instead of provide_class()??
# - It seems like Guice and others don't have a problem with object A from
#     singleton scope getting injected with object B from prototype scope.  Is
#     that because you may just need one of something, and it's immutable, so
#     you can create them with impunity?  And: is it good to have a feature
#     that limits what scopes are usable from what other scopes?  For
#     instance, I'd want to make sure that I never created a singleton that
#     included a request-scoped instance.
# - Remove _Injector.wrap()?
# - In safe mode, where initializers must have @inject to be injected, should
#     that also apply to classes whose only initializer param is self?  It
#     seems like Guice makes an exception in this case.  Why?
# - Should @inject conflict with an explicit binding in a binding function?
#     @inject creates a binding from the class's corresponding arg name(s) to
#     the class, in the default scope.  But isn't that the same as @binds_to?
#     Why is it OK to mark a class injectable with @inject?  Doesn't that make
#     two places you have to look to see if a class is injectable?
# - Why should @inject apply to __init__() rather than the class?
