
import sys
import unittest

import finding


class FindClassesTest(unittest.TestCase):

    def test_finds_passed_in_classes(self):
        class SomeClass(object):
            pass
        self.assertIn(SomeClass, finding.find_classes(classes=[SomeClass]))

    def test_finds_classes_in_passed_in_modules(self):
        this_module = sys.modules[FindClassesTest.__module__]
        self.assertIn(FindClassesTest,
                      finding.find_classes(modules=[this_module]))

    def test_returns_class_once_even_if_passed_in_multiple_times(self):
        this_module = sys.modules[FindClassesTest.__module__]
        self.assertIn(
            FindClassesTest,
            finding.find_classes(modules=[this_module, this_module],
                                 classes=[FindClassesTest, FindClassesTest]))

    def test_reads_sys_modules_if_nothing_specified(self):
        self.assertIn(FindClassesTest, finding.find_classes())


def a_fn_to_find():
    pass


class FindFunctionsTest(unittest.TestCase):

    def test_finds_passed_in_provider_fns(self):
        def a_provider_fn():
            pass
        self.assertIn(a_provider_fn,
                      finding.find_functions(provider_fns=[a_provider_fn]))

    def test_finds_functions_in_passed_in_modules(self):
        this_module = sys.modules[FindFunctionsTest.__module__]
        self.assertIn(a_fn_to_find,
                      finding.find_functions(modules=[this_module]))

    def test_returns_fn_once_even_if_passed_in_multiple_times(self):
        this_module = sys.modules[FindFunctionsTest.__module__]
        self.assertIn(
            a_fn_to_find,
            finding.find_functions(modules=[this_module, this_module],
                                   provider_fns=[a_fn_to_find, a_fn_to_find]))

    def test_reads_sys_modules_if_nothing_specified(self):
        self.assertIn(a_fn_to_find, finding.find_functions())
