# VNC Device Plugin Design

## Summary

Add a built-in `vnc` device plugin so `ComputerUseAgent` can control remote devices over the VNC protocol. The plugin will use `vncdotool` for screenshots and input events while continuing to fit the existing `DeviceAdapter` interface. The agent core should remain unchanged: it captures a `DeviceFrame`, sends the current screenshot to the model, parses an action, normalizes coordinates globally, then dispatches a `DeviceCommand` to the selected device adapter.

The plugin is aimed at desktop GUI automation by default and uses the `computer` prompt profile unless the plugin config explicitly sets `prompt_profile=cellphone`. This allows the same plugin to drive remote devices that expose a phone-like UI over VNC without forcing a new prompt selection mechanism.

## Goals

- Add a built-in `vnc` device plugin under `computer_use/devices/plugins/vnc/`
- Reuse the existing device plugin architecture and global coordinate normalization
- Support long-lived VNC connections for multi-step tasks
- Support remote screenshots and standard mouse/keyboard actions through `vncdotool`
- Allow plugin config to choose between `computer` and `cellphone` prompt profiles
- Keep the first version limited to basic connection parameters: `host`, `port`, `password`

## Non-Goals

- Automatic reconnection or session recovery
- Multi-target selection such as `/display` or VNC monitor switching
- File transfer, clipboard sync, or remote window enumeration
- VNC-specific prompt templates
- Native phone-only actions such as `press_home` or `open_app`

## Plugin Surface

### Plugin identity

- Plugin name: `vnc`
- Plugin directory: `computer_use/devices/plugins/vnc/`
- Plugin manifest: `plugin.json`
- Plugin entrypoint: `plugin:create_adapter`

### Plugin config

The plugin accepts these JSON config fields:

- `host`: required, VNC server hostname or IP
- `port`: optional, defaults to the VNC port expected by the underlying client
- `password`: optional, VNC authentication password
- `prompt_profile`: optional, defaults to `computer`; may be set to `cellphone`
- `operating_system`: optional, prompt-injection hint; defaults to `Remote VNC Device`

Any missing `host` should be treated as a configuration error during adapter initialization.

### DeviceAdapter behavior

The `vnc` adapter implements the existing `DeviceAdapter` contract:

- `connect()`: establish and cache a long-lived VNC client connection
- `close()`: disconnect and release client resources
- `capture_frame()`: fetch the current remote framebuffer and return a `DeviceFrame`
- `execute_command()`: send normalized mouse or keyboard events
- `get_status()`: return stable connection status fields
- `get_environment_info()`: expose `operating_system`
- `get_prompt_profile()`: return `computer` by default or `cellphone` when configured

The adapter does not support target selection:

- `supports_target_selection()` remains `False`
- `list_targets()` remains empty
- `set_target()` remains unsupported

## Architecture

### Adapter structure

Add these files:

- `computer_use/devices/plugins/vnc/__init__.py`
- `computer_use/devices/plugins/vnc/plugin.json`
- `computer_use/devices/plugins/vnc/plugin.py`
- `computer_use/devices/plugins/vnc/adapter.py`

The adapter owns all `vncdotool` interaction. The agent must not import `vncdotool` directly.

### Connection lifecycle

The adapter keeps a long-lived VNC client connection for the lifetime of the agent session:

1. `connect()` creates the client and authenticates if needed.
2. The client is stored on the adapter instance.
3. `capture_frame()` and `execute_command()` reuse the same client.
4. `close()` explicitly disconnects and clears the stored client.

The first version does not attempt automatic reconnection. If the remote session drops after `connect()`, subsequent commands should fail clearly instead of silently reconnecting.

This mirrors the existing plugin design direction: the device adapter owns the transport lifecycle while the agent remains transport-agnostic.

## Prompt Profile and Environment Information

The plugin must expose prompt selection through `get_prompt_profile()`:

- default: `computer`
- configurable: `cellphone`

This keeps prompt selection inside the existing profile mechanism instead of adding device-name conditionals to the agent.

The plugin must also expose environment info:

- `operating_system`: use configured `operating_system` when present
- otherwise default to `Remote VNC Device`

This ensures system prompt injection describes the remote device rather than the local host running the agent.

## Screenshot Flow

### Screenshot source

`capture_frame()` uses `vncdotool` to retrieve the current remote screen image. The adapter should then encode the screenshot as a PNG data URL for `DeviceFrame.image_data_url`.

### Frame construction

The returned `DeviceFrame` must contain:

- `image_data_url`: `data:image/png;base64,...`
- `width`
- `height`
- `metadata`

Recommended metadata fields:

- `device_name: "vnc"`
- `capture_method: "vncdotool"`
- `host`
- `port`

### Width and height detection

Width and height should be derived through the existing shared helper path rather than private image parsing logic in the plugin:

