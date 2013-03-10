
import sys
import unittest

import finding


class FindClassesTest(unittest.TestCase):

    def test_finds_passed_in_classes(self):
        class SomeClass(object):
            pass
        self.assertIn(SomeClass, finding.FindClasses(classes=[SomeClass]))

    def test_finds_classes_in_passed_in_modules(self):
        this_module = sys.modules[FindClassesTest.__module__]
        self.assertIn(FindClassesTest,
                      finding.FindClasses(modules=[this_module]))

    def test_returns_class_once_even_if_passed_in_multiple_times(self):
        this_module = sys.modules[FindClassesTest.__module__]
        self.assertIn(
            FindClassesTest,
            finding.FindClasses(modules=[this_module, this_module],
                                classes=[FindClassesTest, FindClassesTest]))

    def test_reads_sys_modules_if_no_classes_or_modules_specified(self):
        self.assertIn(FindClassesTest, finding.FindClasses())
