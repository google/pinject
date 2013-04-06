#!/usr/bin/python

import traceback

import errors
import injecting


all_print_methods = []

def print_ambiguous_arg_name_error():
    class SomeClass():
        def __init__(self, foo):
            pass
    class Foo():
        pass
    class _Foo():
        pass
    injector = injecting.new_injector(classes=[SomeClass, Foo, _Foo])
    try:
        _ = injector.provide(SomeClass)
        raise Exception('failed to raise')
    except errors.AmbiguousArgNameError:
        traceback.print_exc()
all_print_methods.append(print_ambiguous_arg_name_error)

for print_method in all_print_methods:
    print '#' * 78
    print_method()
print '#' * 78
