import importlib.util
import unittest
from pathlib import Path


_PLUGIN_TEST_PATH = (
    Path(__file__).resolve().parents[1]
    / 'computer_use'
    / 'devices'
    / 'plugins'
    / 'lumi_cua_sandbox'
    / 'tests'
    / 'test_lumi_cua_sandbox_device.py'
)


class _MissingLumiCuaSandboxPluginTests(unittest.TestCase):
    @unittest.skip('lumi_cua_sandbox plugin tests are unavailable in this workspace')
    def test_lumi_cua_sandbox_plugin_tests_unavailable(self):
        pass


def _load_plugin_test_module():
    spec = importlib.util.spec_from_file_location(
        'lumi_cua_sandbox_plugin_tests',
        _PLUGIN_TEST_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f'无法加载 lumi_cua_sandbox 插件测试: {_PLUGIN_TEST_PATH}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_tests(loader, standard_tests, pattern):
    if not _PLUGIN_TEST_PATH.exists():
        return loader.loadTestsFromTestCase(_MissingLumiCuaSandboxPluginTests)
    return loader.loadTestsFromModule(_load_plugin_test_module())
