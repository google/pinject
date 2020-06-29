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


import inspect
import sys


ALL_IMPORTED_MODULES = object()


def find_classes(modules, classes):
    if classes is not None:
        all_classes = set(classes)
    else:
        all_classes = set()
    for module in _get_explicit_or_default_modules(modules):
        # TODO(kurts): how is a module getting to be None??
        if module is not None:
            all_classes |= _find_classes_in_module(module)
    return all_classes


def _get_explicit_or_default_modules(modules):
    if modules is ALL_IMPORTED_MODULES:
        return list(sys.modules.values())
    elif modules is None:
        return []
    return modules


def _find_classes_in_module(module):
    classes = set()

    try:
        # Handle find_classes_in_module when module.__bases__ is not a tuple:
        #   https://github.com/google/pinject/pull/54
        #
        # modules, such tensorboard.compat.tensorflow_stub (2.2.2) return the
        # __bases__ attribute as an integer, instead of the expected tuple
        #
        # when the inspect.getmembers() function attemps to iterate through it
        # an error is raised
        #
        # this pre-empts this error, by assigning an empty tuple to avoid TypeError
        if not isinstance(module.__bases__, tuple):
            module.__bases__ = ()
    except AttributeError:
        pass

    for member_name, member in inspect.getmembers(module):
        try:
            if inspect.isclass(member) and not member_name == '__class__':
                classes.add(member)
        except NameError:
            # In Python 3 calling isinstance() on SWIG's global cvar property
            # raises:
            #     "NameError: Unknown C global variable"
            # In that case just continue, otherwise let the Error through.
            if not member_name == 'cvar':
                raise
    return classes
