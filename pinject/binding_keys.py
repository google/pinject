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


from . import annotations


class BindingKey(object):
    """The key for a binding."""

    def __init__(self, name, annotation):
        """Initializer.

        Args:
          name: the name of the bound arg
          annotation: an Annotation
        """
        self._name = name
        self._annotation = annotation

    def __repr__(self):
        return '<{0}>'.format(self)

    def __str__(self):
        return 'the binding name "{0}" ({1})'.format(
            self._name, self.annotation_as_adjective())

    def annotation_as_adjective(self):
        return self._annotation.as_adjective()

    def __eq__(self, other):
        return (isinstance(other, BindingKey) and
                self._name == other._name and
                self._annotation == other._annotation)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self._name) ^ hash(self._annotation)


def new(arg_name, annotated_with=None):
    """Creates a BindingKey.

    Args:
      arg_name: the name of the bound arg
      annotation: an Annotation, or None to create an unannotated binding key
    Returns:
      a new BindingKey
    """
    if annotated_with is not None:
        annotation = annotations.Annotation(annotated_with)
    else:
        annotation = annotations.NO_ANNOTATION
    return BindingKey(arg_name, annotation)
