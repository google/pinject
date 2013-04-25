#!/usr/bin/python

import unittest

import pinject


class CopiedClassesTest(unittest.TestCase):

    def test_new_object_graph_works(self):
        class SomeClass(object):
                pass
        injector = pinject.new_object_graph(classes=[SomeClass])
        self.assertIsInstance(injector.provide(SomeClass), SomeClass)