1. get raw PNG bytes from the screenshot result
2. call `computer_use.devices.helpers.detect_image_size(...)`
3. construct the `DeviceFrame`

This keeps image metadata parsing centralized and consistent with other device plugins.

## Command Execution Model

The plugin receives already-normalized frame-local pixel coordinates through `DeviceCommand`. It must not reinterpret `coordinate_space`, `coordinate_scale`, or model-image dimensions.

### Supported command types

The first version supports these command types:

- `click`
- `double_click`
- `right_click`
- `move`
- `drag`
- `type_text`
- `hotkey`
- `key_down`
- `key_up`
- `scroll`
- `wait`

### Command semantics

#### click

- move pointer to `point`
- send left-button click

#### double_click

- move pointer to `point`
- send two left-button clicks

#### right_click

- move pointer to `point`
- send right-button click

#### move

- move pointer to `point`

#### drag

- move pointer to `start_point`
- press left mouse button
- move pointer to `end_point`
- release left mouse button

#### type_text

- send the string through the VNC keyboard input path
- preserve newline characters if the underlying library supports them; otherwise translate them into `enter`

#### hotkey

- parse the normalized hotkey payload into a key sequence
- press modifiers first, then the main key, then release in reverse order

#### key_down / key_up

- directly forward the normalized key event

#### scroll

- use VNC mouse wheel button events
- `up` maps to button `4`
- `down` maps to button `5`
- `left` maps to button `6`
- `right` maps to button `7`

Horizontal scroll support must be documented as environment-dependent because many VNC servers and remote desktop stacks only reliably support vertical wheel buttons.

#### wait

- do not send any VNC command
- sleep locally in the adapter
- clamp to the same `1-60` second range used by other device plugins

### Unsupported commands

The plugin should clearly reject unsupported commands such as:

- `open_app`
- `press_home`
- `press_back`
- any device-specific command not listed above

The error should be explicit: `vnc 不支持命令类型: <name>`.

## Error Handling

The plugin should fail clearly and early with actionable messages.

### Configuration errors

- missing `host`: `vnc 设备配置缺少 host`

### Connection errors

- connection failure: `vnc connect 失败: ...`
- authentication failure: `vnc 认证失败: ...`

### Screenshot errors

- screenshot capture failure: `vnc capture screenshot 失败: ...`
- invalid image bytes: include a short cause from the image helper

### Command execution errors

- event send failure: `vnc <action> 失败: ...`
- malformed coordinates or keys: raise `ValueError` with `vnc` in the message

The adapter should not silently retry or downgrade failing commands in v1.

## Dependency Strategy

Add `vncdotool` as a project dependency and mention it in environment checks and documentation.

The plugin assumes:

- network reachability to the target VNC server
- credentials are already known
- the remote target is ready for GUI interaction

The design does not assume local shell access on the remote system.

## Testing Strategy

Add dedicated unit tests, modeled after the existing `android_adb` and `local` plugin tests.

### Plugin discovery

- built-in `vnc` plugin is discoverable
- `create_device_adapter(device_name='vnc', ...)` loads the correct adapter

### Prompt profile and environment info

- default profile is `computer`
- configured `prompt_profile='cellphone'` is honored
- `operating_system` defaults to `Remote VNC Device`
- configured `operating_system` is returned by `get_environment_info()`

### Screenshot behavior

- screenshot bytes are converted into a PNG data URL `DeviceFrame`
- width and height are populated through `detect_image_size`
- metadata includes `device_name`, `host`, and `port`

### Command mapping

- `click`
- `double_click`
- `right_click`
- `move`
- `drag`
- `type_text`
- `hotkey`
- `key_down`
- `key_up`
- `scroll` for `up/down/left/right`
- `wait`

Tests should verify the exact `vncdotool` client calls made for each command.

### Failure cases

- missing `host`
- failed connection
- failed authentication
- failed screenshot
- unsupported command types
- malformed coordinate payloads

### Agent integration

- agent selects `COMPUTER_USE_DOUBAO` when `prompt_profile=computer`
- agent selects `PHONE_USE_DOUBAO` when `prompt_profile=cellphone`

## Documentation Updates

Update:

- `README.md`
- `.env.example`
- `check_env.py`

The documentation should include:

- `DEVICE_NAME=vnc`
- `DEVICE_CONFIG_JSON` example with `host`, `port`, `password`
- note that `prompt_profile` may be set to `cellphone`
- note that horizontal scroll support depends on the remote VNC environment
- note that the plugin requires `vncdotool`

## Future Extensions

These are intentionally out of scope for v1 but fit the design:

- automatic reconnect
- configurable reconnect policy
- VNC target presets or named connections
- clipboard sync
- multiple display selection if the VNC server exposes it
- richer remote environment reporting
- alternative prompt profiles beyond `computer` and `cellphone`
