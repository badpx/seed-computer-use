# Global Natural Scroll Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `NATURAL_SCROLL` affect `scroll` actions consistently across devices by flipping scroll direction once in the shared command-normalization pipeline.

**Architecture:** Add a shared scroll-direction normalization helper in the device layer, invoke it from `ComputerUseAgent` after coordinate normalization, and remove the now-duplicated natural-scroll inversion from the local executor. Keep the change strictly scoped to `scroll` so `swipe`, `drag`, and other actions remain unchanged.

**Tech Stack:** Python 3, `unittest`, existing device command pipeline in `computer_use.devices`

---

## File Structure

- Modify: `computer_use/devices/coordinates.py`
  - Add a shared helper that flips `scroll.direction` for `NATURAL_SCROLL`
- Modify: `computer_use/agent.py`
  - Invoke the new shared helper in the existing device-command build path
- Modify: `computer_use/devices/plugins/local/executor.py`
  - Remove local-only natural-scroll inversion so local execution consumes already-normalized direction
- Modify: `tests/test_devices.py`
  - Add unit coverage for shared scroll-direction normalization
- Modify: `tests/test_action_executor.py`
  - Update local executor expectations so it no longer inverts direction internally
- Modify: `tests/test_android_adb_device.py`
  - Add an Android regression asserting flipped direction reaches the plugin when `natural_scroll=True`

### Task 1: Add Shared Scroll-Direction Normalization

**Files:**
- Modify: `tests/test_devices.py`
- Modify: `computer_use/devices/coordinates.py`

- [ ] **Step 1: Write the failing shared-normalization tests**

Add these tests to `tests/test_devices.py` near the existing helper/coordinate tests:

```python
class ScrollNormalizationTests(unittest.TestCase):
    def test_normalize_scroll_direction_flips_vertical_direction_when_natural_scroll_enabled(self):
        from computer_use.devices.base import DeviceCommand
        from computer_use.devices.coordinates import normalize_scroll_direction

        command = DeviceCommand('scroll', {'direction': 'down', 'steps': 50})

        normalized = normalize_scroll_direction(command, natural_scroll=True)

        self.assertEqual(normalized.payload['direction'], 'up')
        self.assertEqual(normalized.payload['steps'], 50)

    def test_normalize_scroll_direction_flips_horizontal_direction_when_natural_scroll_enabled(self):
        from computer_use.devices.base import DeviceCommand
        from computer_use.devices.coordinates import normalize_scroll_direction

        command = DeviceCommand('scroll', {'direction': 'left', 'steps': 30})

        normalized = normalize_scroll_direction(command, natural_scroll=True)

        self.assertEqual(normalized.payload['direction'], 'right')

    def test_normalize_scroll_direction_leaves_non_scroll_commands_unchanged(self):
        from computer_use.devices.base import DeviceCommand
        from computer_use.devices.coordinates import normalize_scroll_direction

        command = DeviceCommand('swipe', {'direction': 'down', 'steps': 50})

        normalized = normalize_scroll_direction(command, natural_scroll=True)

        self.assertEqual(normalized.command_type, 'swipe')
        self.assertEqual(normalized.payload['direction'], 'down')

    def test_normalize_scroll_direction_leaves_scroll_direction_unchanged_when_disabled(self):
        from computer_use.devices.base import DeviceCommand
        from computer_use.devices.coordinates import normalize_scroll_direction

        command = DeviceCommand('scroll', {'direction': 'up', 'steps': 12})

        normalized = normalize_scroll_direction(command, natural_scroll=False)

        self.assertEqual(normalized.payload['direction'], 'up')
```

- [ ] **Step 2: Run the new tests to confirm the helper does not exist yet**

Run:

```bash
python -m unittest \
  tests.test_devices.ScrollNormalizationTests.test_normalize_scroll_direction_flips_vertical_direction_when_natural_scroll_enabled \
  tests.test_devices.ScrollNormalizationTests.test_normalize_scroll_direction_flips_horizontal_direction_when_natural_scroll_enabled \
  tests.test_devices.ScrollNormalizationTests.test_normalize_scroll_direction_leaves_non_scroll_commands_unchanged \
  tests.test_devices.ScrollNormalizationTests.test_normalize_scroll_direction_leaves_scroll_direction_unchanged_when_disabled \
  -v
```

Expected: `ImportError` or `AttributeError` because `normalize_scroll_direction` does not exist yet.

