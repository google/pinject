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

LOCALS_TOKEN = '<locals>'


def get_loc(thing):
    try:
        return '{0}:{1}'.format(
            inspect.getfile(thing), inspect.getsourcelines(thing)[1])
    except (TypeError, IOError):
        return 'unknown location'


def get_name_and_loc(thing):
    try:
        type_name = _get_type_name(thing)
        class_name = '{0}.{1}'.format(type_name, thing.__name__)
    except (TypeError, IOError):
        class_name = '{0}.{1}'.format(
            inspect.getmodule(thing).__name__, thing.__name__)
    try:
        return '{0} at {1}:{2}'.format(class_name, inspect.getfile(thing),
                                       inspect.getsourcelines(thing)[1])
    except (TypeError, IOError):
        return class_name


def get_back_frame_loc():
    back_frame = inspect.currentframe().f_back.f_back
    return '{0}:{1}'.format(back_frame.f_code.co_filename,
                            back_frame.f_lineno)


def _get_type_name(target_thing):
    """
    Functions, bound methods and unbound methods change significantly in Python 3.

    For instance:

    class SomeObject(object):
        def method():
            pass

    In Python 2:
    - Unbound method inspect.ismethod(SomeObject.method) returns True
    - Unbound inspect.isfunction(SomeObject.method) returns False
    - Unbound hasattr(SomeObject.method, 'im_class') returns True
    - Bound method inspect.ismethod(SomeObject().method) returns True
    - Bound method inspect.isfunction(SomeObject().method) returns False
    - Bound hasattr(SomeObject().method, 'im_class') returns True

    In Python 3:
    - Unbound method inspect.ismethod(SomeObject.method) returns False
    - Unbound inspect.isfunction(SomeObject.method) returns True
    - Unbound hasattr(SomeObject.method, 'im_class') returns False
    - Bound method inspect.ismethod(SomeObject().method) returns True
    - Bound method inspect.isfunction(SomeObject().method) returns False
    - Bound hasattr(SomeObject().method, 'im_class') returns False

    This method tries to consolidate the approach for retrieving the
    enclosing type of a bound/unbound method and functions.
    """
    thing = target_thing
    if hasattr(thing, 'im_class'):
        # only works in Python 2
        return thing.im_class.__name__
    if inspect.ismethod(thing):
        for cls in inspect.getmro(thing.__self__.__class__):
            if cls.__dict__.get(thing.__name__) is thing:
                return cls.__name__
        thing = thing.__func__
    if inspect.isfunction(thing) and hasattr(thing, '__qualname__'):
        qualifier = thing.__qualname__
        if LOCALS_TOKEN in qualifier:
            return _get_local_type_name(thing)
        return _get_external_type_name(thing)
    return inspect.getmodule(target_thing).__name__


def _get_local_type_name(thing):
    qualifier = thing.__qualname__
    parts = qualifier.split(LOCALS_TOKEN, 1)
    type_name = parts[1].split('.')[1]
    if thing.__name__ == type_name:
        return inspect.getmodule(thing).__name__
    return type_name


def _get_external_type_name(thing):
    qualifier = thing.__qualname__
    name = qualifier.rsplit('.', 1)[0]
    if hasattr(inspect.getmodule(thing), name):
        cls = getattr(inspect.getmodule(thing), name)
        if isinstance(cls, type):
            return cls.__name__
    return inspect.getmodule(thing).__name__
