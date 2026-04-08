# Android ADB Device Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a built-in `android_adb` device plugin that captures Android screenshots through `adb`, executes the phone action set through `adb shell input`, and switches the agent to the phone-specific prompt profile.

**Architecture:** Extend the shared device interface with a prompt-profile method so prompt selection stays in the core while device-specific command execution stays in plugins. Reuse the existing shared command mapping and coordinate normalization pipeline, then add a new `android_adb` plugin that translates normalized phone commands into `adb` subprocess calls and extracts PNG data from `screencap` output even when warning text appears before the binary payload.

**Tech Stack:** Python 3, `unittest`, existing device plugin registry/factory, `subprocess`, `Pillow` through existing frame helpers.

---

## File Structure

- Create: `computer_use/devices/plugins/android_adb/__init__.py`
  - Package marker for the built-in Android plugin.
- Create: `computer_use/devices/plugins/android_adb/plugin.json`
  - Built-in plugin manifest with `name: "android_adb"`.
- Create: `computer_use/devices/plugins/android_adb/plugin.py`
  - Exposes `create_adapter(config)` for plugin loading.
- Create: `computer_use/devices/plugins/android_adb/adapter.py`
  - Implements screenshot capture, PNG-prefix stripping, adb command execution, and Android action mappings.
- Modify: `computer_use/devices/base.py`
  - Add `get_prompt_profile()` to `DeviceAdapter`.
- Modify: `computer_use/agent.py`
  - Choose system prompt from prompt profile instead of hardcoding the computer prompt.
- Modify: `computer_use/prompts.py`
  - No new prompt body required, but the plan assumes `PHONE_USE_DOUBAO` remains the selected template for `cellphone`.
- Modify: `computer_use/devices/command_mapper.py`
  - Add phone actions: `long_press`, `open_app`, `press_home`, `press_back`.
- Modify: `tests/test_devices.py`
  - Add built-in plugin discovery and prompt-profile tests.
- Create: `tests/test_android_adb_device.py`
  - Unit tests for screenshot parsing and adb command mappings.
- Modify: `tests/test_agent_context.py`
  - Add agent-level prompt selection coverage for `cellphone`.
- Modify: `README.md`
  - Document the new built-in Android plugin, assumptions, and prerequisites.
- Modify: `.env.example`
  - Add `DEVICE_NAME=android_adb` example usage.

### Task 1: Prompt Profile Support In The Shared Device Interface

**Files:**
- Modify: `computer_use/devices/base.py`
- Modify: `computer_use/agent.py`
- Test: `tests/test_agent_context.py`
- Test: `tests/test_devices.py`

- [ ] **Step 1: Write the failing prompt-profile tests**

Add a device double to `tests/test_agent_context.py` that exposes `get_prompt_profile()` and confirm the agent selects the phone prompt for `cellphone`.

```python
class PromptProfileDevice:
    device_name = 'prompt-profile-device'

    def connect(self):
        return None

    def close(self):
        return None

    def capture_frame(self):
        return DeviceFrame(
            image_data_url=f'data:image/png;base64,{PNG_1X1_BASE64}',
            width=1,
            height=1,
            metadata={},
        )

    def execute_command(self, command):
        return 'DONE'

    def get_status(self):
        return {'device_name': self.device_name}

    def get_environment_info(self):
        return {'operating_system': 'Android'}

    def get_prompt_profile(self):
        return 'cellphone'


def test_build_system_prompt_uses_phone_prompt_for_cellphone_profile(self):
    agent = ComputerUseAgent(
        device_adapter=PromptProfileDevice(),
        api_key='test-key',
        model='test-model',
        base_url='http://example.invalid',
        verbose=False,
        print_init_status=False,
    )
    prompt = agent._build_system_prompt()
    self.assertIn("press_home()", prompt)
    self.assertIn("open_app(app_name='')", prompt)
    self.assertNotIn("hotkey(key='ctrl c')", prompt)
```

Add a small test in `tests/test_devices.py` for the new default method:

```python
class DummyDevice(DeviceAdapter):
    def connect(self): return None
    def close(self): return None
    def capture_frame(self): raise NotImplementedError
    def execute_command(self, command): raise NotImplementedError
    def get_status(self): return {}


def test_device_adapter_default_prompt_profile_is_computer(self):
    self.assertEqual(DummyDevice().get_prompt_profile(), 'computer')
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
python -m unittest \
  tests.test_agent_context.ComputerUseAgentContextTests.test_build_system_prompt_uses_phone_prompt_for_cellphone_profile \
  tests.test_devices.DeviceRegistryTests.test_device_adapter_default_prompt_profile_is_computer -v
```

Expected:

- one failure because `DeviceAdapter` does not define `get_prompt_profile()`
- one failure because the agent still always uses `COMPUTER_USE_DOUBAO`

- [ ] **Step 3: Add `get_prompt_profile()` and switch the agent to profile-based prompt selection**

Update `computer_use/devices/base.py`:

```python
class DeviceAdapter(ABC):
    ...
    def get_prompt_profile(self) -> str:
        return 'computer'
```

Update `computer_use/agent.py` to select the template by profile:

```python
from .prompts import COMPUTER_USE_DOUBAO, PHONE_USE_DOUBAO, SKILLS_PROMPT_ADDENDUM

PROMPT_PROFILES = {
    'computer': COMPUTER_USE_DOUBAO,
    'cellphone': PHONE_USE_DOUBAO,
}

def _get_prompt_profile(self) -> str:
    profile = str(getattr(self.device, 'get_prompt_profile', lambda: 'computer')() or 'computer')
    return profile if profile in PROMPT_PROFILES else 'computer'

def _build_system_prompt(self) -> str:
    prompt_template = PROMPT_PROFILES[self._get_prompt_profile()]
    prompt = prompt_template.format(
        instruction='',
        language=self.language,
    )
    prompt += self._build_runtime_context_prompt()
    if self.skills:
        prompt += SKILLS_PROMPT_ADDENDUM
    return prompt
```

Do not change screenshot or history assembly in this task.

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run:

```bash
python -m unittest \
  tests.test_agent_context.ComputerUseAgentContextTests.test_build_system_prompt_uses_phone_prompt_for_cellphone_profile \
  tests.test_devices.DeviceRegistryTests.test_device_adapter_default_prompt_profile_is_computer -v
```

Expected:

- both tests PASS

- [ ] **Step 5: Commit**

```bash
git add computer_use/devices/base.py computer_use/agent.py tests/test_agent_context.py tests/test_devices.py
git commit -m "Add device prompt profile support"
```

### Task 2: Extend Shared Command Mapping For Phone Actions

**Files:**
- Modify: `computer_use/devices/command_mapper.py`
- Test: `tests/test_devices.py`

- [ ] **Step 1: Write the failing command-mapping tests**

Add tests to `tests/test_devices.py` for the four new phone actions:

```python
def test_map_action_to_command_maps_long_press(self):
    command = map_action_to_command(
        {'action_type': 'long_press', 'action_inputs': {'point': [100, 200]}}
    )
    self.assertEqual(command.command_type, 'long_press')
    self.assertEqual(command.payload['point'], [100, 200])


def test_map_action_to_command_maps_open_app(self):
    command = map_action_to_command(
        {'action_type': 'open_app', 'action_inputs': {'app_name': 'com.demo.app'}}
    )
    self.assertEqual(command.command_type, 'open_app')
    self.assertEqual(command.payload['app_name'], 'com.demo.app')


def test_map_action_to_command_maps_press_home_and_back(self):
    home = map_action_to_command({'action_type': 'press_home', 'action_inputs': {}})
    back = map_action_to_command({'action_type': 'press_back', 'action_inputs': {}})
    self.assertEqual(home.command_type, 'press_home')
    self.assertEqual(back.command_type, 'press_back')
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
python -m unittest tests.test_devices.DeviceHelpersTests tests.test_devices.DeviceRegistryTests -v
```

Expected:

- the new mapping assertions FAIL because `map_action_to_command()` does not yet map these actions

- [ ] **Step 3: Add the new action mappings**

Update `computer_use/devices/command_mapper.py`:

```python
command_type = {
    'click': 'click',
    'left_single': 'click',
    'left_double': 'double_click',
    'right_single': 'right_click',
    'hover': 'move',
    'drag': 'drag',
    'long_press': 'long_press',
    'open_app': 'open_app',
    'press_home': 'press_home',
    'press_back': 'press_back',
    'hotkey': 'hotkey',
    'press': 'key_down',
    'keydown': 'key_down',
    'release': 'key_up',
    'keyup': 'key_up',
    'type': 'type_text',
    'scroll': 'scroll',
    'wait': 'wait',
}.get(action_type, action_type)
```

Do not introduce Android-specific subprocess logic here; keep this task limited to semantic command translation.

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run:

```bash
python -m unittest tests.test_devices -v
```

Expected:

- all updated device-layer tests PASS

- [ ] **Step 5: Commit**

```bash
git add computer_use/devices/command_mapper.py tests/test_devices.py
git commit -m "Map phone actions into shared device commands"
```

### Task 3: Add The Built-In `android_adb` Device Plugin

**Files:**
- Create: `computer_use/devices/plugins/android_adb/__init__.py`
- Create: `computer_use/devices/plugins/android_adb/plugin.json`
- Create: `computer_use/devices/plugins/android_adb/plugin.py`
- Create: `computer_use/devices/plugins/android_adb/adapter.py`
- Test: `tests/test_android_adb_device.py`

- [ ] **Step 1: Write the failing plugin and adapter tests**

Create `tests/test_android_adb_device.py` with a fake `subprocess.run` side effect and a tiny PNG payload.

```python
import subprocess
import unittest
from unittest import mock

from computer_use.devices.base import DeviceCommand
from computer_use.devices.factory import create_device_adapter

PNG_BYTES = (
    b'\\x89PNG\\r\\n\\x1a\\n'
    b'\\x00\\x00\\x00\\rIHDR'
    b'\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x01'
    b'\\x08\\x06\\x00\\x00\\x00\\x1f\\x15\\xc4\\x89'
    b'\\x00\\x00\\x00\\x0aIDATx\\x9cc\\xf8\\x0f\\x00\\x01\\x01\\x01\\x00\\x18\\xdd\\x8d\\xb1'
    b'\\x00\\x00\\x00\\x00IEND\\xaeB`\\x82'
)


class AndroidAdbDeviceTests(unittest.TestCase):
    @mock.patch('computer_use.devices.plugins.android_adb.adapter.subprocess.run')
    def test_capture_frame_reads_png_after_warning_prefix(self, run_mock):
        warning = (
            b'[Warning] Multiple displays were found\\n'
            b'A display ID can be specified with the [-d display-id] option.\\n'
        )
        run_mock.return_value = subprocess.CompletedProcess(
            args=['adb', 'exec-out', 'screencap', '-p'],
            returncode=0,
            stdout=warning + PNG_BYTES,
            stderr=b'',
        )

        adapter = create_device_adapter(device_name='android_adb')
        frame = adapter.capture_frame()

        self.assertEqual((frame.width, frame.height), (1, 1))
        self.assertTrue(frame.image_data_url.startswith('data:image/png;base64,'))
        self.assertTrue(frame.metadata['png_prefix_stripped'])

    @mock.patch('computer_use.devices.plugins.android_adb.adapter.subprocess.run')
    def test_execute_command_maps_click_to_adb_tap(self, run_mock):
        run_mock.return_value = subprocess.CompletedProcess(
            args=['adb', 'shell', 'input', 'tap', '10', '20'],
            returncode=0,
            stdout=b'',
            stderr=b'',
        )

        adapter = create_device_adapter(device_name='android_adb')
        result = adapter.execute_command(
            DeviceCommand(command_type='click', payload={'point': [10, 20]})
        )

        self.assertIn('tap', result.lower())
        run_mock.assert_called_with(
            ['adb', 'shell', 'input', 'tap', '10', '20'],
            capture_output=True,
            check=False,
        )
