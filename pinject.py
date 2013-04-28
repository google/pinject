import sys

import errors
Error = errors.Error
for thing in dir(errors):
    if isinstance(thing, errors.Error):
        setattr(sys.modules(__name__), thing.__name__, thing)

import object_graph
new_object_graph = object_graph.new_object_graph

# TODO:
# - reasonable error messages for all exceptions
# - validate python types of all input
# - either allow binding specs to declare required bindings, or else declare
#     all entry points up front
# - standard tests for scopes (reentrant? thread-safe?), annotations (eq?
#      hash?), etc.

# Maybe TODO:
# - eager singletons
# - allow field injection
#     (lack of field docstrings is OK because they're the appropriate instances of that type)
#     (but get a second opinion on whether it decreases testability)
# - require/allow declaration of entry points
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
# - How should I deal with someone wanting to instantiate a class in a scope,
#     without using an arg name in between?  Scopes apply to binding keys,
#     which are arg names, not classes.  Is it going to be harmful if you
#     can't instantiate a class directly in a scope?  I don't think so, but
#     I'm not sure.  It makes some things awkward, like a special scope from
#     which it's OK to inject objects from any scope.  Maybe the main
#     ObjectGraph method should be wrap() instead of provide_class()??
# - Remove ObjectGraph.wrap()?
# - Why should @inject apply to __init__() rather than the class?
# - What's the advantage of making the user list entry points in order to
#     validate the object graph, instead of, say, doing it the Guice way with
#     require()?
