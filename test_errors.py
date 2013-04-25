#!/usr/bin/python

import traceback

import errors
import object_graph


all_print_methods = []


def print_ambiguous_arg_name_error():
    class SomeClass():
        def __init__(self, foo):
            pass
    class Foo():
        pass
    class _Foo():
        pass
    injector = object_graph.new_injector(classes=[SomeClass, Foo, _Foo])
    try:
        _ = injector.provide(SomeClass)
        raise Exception('failed to raise')
    except errors.AmbiguousArgNameError:
        traceback.print_exc()
all_print_methods.append(print_ambiguous_arg_name_error)


def print_bad_dependency_scope_error():
    class Foo(object):
        pass
    class Bar(object):
        def __init__(self, foo):
            pass
    injector = object_graph.new_injector(
        classes=[Foo, Bar], is_scope_usable_from_scope=lambda _1, _2: False)
    try:
        _ = injector.provide(Bar)
        raise Exception('failed to raise')
    except errors.BadDependencyScopeError:
        traceback.print_exc()
all_print_methods.append(print_bad_dependency_scope_error)


def print_conflicting_bindings_error():
    def binding_fn(bind):
        bind('foo', to_instance=1)
        bind('foo', to_instance=2)
    try:
        _ = object_graph.new_injector(binding_fns=[binding_fn])
        raise Exception('failed to raise')
    except errors.ConflictingBindingsError:
        traceback.print_exc()
all_print_methods.append(print_conflicting_bindings_error)


for print_method in all_print_methods:
    print '#' * 78
    print_method()
print '#' * 78
