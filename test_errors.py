#!/usr/bin/python

"""Copyright 2013 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


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
    obj_graph = object_graph.new_object_graph(classes=[SomeClass, Foo, _Foo])
    try:
        _ = obj_graph.provide(SomeClass)
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
    obj_graph = object_graph.new_object_graph(
        classes=[Foo, Bar], is_scope_usable_from_scope=lambda _1, _2: False)
    try:
        _ = obj_graph.provide(Bar)
        raise Exception('failed to raise')
    except errors.BadDependencyScopeError:
        traceback.print_exc()
all_print_methods.append(print_bad_dependency_scope_error)


def print_conflicting_bindings_error():
    def binding_fn(bind):
        bind('foo', to_instance=1)
        bind('foo', to_instance=2)
    try:
        _ = object_graph.new_object_graph(binding_fns=[binding_fn])
        raise Exception('failed to raise')
    except errors.ConflictingBindingsError:
        traceback.print_exc()
all_print_methods.append(print_conflicting_bindings_error)


for print_method in all_print_methods:
    print '#' * 78
    print_method()
print '#' * 78
