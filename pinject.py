import sys

import binding
BindingSpec = binding.BindingSpec

import errors
Error = errors.Error
for thing in dir(errors):
    if isinstance(thing, errors.Error):
        setattr(sys.modules(__name__), thing.__name__, thing)

import object_graph
new_object_graph = object_graph.new_object_graph

import scoping
PROTOTYPE = scoping.PROTOTYPE
Scope = scoping.Scope
SINGLETON = scoping.SINGLETON

import wrapping
annotate_arg = wrapping.annotate_arg
injectable = wrapping.injectable
provides = wrapping.provides
