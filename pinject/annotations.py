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


class Annotation(object):
    """A binding annotation."""

    def __init__(self, annotation_obj):
        """Initializer.

        Args:
          annotation_obj: the annotation object, which can be any object that
              implements __eq__() and __hash__()
        """
        self._annotation_obj = annotation_obj

    def as_adjective(self):
        """Returns the annotation as an adjective phrase.

        For example, if the annotation object is '3', then the annotation
        adjective phrase is 'annotated with "3"'.

        Returns:
          an annotation adjective phrase
        """
        return 'annotated with "{0}"'.format(self._annotation_obj)

    def __repr__(self):
        return '<{0}>'.format(self.as_adjective())

    def __eq__(self, other):
        return (isinstance(other, Annotation) and
                self._annotation_obj == other._annotation_obj)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self._annotation_obj)


class _NoAnnotation(object):
    """A polymorph for Annotation but that actually means "no annotation"."""

    def as_adjective(self):
        return 'unannotated'

    def __repr__(self):
        return '<{0}>'.format(self.as_adjective())

    def __eq__(self, other):
        return isinstance(other, _NoAnnotation)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return 0


NO_ANNOTATION = _NoAnnotation()
