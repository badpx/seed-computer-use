# 历史上下文与截图组织

本文档说明 `computer_use` 在多轮任务中如何组织上下文、保留截图，以及何时注入执行反馈。它主要用于排障和理解行为，不是快速使用本项目的前置阅读材料。

## 每轮发送给模型的内容

每一轮调用模型时，代理会发送：

- 单独一份 system 提示词
- 会话历史中的用户指令消息
- 会话历史中的 assistant 历史响应
- 已展开并持久生效的 skill 指令消息
- 最近 `N` 张截图对应的图片消息，默认最多 5 张，包含当前轮
- 历史执行反馈文本

其中：

- 失败反馈始终会注入，帮助模型根据错误信息及时纠正
- 成功反馈默认关闭，可通过 `INCLUDE_EXECUTION_FEEDBACK` 或 CLI 开启

## 文本与图片的保留规则

### 文本消息

文本消息默认全部保留，包括：

- 用户指令
- assistant 响应
- skill 指令
- 执行反馈

### 图片消息

图片只保留最近 `MAX_CONTEXT_SCREENSHOTS` 张，默认值为 `5`，包含当前截图。

历史截图优先保存在限长内存队列中，不依赖本地截图文件回放。

## 执行反馈注入规则

### 失败反馈

失败反馈始终会进入上下文，不受 `INCLUDE_EXECUTION_FEEDBACK` 开关影响。典型场景包括：

- Action 解析失败
- 设备执行失败
- 当前设备不支持某个动作

失败反馈中会包含：

- `Parsed Action`
- `Execution Status`
- `Failure Reason`

### 成功反馈

成功反馈是否进入上下文，由 `INCLUDE_EXECUTION_FEEDBACK` 控制。

成功反馈中会包含：

- `Parsed Action`
- `Execution Status`
- `Execution Result`

## 上下文压缩

当估算上下文占用超过窗口的 90% 时，代理会按用户指令 turn 自动压缩旧历史：

- 把旧的 `user / assistant / feedback` 总结成更短的 `user + assistant` pair
- 丢弃这些旧 turn 对应的截图

这样可以尽量保留最近的视觉状态和最新的执行反馈，同时减少 token 消耗。

## 截图缩放与坐标还原

如果设置了 `SCREENSHOT_SIZE` 或 `--screenshot-size`，工具会先把截图强制缩放为 `NxN` 再传给模型。

当前约束：

- 仅支持正方形尺寸
- `pixel` 坐标会按“模型图尺寸 -> 真实截图尺寸”自动换算
- 目标设备若支持局部画面或目标切换，模型坐标会先相对于当前目标画面归一化，再交给对应设备插件执行

## 目标显示器或目标设备

如果当前设备支持 target selection，并且设置了 `DISPLAY_INDEX` 或 `--display-index`：

- 工具会只截取该目标的画面
- 模型输出的局部坐标会自动换算到设备执行所需的坐标系

内置 `local` 设备插件会把它解释为显示器编号。其他设备是否支持 target selection，取决于各自插件实现。

## 调试建议

- 常规调试：开启 `SAVE_CONTEXT_LOG=true`
- 需要看完整请求：额外传 `--verbose`
- 排查截图和坐标问题：重点看 JSONL 里的截图路径、截图尺寸、设备状态和执行反馈
