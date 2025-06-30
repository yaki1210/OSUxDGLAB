# main.py (修改后)

import customtkinter as ctk
from ui import OSUApp
from core import AppController

if __name__ == "__main__":
    # 1. 创建核心控制器
    controller = AppController()
    
    # 2. 创建UI，并将控制器注入其中
    # UI现在会自己创建和管理主窗口
    app_ui = OSUApp(controller)
    
    # 3. 将UI实例告知控制器，完成双向绑定
    controller.set_ui(app_ui)
    
    # 4. 启动UI主循环
    app_ui.run()