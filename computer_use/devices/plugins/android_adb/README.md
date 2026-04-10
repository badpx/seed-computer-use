# Android ADB Device Plugin

`android_adb` 设备插件通过 `adb` 控制已经连接到电脑的 Android 设备。

## 前提条件

- 已安装 Android platform tools
- `adb` 已在 `PATH` 中
- 启动 Agent 前，目标手机已经连接到电脑
- 当前仅支持默认 adb 目标，请确保同一时刻只连接一个手机或模拟器

## 启用方式

```bash
python -m computer_use "打开浏览器" \
  --device android_adb
```

或在 `.env` 中设置：

```bash
DEVICE_NAME=android_adb
```

## 私有配置

通过 `DEVICE_CONFIG_JSON` 传入。

### `swipe_settle_seconds`

`swipe` 动作执行后额外等待的秒数，用于避免下一次截图落在惯性滑动中的中间帧。

- 默认值：`1.0`

示例：

```bash
DEVICE_CONFIG_JSON={"swipe_settle_seconds":0.5}
```

### `app_name_to_package`

为 `open_app(app_name='...')` 提供自定义应用名到 Android package name 的映射。

示例：

```bash
DEVICE_CONFIG_JSON={"app_name_to_package":{"醒图":"com.xt.retouch"}}
```

插件内置了一小组常见应用映射，例如：

- `醒图`
- `微信`
- `抖音`
- `小红书`
- `Chrome`
- `设置`

如果已知 package name，也可以直接把 `app_name` 写成 package name。

## 当前限制

- 中文等非 ASCII 文本无法通过原生 `adb shell input text` 稳定输入，插件会返回明确错误提示
- 当前不支持多设备选择
- 当前不支持 target selection
