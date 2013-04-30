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
