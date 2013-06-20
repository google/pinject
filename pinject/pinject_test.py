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

import pinject


class CopiedClassesTest(unittest.TestCase):

    def test_new_object_graph_works(self):
        class SomeClass(object):
                pass
        obj_graph = pinject.new_object_graph(classes=[SomeClass])
        self.assertIsInstance(obj_graph.provide(SomeClass), SomeClass)
