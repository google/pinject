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


from . import binding_keys
from . import locations


class RequiredBinding(object):

    def __init__(self, binding_key, require_loc):
        self.binding_key = binding_key
        self.require_loc = require_loc


class RequiredBindings(object):

    def __init__(self):
        self._req_bindings = []

    def require(self, arg_name, annotated_with=None):
        self._req_bindings.append(RequiredBinding(
            binding_keys.new(arg_name, annotated_with),
            locations.get_back_frame_loc()))

    def get(self):
        return self._req_bindings