- [ ] **Step 3: Implement the minimal shared helper**

Add this helper to `computer_use/devices/coordinates.py` below `normalize_command_coordinates()`:

```python
def normalize_scroll_direction(
    command: DeviceCommand,
    *,
    natural_scroll: bool,
) -> DeviceCommand:
    if command.command_type != 'scroll' or not natural_scroll:
        return command

    payload = dict(command.payload or {})
    direction = str(payload.get('direction', '')).strip().lower()
    opposite = {
        'up': 'down',
        'down': 'up',
        'left': 'right',
        'right': 'left',
    }
    if direction in opposite:
        payload['direction'] = opposite[direction]

    return DeviceCommand(
        command_type=command.command_type,
        payload=payload,
        metadata=dict(command.metadata or {}),
    )
```

Do not change coordinate logic in this task.

- [ ] **Step 4: Run the shared-normalization tests to verify they pass**

Run:

```bash
python -m unittest \
  tests.test_devices.ScrollNormalizationTests.test_normalize_scroll_direction_flips_vertical_direction_when_natural_scroll_enabled \
  tests.test_devices.ScrollNormalizationTests.test_normalize_scroll_direction_flips_horizontal_direction_when_natural_scroll_enabled \
  tests.test_devices.ScrollNormalizationTests.test_normalize_scroll_direction_leaves_non_scroll_commands_unchanged \
  tests.test_devices.ScrollNormalizationTests.test_normalize_scroll_direction_leaves_scroll_direction_unchanged_when_disabled \
  -v
```

Expected: all four tests pass.

- [ ] **Step 5: Commit the helper and tests**

```bash
git add tests/test_devices.py computer_use/devices/coordinates.py
git commit -m "添加全局滚动方向归一化"
```

### Task 2: Integrate Shared Scroll Normalization Into Agent Dispatch

**Files:**
- Modify: `tests/test_android_adb_device.py`
- Modify: `computer_use/agent.py`

- [ ] **Step 1: Write the failing Android integration regression**

Add this test to `tests/test_android_adb_device.py`:

```python
    def test_agent_flips_scroll_direction_for_android_when_natural_scroll_enabled(self):
        from computer_use.devices.base import DeviceCommand, DeviceFrame
        from computer_use.agent import ComputerUseAgent

        class FakeAndroidDevice:
            def __init__(self):
                self.commands = []

            @property
            def device_name(self):
                return 'android_adb'

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

            def execute_command(self, command: DeviceCommand):
                self.commands.append(command)
                return 'scroll 执行成功'

            def get_status(self):
                return {}

            def get_prompt_profile(self):
                return 'cellphone'

            def get_environment_info(self):
                return {'operating_system': 'Android'}

        fake_device = FakeAndroidDevice()
        agent = ComputerUseAgent(
            instruction='测试',
            device_adapter=fake_device,
            natural_scroll=True,
            max_steps=1,
            verbose=False,
            print_init_status=False,
        )

        action = {'action_type': 'scroll', 'action_inputs': {'direction': 'down', 'steps': 50}}
        command = agent._build_device_command(action, image_width=1000, image_height=1000, model_image_width=1000, model_image_height=1000)

        self.assertEqual(command.payload['direction'], 'up')
```

This test intentionally checks the command before plugin execution so the behavior is clearly global.

- [ ] **Step 2: Run the targeted test to confirm the agent still passes the original direction**

Run:

```bash
python -m unittest \
  tests.test_android_adb_device.AndroidAdbDeviceAdapterTests.test_agent_flips_scroll_direction_for_android_when_natural_scroll_enabled \
  -v
```

Expected: FAIL because the command payload direction is still `down`.

- [ ] **Step 3: Wire the new helper into `ComputerUseAgent`**

In `computer_use/agent.py`, update the imports and the command-build pipeline so `_build_device_command(...)` applies the helper after coordinate normalization:

```python
from computer_use.devices.coordinates import (
    normalize_command_coordinates,
    normalize_scroll_direction,
)
```

and later:

```python
command = normalize_command_coordinates(
    command,
    image_width=image_width,
    image_height=image_height,
    model_image_width=model_image_width,
    model_image_height=model_image_height,
    coordinate_space=self.coordinate_space,
    coordinate_scale=self.coordinate_scale,
)
command = normalize_scroll_direction(
    command,
    natural_scroll=self.natural_scroll,
)
```

