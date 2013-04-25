#!/usr/bin/python

import unittest

import pinject


class CopiedClassesTest(unittest.TestCase):

    def test_new_object_graph_works(self):
        class SomeClass(object):
                pass
        obj_graph = pinject.new_object_graph(classes=[SomeClass])
        self.assertIsInstance(obj_graph.provide(SomeClass), SomeClass)
