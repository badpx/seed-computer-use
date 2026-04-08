import importlib
import sys
import unittest


class PublicApiTests(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop('computer_use', None)

    def test_top_level_module_no_longer_exports_action_executor(self):
        module = importlib.import_module('computer_use')

        with self.assertRaises(AttributeError):
            getattr(module, 'ActionExecutor')

        with self.assertRaises(AttributeError):
            getattr(module, 'execute_action')