Keep this change scoped to the existing command-building path. Do not add device-specific branches.

- [ ] **Step 4: Run the targeted Android integration test to verify it passes**

Run:

```bash
python -m unittest \
  tests.test_android_adb_device.AndroidAdbDeviceAdapterTests.test_agent_flips_scroll_direction_for_android_when_natural_scroll_enabled \
  -v
```

Expected: PASS with the command payload direction equal to `up`.

- [ ] **Step 5: Commit the agent integration**

```bash
git add tests/test_android_adb_device.py computer_use/agent.py
git commit -m "接入全局自然滚动方向归一化"
```

### Task 3: Remove Local Double-Inversion And Preserve End-To-End Behavior

**Files:**
- Modify: `tests/test_action_executor.py`
- Modify: `computer_use/devices/plugins/local/executor.py`

- [ ] **Step 1: Update local executor tests to reflect the new responsibility split**

In `tests/test_action_executor.py`, replace the current natural-scroll-specific assertion with one that proves the local executor now interprets direction literally:

```python
    def test_scroll_interprets_direction_literally_after_global_normalization(self):
        executor = self._make_executor(natural_scroll=True)
        result = executor.execute(
            {'action_type': 'scroll', 'action_inputs': {'direction': 'down', 'steps': 50, 'point': [498, 558]}}
        )
        self.assertEqual(self.fake_pyautogui.move_to_calls, [((498, 558), {})])
        self.assertEqual(self.fake_pyautogui.scroll_calls, [((50,), {})])
        self.assertEqual(result, '滚动down 50步: (498, 558)')
```

Add a new end-to-end regression that proves global normalization plus local execution still yields the old natural-scroll user-facing behavior:

```python
    def test_global_normalization_preserves_local_natural_scroll_behavior(self):
        from computer_use.devices.base import DeviceCommand
        from computer_use.devices.coordinates import normalize_scroll_direction

        executor = self._make_executor(natural_scroll=True)
        command = DeviceCommand('scroll', {'direction': 'down', 'steps': 50, 'point': [498, 558]})
        normalized = normalize_scroll_direction(command, natural_scroll=True)

        result = executor.execute({'action_type': 'scroll', 'action_inputs': normalized.payload})

        self.assertEqual(self.fake_pyautogui.scroll_calls, [((-50,), {})])
        self.assertEqual(result, '滚动up 50步: (498, 558)')
```

- [ ] **Step 2: Run the targeted local tests to confirm the executor still double-inverts**

Run:

```bash
python -m unittest \
  tests.test_action_executor.LocalActionExecutorTests.test_scroll_interprets_direction_literally_after_global_normalization \
  tests.test_action_executor.LocalActionExecutorTests.test_global_normalization_preserves_local_natural_scroll_behavior \
  -v
```

Expected: the first test fails because local execution still flips `down` to a negative amount internally.

- [ ] **Step 3: Remove local-only inversion logic**

In `computer_use/devices/plugins/local/executor.py`, simplify `_execute_scroll()` so it no longer consults `self.natural_scroll`:

```python
        amount = steps if direction == 'down' else -steps
        pyautogui.scroll(amount)
```

Leave the rest of the method unchanged. Do not remove the constructor argument in this task; that can remain for backward compatibility even if it is no longer used for execution.

- [ ] **Step 4: Run focused and full regression suites**

Run:

```bash
python -m unittest \
  tests.test_action_executor.LocalActionExecutorTests.test_scroll_interprets_direction_literally_after_global_normalization \
  tests.test_action_executor.LocalActionExecutorTests.test_global_normalization_preserves_local_natural_scroll_behavior \
  tests.test_devices.ScrollNormalizationTests \
  tests.test_android_adb_device.AndroidAdbDeviceAdapterTests.test_agent_flips_scroll_direction_for_android_when_natural_scroll_enabled \
  -v
python -m unittest discover -s tests -v
python -m compileall computer_use tests check_env.py
```

Expected:

- focused tests PASS
- full `unittest discover` PASS
- `compileall` PASS

- [ ] **Step 5: Commit the local cleanup and full verification**

```bash
git add tests/test_action_executor.py \
  tests/test_devices.py \
  tests/test_android_adb_device.py \
  computer_use/devices/plugins/local/executor.py \
  computer_use/devices/coordinates.py \
  computer_use/agent.py
git commit -m "统一自然滚动配置语义"
```
