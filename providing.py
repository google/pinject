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


_PROVIDER_FN_PREFIX = 'provide_'


def default_get_arg_names_from_provider_fn_name(provider_fn_name):
    if provider_fn_name.startswith(_PROVIDER_FN_PREFIX):
        return [provider_fn_name[len(_PROVIDER_FN_PREFIX):]]
    else:
        return []
