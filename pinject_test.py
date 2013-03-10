#!/usr/bin/python

import unittest

import pinject


class CopiedClassesTest(unittest.TestCase):

    def test_new_injector_works(self):
        class SomeClass(object):
                pass
        injector = pinject.NewInjector(classes=[SomeClass])
        self.assertTrue(isinstance(injector.provide(SomeClass), SomeClass))
