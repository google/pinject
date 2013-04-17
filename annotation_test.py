
import unittest

import annotation


class AnnotationTest(unittest.TestCase):

    def test_as_correct_adjective(self):
        self.assertEqual('annotated with "foo"',
                         annotation.Annotation('foo').as_adjective())

    def test_equal(self):
        self.assertEqual(annotation.Annotation('foo'), annotation.Annotation('foo'))
        self.assertEqual(hash(annotation.Annotation('foo')),
                         hash(annotation.Annotation('foo')))

    def test_not_equal(self):
        self.assertNotEqual(annotation.Annotation('foo'),
                            annotation.Annotation('bar'))
        self.assertNotEqual(hash(annotation.Annotation('foo')),
                            hash(annotation.Annotation('bar')))


class NoAnnotationTest(unittest.TestCase):

    def test_as_correct_adjective(self):
        self.assertEqual('unannotated', annotation._NoAnnotation().as_adjective())

    def test_equal(self):
        self.assertEqual(annotation._NoAnnotation(), annotation._NoAnnotation())
        self.assertEqual(hash(annotation._NoAnnotation()),
                         hash(annotation._NoAnnotation()))

    def test_not_equal(self):
        self.assertNotEqual(annotation._NoAnnotation(),
                            annotation.Annotation('bar'))
        self.assertNotEqual(hash(annotation._NoAnnotation()),
                            hash(annotation.Annotation('bar')))
