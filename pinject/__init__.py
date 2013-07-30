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


import sys


__all__ = []
from .bindings import BindingSpec
__all__.extend(['BindingSpec'])
from .decorators import annotate_arg, inject, injectable, provides
__all__.extend(['annotate_arg', 'inject', 'injectable', 'provides'])
for thing_name in dir(errors):
    thing = getattr(errors, thing_name)
    if type(thing) == type(str):
        setattr(sys.modules[__name__], thing_name, thing)
        __all__.append(thing_name)
from .initializers import copy_args_to_internal_fields
from .initializers import copy_args_to_public_fields
from .object_graph import new_object_graph
__all__.extend(['new_object_graph'])
from .scoping import PROTOTYPE, Scope, SINGLETON
__all__.extend(['PROTOTYPE', 'Scope', 'SINGLETON'])

# TODO(kurts): figure out how to avoid breaking unittests by uncommenting this
#   section.
# this_module = sys.modules[__name__]
# for thing_name in dir(this_module):
#     if (thing_name != 'this_module' and
#         type(getattr(this_module, thing_name)) == type(this_module)):
#         delattr(this_module, thing_name)
# delattr(this_module, '__builtins__')
# delattr(this_module, 'thing_name')
# delattr(this_module, 'this_module')
