import importlib
import sys
import types
import unittest


class FakePyAutoGUI(types.ModuleType):
    def __init__(self):
        super().__init__('pyautogui')
        self.FAILSAFE = False
        self.PAUSE = 0
        self.click_calls = []

    def click(self, *args, **kwargs):
        self.click_calls.append((args, kwargs))

    def moveTo(self, *args, **kwargs):
        pass

    def dragTo(self, *args, **kwargs):
        pass

    def hotkey(self, *keys):
        pass

    def keyDown(self, *args, **kwargs):
        pass

    def keyUp(self, *args, **kwargs):
        pass

    def write(self, *args, **kwargs):
        pass

    def press(self, *args, **kwargs):
        pass

    def scroll(self, *args, **kwargs):
        pass


class LocalExecutorTests(unittest.TestCase):
    def setUp(self):
        sys.modules['pyautogui'] = FakePyAutoGUI()
        sys.modules.pop('computer_use.devices.plugins.local.executor', None)

    def tearDown(self):
        sys.modules.pop('pyautogui', None)
        sys.modules.pop('computer_use.devices.plugins.local.executor', None)

    def test_local_executor_supports_pixel_click_with_display_offset(self):
        module = importlib.import_module('computer_use.devices.plugins.local.executor')
        executor = module.LocalActionExecutor(
            verbose=False,
            display_offset_x=-1440,
            display_offset_y=90,
        )

        result = executor.execute(
            {
                'action_type': 'click',
                'action_inputs': {'point': [25, 50]},
            }
        )

        self.assertEqual(
            sys.modules['pyautogui'].click_calls,
            [((-1415, 140), {'button': 'left', 'clicks': 1})],
        )
        self.assertEqual(result, '单击 (-1415, 140)')