```

Also add tests for:

- `get_prompt_profile() == 'cellphone'`
- `get_environment_info()['operating_system'] == 'Android'`
- built-in discovery includes `android_adb`

- [ ] **Step 2: Run the new Android tests to verify they fail**

Run:

```bash
python -m unittest tests.test_android_adb_device -v
```

Expected:

- import failure because the plugin files do not exist yet

- [ ] **Step 3: Add the built-in plugin files and the minimal adapter**

Create `computer_use/devices/plugins/android_adb/plugin.json`:

```json
{
  "name": "android_adb",
  "description": "Control an Android phone over adb",
  "entrypoint": "plugin:create_adapter"
}
```

Create `computer_use/devices/plugins/android_adb/plugin.py`:

```python
from .adapter import AndroidAdbDeviceAdapter


def create_adapter(config):
    return AndroidAdbDeviceAdapter(config or {})
```

Create `computer_use/devices/plugins/android_adb/adapter.py` with the minimal adapter skeleton:

```python
import base64
import io
import subprocess
from typing import Any, Dict

from ...base import DeviceAdapter, DeviceCommand, DeviceFrame


class AndroidAdbDeviceAdapter(DeviceAdapter):
    def __init__(self, plugin_config: Dict[str, Any]):
        self.plugin_config = dict(plugin_config or {})
        self.verbose = bool(self.plugin_config.get('verbose', True))

    @property
    def device_name(self) -> str:
        return 'android_adb'

    def connect(self) -> None:
        return None

    def close(self) -> None:
        return None

    def get_prompt_profile(self) -> str:
        return 'cellphone'

    def get_environment_info(self) -> Dict[str, Any]:
        return {'operating_system': 'Android'}

    def get_status(self) -> Dict[str, Any]:
        return {'device_name': self.device_name, 'connected_via': 'adb'}
```

Do not implement all commands yet; this step is only to make the plugin load and establish its identity.

- [ ] **Step 4: Run the Android tests again to verify the remaining failures are inside adapter behavior**

Run:

```bash
python -m unittest tests.test_android_adb_device -v
```

Expected:

- plugin discovery tests PASS
- screenshot and command execution tests still FAIL because `capture_frame()` and `execute_command()` are not implemented

- [ ] **Step 5: Implement screenshot capture, PNG-prefix stripping, and command execution**

Extend `computer_use/devices/plugins/android_adb/adapter.py` with:

```python
PNG_SIGNATURE = b'\\x89PNG\\r\\n\\x1a\\n'
LONG_PRESS_DURATION_MS = 600
DRAG_DURATION_MS = 400

def capture_frame(self) -> DeviceFrame:
    result = self._run_adb(['exec-out', 'screencap', '-p'])
    png_bytes, prefix_stripped = self._extract_png_payload(result.stdout)
    width, height = self._read_png_size(png_bytes)
    image_base64 = base64.b64encode(png_bytes).decode('utf-8')
    return DeviceFrame(
        image_data_url=f'data:image/png;base64,{image_base64}',
        width=width,
        height=height,
        metadata={
            'device_name': self.device_name,
            'capture_method': 'adb_exec_out_screencap',
            'png_prefix_stripped': prefix_stripped,
        },
    )

def execute_command(self, command: DeviceCommand):
    handlers = {
        'click': self._execute_click,
        'long_press': self._execute_long_press,
        'drag': self._execute_drag,
        'type_text': self._execute_type_text,
        'scroll': self._execute_scroll,
        'open_app': self._execute_open_app,
        'press_home': self._execute_press_home,
        'press_back': self._execute_press_back,
    }
    handler = handlers.get(command.command_type)
    if handler is None:
        raise ValueError(f'android_adb 不支持动作: {command.command_type}')
    return handler(command.payload)

