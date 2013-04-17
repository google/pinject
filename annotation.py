

class Annotation(object):

    def __init__(self, annotation_obj):
        self._annotation_obj = annotation_obj

    def as_adjective(self):
        return 'annotated with "{0}"'.format(self._annotation_obj)

    def __eq__(self, other):
        return (isinstance(other, Annotation) and
                self._annotation_obj == other._annotation_obj)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self._annotation_obj)


class _NoAnnotation(object):

    def as_adjective(self):
        return 'unannotated'

    def __eq__(self, other):
        return isinstance(other, _NoAnnotation)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return 0


_NO_ANNOTATION = _NoAnnotation()
