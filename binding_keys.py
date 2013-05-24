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


import annotation as annotation_lib


class BindingKey(object):
    """The key for a binding."""

    def __init__(self, arg_name, annotation):
        """Initializer.

        Args:
          arg_name: the name of the bound arg
          annotation: an Annotation
        """
        self._arg_name = arg_name
        self._annotation = annotation

    def __repr__(self):
        return '<{0}>'.format(self)

    def __str__(self):
        return 'the arg name "{0}" {1}'.format(
            self._arg_name, self._annotation.as_adjective())

    def __eq__(self, other):
        return (isinstance(other, BindingKey) and
                self._arg_name == other._arg_name and
                self._annotation == other._annotation)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self._arg_name) ^ hash(self._annotation)

    def can_apply_to_one_of_arg_names(self, arg_names):
        return self._arg_name in arg_names

    def conflicts_with_any_binding_key(self, binding_keys):
        return self._arg_name in [bk._arg_name for bk in binding_keys]

    def put_provided_value_in_kwargs(self, value, kwargs):
        kwargs[self._arg_name] = value


# TODO(kurts): Get a second opinion on module-level methods operating on
# internal state of classes.  In another language, this would be a static
# member and so allowed access to internals.
def get_unbound_arg_names(arg_names, arg_binding_keys):
    bound_arg_names = [bk._arg_name for bk in arg_binding_keys]
    return [arg_name for arg_name in arg_names
            if arg_name not in bound_arg_names]


def new(arg_name, annotated_with=None):
    if annotated_with is not None:
        annotation = annotation_lib.Annotation(annotated_with)
    else:
        annotation = annotation_lib.NO_ANNOTATION
    return BindingKey(arg_name, annotation)