def _run_adb(self, adb_args):
    try:
        result = subprocess.run(
            ['adb', *adb_args],
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError('未找到 adb，请确认 adb 已安装并在 PATH 中') from exc
    if result.returncode != 0:
        stderr_text = result.stderr.decode('utf-8', errors='replace').strip()
        raise RuntimeError(f'adb 命令执行失败: {stderr_text or result.returncode}')
    return result
```

Implement `_extract_png_payload()` so it searches for `PNG_SIGNATURE` inside stdout and strips any warning prefix:

```python
def _extract_png_payload(self, stdout: bytes) -> tuple[bytes, bool]:
    index = stdout.find(PNG_SIGNATURE)
    if index < 0:
        preview = stdout[:200].decode('utf-8', errors='replace').strip()
        raise RuntimeError(f'Android 截图输出中未找到 PNG 数据: {preview}')
    return stdout[index:], index > 0
```

Implement the command mappings:

```python
def _execute_click(self, payload):
    x, y = self._require_point(payload.get('point'))
    self._run_adb(['shell', 'input', 'tap', str(x), str(y)])
    return f'tap ({x}, {y})'

def _execute_long_press(self, payload):
    x, y = self._require_point(payload.get('point'))
    self._run_adb(['shell', 'input', 'swipe', str(x), str(y), str(x), str(y), str(LONG_PRESS_DURATION_MS)])
    return f'long_press ({x}, {y})'

def _execute_drag(self, payload):
    x1, y1 = self._require_point(payload.get('start_point'))
    x2, y2 = self._require_point(payload.get('end_point'))
    self._run_adb(['shell', 'input', 'draganddrop', str(x1), str(y1), str(x2), str(y2), str(DRAG_DURATION_MS)])
    return f'drag ({x1}, {y1}) -> ({x2}, {y2})'
```

Implement `_execute_type_text()` so trailing newline becomes a second `KEYCODE_ENTER` call and use a small explicit text escape helper:

```python
def _execute_type_text(self, payload):
    content = str(payload.get('content') or '')
    submit = content.endswith('\\n')
    if submit:
        content = content[:-1]
    escaped = self._escape_text(content)
    if escaped:
        self._run_adb(['shell', 'input', 'text', escaped])
    if submit:
        self._run_adb(['shell', 'input', 'keyevent', 'KEYCODE_ENTER'])
    return 'type'
```

Implement `_execute_open_app()`, `_execute_press_home()`, `_execute_press_back()`, and `_execute_scroll()` with direct `adb shell input` commands.

- [ ] **Step 6: Run the Android plugin tests to verify they pass**

Run:

```bash
python -m unittest tests.test_android_adb_device -v
```

Expected:

- all Android plugin tests PASS

- [ ] **Step 7: Commit**

```bash
git add \
  computer_use/devices/plugins/android_adb/__init__.py \
  computer_use/devices/plugins/android_adb/plugin.json \
  computer_use/devices/plugins/android_adb/plugin.py \
  computer_use/devices/plugins/android_adb/adapter.py \
  tests/test_android_adb_device.py
git commit -m "Add android adb device plugin"
```

### Task 4: Finish Android Action Coverage, Documentation, And Full Regression

**Files:**
- Modify: `tests/test_android_adb_device.py`
- Modify: `tests/test_devices.py`
- Modify: `README.md`
- Modify: `.env.example`

- [ ] **Step 1: Add the remaining failing regression tests**

Expand `tests/test_android_adb_device.py` to cover:

```python
@mock.patch('computer_use.devices.plugins.android_adb.adapter.subprocess.run')
def test_execute_command_maps_type_with_submit_to_text_then_enter(self, run_mock):
    run_mock.return_value = subprocess.CompletedProcess(args=['adb'], returncode=0, stdout=b'', stderr=b'')
    adapter = create_device_adapter(device_name='android_adb')

    adapter.execute_command(DeviceCommand(command_type='type_text', payload={'content': 'hello\\n'}))

    self.assertEqual(run_mock.call_args_list[0].args[0], ['adb', 'shell', 'input', 'text', 'hello'])
    self.assertEqual(run_mock.call_args_list[1].args[0], ['adb', 'shell', 'input', 'keyevent', 'KEYCODE_ENTER'])

@mock.patch('computer_use.devices.plugins.android_adb.adapter.subprocess.run')
def test_execute_command_maps_press_home_and_back(self, run_mock):
    run_mock.return_value = subprocess.CompletedProcess(args=['adb'], returncode=0, stdout=b'', stderr=b'')
    adapter = create_device_adapter(device_name='android_adb')

    adapter.execute_command(DeviceCommand(command_type='press_home', payload={}))
    adapter.execute_command(DeviceCommand(command_type='press_back', payload={}))

    self.assertEqual(run_mock.call_args_list[0].args[0], ['adb', 'shell', 'input', 'keyevent', 'KEYCODE_HOME'])
    self.assertEqual(run_mock.call_args_list[1].args[0], ['adb', 'shell', 'input', 'keyevent', 'KEYCODE_BACK'])

@mock.patch('computer_use.devices.plugins.android_adb.adapter.subprocess.run')
def test_execute_command_maps_open_app_to_monkey(self, run_mock):
    run_mock.return_value = subprocess.CompletedProcess(args=['adb'], returncode=0, stdout=b'', stderr=b'')
    adapter = create_device_adapter(device_name='android_adb')

    adapter.execute_command(DeviceCommand(command_type='open_app', payload={'app_name': 'com.demo.app'}))

    self.assertEqual(
        run_mock.call_args.args[0],
        ['adb', 'shell', 'monkey', '-p', 'com.demo.app', '-c', 'android.intent.category.LAUNCHER', '1'],
    )
```

Add negative tests for:

- unsupported action
- missing `adb`
- non-zero exit code with stderr
- stdout without a PNG signature

- [ ] **Step 2: Run the Android regression tests to verify they fail before the finishing changes**

Run:

```bash
python -m unittest tests.test_android_adb_device -v
```

Expected:

- one or more failures in text escaping, scroll mapping, or error handling that still need implementation polish

- [ ] **Step 3: Finish the remaining adapter behavior and update docs**

Complete the Android adapter so the remaining tests pass:

```python
def _execute_open_app(self, payload):
    package_name = str(payload.get('app_name') or '').strip()
    if not package_name:
        raise ValueError('open_app 需要 app_name')
    self._run_adb(['shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'])
    return f'open_app {package_name}'

def _execute_press_home(self, payload):
    self._run_adb(['shell', 'input', 'keyevent', 'KEYCODE_HOME'])
    return 'press_home'

def _execute_press_back(self, payload):
    self._run_adb(['shell', 'input', 'keyevent', 'KEYCODE_BACK'])
    return 'press_back'
```

Implement a minimal scroll converter:

```python
def _execute_scroll(self, payload):
    x, y = self._require_point(payload.get('point'))
    direction = str(payload.get('direction') or '').strip().lower()
    steps = max(1, min(50, int(payload.get('steps', 1))))
    axis_name, axis_value = self._scroll_axis(direction, steps)
    self._run_adb([
        'shell', 'input', 'touchscreen', 'scroll',
        str(x), str(y),
        '--axis', f'{axis_name},{axis_value}',
    ])
    return f'scroll {direction} at ({x}, {y})'
```

Update `README.md` with a small Android section:

```md
### Android ADB Device

Use `DEVICE_NAME=android_adb` when `adb` is installed, the target phone is already connected, and you want the agent to operate a phone instead of a desktop device. The built-in Android plugin captures screenshots through `adb exec-out screencap -p` and sends touch/key events through `adb shell input`.
```

Update `.env.example`:

```bash
DEVICE_NAME=android_adb
```

- [ ] **Step 4: Run the targeted tests and then the full regression suite**

Run:

```bash
python -m unittest tests.test_android_adb_device tests.test_agent_context tests.test_devices -v
python -m unittest discover -s tests -v
python -m compileall computer_use tests check_env.py
```

Expected:

- targeted Android/device/agent tests PASS
- full `unittest discover` PASS
- `compileall` PASS

- [ ] **Step 5: Commit**

```bash
git add \
  tests/test_android_adb_device.py \
  tests/test_devices.py \
  tests/test_agent_context.py \
  README.md \
  .env.example
git commit -m "Document and verify android adb device support"
```

## Self-Review

- Spec coverage check:
  - built-in plugin: Task 3
  - prompt profile `cellphone`: Task 1
  - phone action mapping additions: Task 2
  - screenshot warning-prefix stripping: Task 3
  - `adb shell input` mappings: Tasks 3 and 4
  - Android docs and config examples: Task 4
- Placeholder scan:
  - no `TODO`, `TBD`, or implicit “handle errors later” steps remain
- Type consistency:
  - prompt profile name is consistently `cellphone`
  - plugin name is consistently `android_adb`
  - command types are consistently `long_press`, `open_app`, `press_home`, `press_back`, `type_text`
