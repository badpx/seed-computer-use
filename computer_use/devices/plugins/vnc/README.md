# VNC Device Plugin

`vnc` 设备插件通过 `vncdotool` 连接并控制远程 VNC 设备。

## 前提条件

- 已执行 `pip install -r requirements.txt`
- 目标 VNC 服务端可访问
- 若服务端启用了密码认证，需要在配置中提供 `password`

## 启用方式

```bash
python -m computer_use "打开远程浏览器" \
  --device vnc \
  --device-config-json '{"host":"127.0.0.1","port":5900,"password":"secret"}'
```

或在 `.env` 中设置：

```bash
DEVICE_NAME=vnc
DEVICE_CONFIG_JSON={"host":"127.0.0.1","port":5900,"password":"secret"}
```

## 私有配置

### 必需字段

- `host`

### 可选字段

- `port`
- `password`
- `prompt_profile`
- `operating_system`

示例：

```bash
DEVICE_CONFIG_JSON={"host":"127.0.0.1","port":5900,"password":"secret"}
```

切换到手机动作空间：

```bash
DEVICE_CONFIG_JSON={"host":"127.0.0.1","port":5901,"prompt_profile":"cellphone","operating_system":"Android"}
```

## 当前限制

- `type_text` 仅稳定支持 ASCII 文本；非 ASCII 文本会返回明确错误
- `scroll(left/right)` 会尝试发送 VNC 扩展滚轮按钮 `6/7`，是否生效取决于远端 VNC 服务端和目标系统
- 当前不支持 target selection
