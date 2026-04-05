"""
截图模块
支持全屏截图和按需保存
"""

from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

import pyautogui
from PIL import Image


class ScreenshotManager:
    """截图管理器"""
    
    def __init__(self):
        self.format = 'png'
    
    def capture(
        self,
        filename: Optional[str] = None,
        save: bool = False,
        save_dir: Optional[str] = None,
    ) -> Tuple[Image.Image, Optional[str]]:
        """
        捕获全屏截图
        
        Args:
            filename: 自定义文件名，默认使用时间戳
            save: 是否保存截图
            save_dir: 保存目录；未指定时使用当前目录
            
        Returns:
            Tuple[Image.Image, Optional[str]]: (截图对象, 保存路径或None)
        """
        # 获取屏幕尺寸
        screen_width, screen_height = pyautogui.size()
        
        # 捕获全屏
        screenshot = pyautogui.screenshot(
            region=(0, 0, screen_width, screen_height)
        )
        
        if save:
            # 生成文件名
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"screenshot_{timestamp}.{self.format}"
            
            # 构建完整路径
            target_dir = Path(save_dir or '.')
            target_dir.mkdir(parents=True, exist_ok=True)
            save_path = target_dir / filename
            
            # 保存截图
            screenshot.save(save_path)
            
            return screenshot, str(save_path)
        
        return screenshot, None
    
screenshot_manager = ScreenshotManager()


def capture_screenshot(
    filename: Optional[str] = None,
    save: bool = False,
    save_dir: Optional[str] = None,
) -> Tuple[Image.Image, Optional[str]]:
    """
    便捷函数：捕获截图
    
    Args:
        filename: 自定义文件名
        save: 是否保存截图
        save_dir: 保存目录
        
    Returns:
        Tuple[Image.Image, Optional[str]]: (截图对象, 保存路径或None)
    """
    return screenshot_manager.capture(filename, save, save_dir)
