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


import decorator

from . import errors
from . import support


def copy_args_to_internal_fields(fn):
    """Copies the initializer args to internal member fields.

    This is a decorator that applies to __init__.
    """
    return _copy_args_to_fields(fn, 'copy_args_to_internal_fields', '_')


def copy_args_to_public_fields(fn):
    """Copies the initializer args to public member fields.

    This is a decorator that applies to __init__.
    """
    return _copy_args_to_fields(fn, 'copy_args_to_public_fields', '')


def _copy_args_to_fields(fn, decorator_name, field_prefix):
    if fn.__name__ != '__init__':
        raise errors.DecoratorAppliedToNonInitError(
            decorator_name, fn)
    arg_names, varargs, unused_keywords, unused_defaults = (
        support.get_method_args(fn))
    if varargs is not None:
        raise errors.PargsDisallowedWhenCopyingArgsError(
            decorator_name, fn, varargs)

    def CopyThenCall(fn_to_wrap, self, *pargs, **kwargs):
        for index, parg in enumerate(pargs, start=1):
            setattr(self, field_prefix + arg_names[index], parg)
        for kwarg, kwvalue in support.items(kwargs):
            setattr(self, field_prefix + kwarg, kwvalue)
        fn_to_wrap(self, *pargs, **kwargs)

    return decorator.decorator(CopyThenCall, fn)
