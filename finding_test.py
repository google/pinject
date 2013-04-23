
import sys
import unittest

import finding


class FindClassesTest(unittest.TestCase):

    def test_finds_passed_in_classes(self):
        class SomeClass(object):
            pass
        self.assertIn(SomeClass,
                      finding.find_classes(modules=None, classes=[SomeClass]))

    def test_finds_classes_in_passed_in_modules(self):
        this_module = sys.modules[FindClassesTest.__module__]
        self.assertIn(FindClassesTest,
                      finding.find_classes(modules=[this_module], classes=None))

    def test_returns_class_once_even_if_passed_in_multiple_times(self):
        this_module = sys.modules[FindClassesTest.__module__]
        self.assertIn(
            FindClassesTest,
            finding.find_classes(modules=[this_module, this_module],
                                 classes=[FindClassesTest, FindClassesTest]))

    def test_reads_sys_modules_for_all_imported_modules(self):
        self.assertIn(
            FindClassesTest,
            finding.find_classes(modules=finding.ALL_IMPORTED_MODULES,
                                 classes=None))


def a_fn_to_find():
    pass


class FindFunctionsTest(unittest.TestCase):

    def test_finds_functions_in_passed_in_modules(self):
        this_module = sys.modules[FindFunctionsTest.__module__]
        self.assertIn(a_fn_to_find, finding.find_functions([this_module]))

    def test_returns_fn_once_even_if_passed_in_multiple_times(self):
        this_module = sys.modules[FindFunctionsTest.__module__]
        self.assertIn(a_fn_to_find,
                      finding.find_functions([this_module, this_module]))

    def test_reads_sys_modules_for_all_imported_modules(self):
        self.assertIn(a_fn_to_find,
                      finding.find_functions(finding.ALL_IMPORTED_MODULES))
