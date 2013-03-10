#!/usr/bin/python

import pinject

class Bar(object):

    def __init__(self):
        pass

    def PrintSomething(self):
        print 'Hello, world!'


class Foo(object):

    def __init__(self, bar):
        self._bar = bar

    def CallBar(self):
        self._bar.PrintSomething()


injector = pinject.NewInjector()
foo = injector.provide(Foo)
foo.CallBar()
