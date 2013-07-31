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


def get_loc(thing):
    try:
        return '{0}:{1}'.format(
            inspect.getfile(thing), inspect.getsourcelines(thing)[1])
    except (TypeError, IOError):
        return 'unknown location'


def get_name_and_loc(thing):
    try:
        if hasattr(thing, 'im_class'):
            class_name = '{0}.{1}'.format(
                thing.im_class.__name__, thing.__name__)
        else:
            class_name = '{0}.{1}'.format(
                inspect.getmodule(thing).__name__, thing.__name__)
    except (TypeError, IOError):
        class_name = '{0}.{1}'.format(
            inspect.getmodule(thing).__name__, thing.__name__)
    try:
        return '{0} at {1}:{2}'.format(class_name, inspect.getfile(thing),
                                       inspect.getsourcelines(thing)[1])
    except (TypeError, IOError) as e:
        return class_name


def get_back_frame_loc():
    back_frame = inspect.currentframe().f_back.f_back
    return '{0}:{1}'.format(back_frame.f_code.co_filename,
                            back_frame.f_lineno)
