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


import six
import collections
import inspect

from . import errors


def items(dict_instance):
    return six.iteritems(dict_instance)


def is_sequence(arg_value):
    return isinstance(arg_value, collections.Sequence)


def is_string(arg_value):
    return isinstance(arg_value, six.string_types)


def is_constructor_defined(cls):
    if six.PY3:
        return inspect.isfunction(cls.__init__)
    return inspect.ismethod(cls.__init__)


def verify_callable(fn, arg_name):
    if not callable(fn):
        raise errors.WrongArgTypeError(arg_name, 'callable', type(fn).__name__)


def verify_subclasses(seq, required_superclass, arg_name):
    if not isinstance(seq, collections.Sequence):
        raise errors.WrongArgTypeError(
            arg_name,
            'sequence (of subclasses of {0})'.format(
                required_superclass.__name__),
            type(seq).__name__)
    for idx, elt in enumerate(seq):
        if not isinstance(elt, required_superclass):
            raise errors.WrongArgElementTypeError(
                arg_name, idx,
                'subclass of {0}'.format(required_superclass.__name__),
                type(elt).__name__)


def verify_module_types(modules, arg_name):
    _verify_types(inspect.ismodule, modules, arg_name, 'module')


def verify_class_types(seq, arg_name):
    _verify_types(inspect.isclass, seq, arg_name, 'class')


def verify_class_type(elt, arg_name):
    _verify_type(inspect.isclass, elt, arg_name, 'class')


def _assert_sequence(seq, arg_name, type_name):
    if not is_sequence(seq):
        raise errors.WrongArgTypeError(
            arg_name, 'sequence (of {0})'.format(type_name), type(seq).__name__)


def _verify_types(fn_checker, seq, arg_name, type_name):
    _assert_sequence(seq, arg_name, type_name)
    for idx, elt in enumerate(seq):
        if not fn_checker(elt):
            raise errors.WrongArgElementTypeError(
                arg_name, idx, type_name, type(elt).__name__)


def _verify_type(fn_checker, elt, arg_name, type_name):
    if not fn_checker(elt):
        raise errors.WrongArgTypeError(
            arg_name, type_name, type(elt).__name__)