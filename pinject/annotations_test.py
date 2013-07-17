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

from pinject import annotations


class AnnotationTest(unittest.TestCase):

    def test_as_correct_adjective(self):
        self.assertEqual('annotated with "foo"',
                         annotations.Annotation('foo').as_adjective())
        self.assertEqual('<annotated with "foo">',
                         repr(annotations.Annotation('foo')))

    def test_equal(self):
        self.assertEqual(annotations.Annotation('foo'),
                         annotations.Annotation('foo'))
        self.assertEqual(hash(annotations.Annotation('foo')),
                         hash(annotations.Annotation('foo')))

    def test_not_equal(self):
        self.assertNotEqual(annotations.Annotation('foo'),
                            annotations.Annotation('bar'))
        self.assertNotEqual(hash(annotations.Annotation('foo')),
                            hash(annotations.Annotation('bar')))


class NoAnnotationTest(unittest.TestCase):

    def test_as_correct_adjective(self):
        self.assertEqual('unannotated',
                         annotations._NoAnnotation().as_adjective())
        self.assertEqual('<unannotated>', repr(annotations._NoAnnotation()))

    def test_equal(self):
        self.assertEqual(annotations._NoAnnotation(),
                         annotations._NoAnnotation())
        self.assertEqual(hash(annotations._NoAnnotation()),
                         hash(annotations._NoAnnotation()))

    def test_not_equal(self):
        self.assertNotEqual(annotations._NoAnnotation(),
                            annotations.Annotation('bar'))
        self.assertNotEqual(hash(annotations._NoAnnotation()),
                            hash(annotations.Annotation('bar')))
