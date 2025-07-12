# OSUxDGLab

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**osu! x DG-lab**

OSUxDGLab 是一个桥接应用程序，它能读取来自 **TOSU (由 gosumemory 提供)** 的实时 osu! 游戏事件，并根据高度可定制的触发条件，自动向 DG-Lab 设备发送波形，从而将游戏中的关键时刻（如连击、失误、PP变化）转化为真实的物理反馈，极大地增强了您的游戏沉浸感。

![OSUxDGLab 主界面](https://raw.githubusercontent.com/yaki1210/OSUxDGLAB/main/assets/UI.png)

*OSUxDGLab 主界面，实时显示游戏数据与触发器配置。*

演示视频(https://www.bilibili.com/video/BV1q13nzaExX/)

---

### ✨ 主要功能

-   **支持lazer** 支持osu!(lazer)。
-   **精美图形界面:** 基于 CustomTkinter 构建的现代化用户界面，拥有深色主题。
-   **实时数据显示:** 即时查看您当前的 PP值和连击数。
-   **多种触发模式:**
    -   **Miss 模式:** 当您断连或出现失误时触发波形。它会智能地结合连击数清零和官方Miss计数，确保触发的精准性。
    -   **PP 模式:** 当您的即时 PP 下降超过设定的阈值时触发，用于惩罚严重失误。
    -   **奖励模式 (连击):** 当您达到特定的连击数里程碑时（例如每100 combo），触发奖励波形。
    -   **奖励模式 (PP):** 当您的即时 PP 上涨并越过设定的阈值时，触发奖励波形。
-   **高度可定制:** 每种模式都可以独立启用/禁用、选择输出通道 (A/B)、指定波形，并精确设置触发阈值。
-   **便捷的 DG-Lab 连接:** 通过生成二维码，让您使用官方App快速无缝地连接 DG-Lab 设备。
-   **稳健的连接处理:** 如果与 TOSU 的连接意外断开，程序会自动尝试重新连接。
-   **实时事件日志:** 详细的日志窗口会实时显示所有连接状态、触发事件和已发送的命令。
-   **测试与模拟:** 无需开始游戏，即可轻松测试任意波形在不同通道上的效果，或模拟一次 Miss/PP 事件来验证您的设置。
-   **设置持久化:** 您的所有配置都会被自动保存，并在下次启动时加载。

### 📋 前置要求

1.  **osu! 游戏:** 游戏本体。
2.  **TOSU:** 您必须已下载并正在运行 [tosu](https://github.com/tosuapp/tosu)。本程序通过连接它提供的 **TOSU** 服务来获取游戏数据。
3.  **DG-Lab 设备:** 一台 DG-Lab 实体设备及其配套的手机 App。
4.  **操作系统:** 主要在 Windows 上开发和测试。

### 🚀 如何使用

1.  **下载程序:**
    -   从本项目的 **[Releases 页面](https://github.com/luxunus/OSUxDGLAB/releases)** 下载最新的 `OSUxDGLab.exe` 文件，或下载OSUxDGLab.zip。

2.  **准备并启动TOSU:**
    -   确保您已经下载了 `tosu.exe`。
    -   **在启动本程序之前，请务必先运行 `tosu.exe`。** 这是最关键的一步！

3.  **运行 OSUxDGLab:**
    -   双击运行下载得到的 `OSUxDGLab.exe`。程序窗口将会出现。

4.  **连接 DG-Lab 设备:**
    -   程序会自动检测并显示您的本地 IP 地址。
    -   点击左上角的二维码图标。
    -   使用您的 DG-Lab 手机 App 扫描显示的二维码以连接设备。
    -   连接成功后，"DG-Lab" 状态标签会显示 "已连接设备"。

5.  **连接到 TOSU 服务:**
    -   点击 "连接 TOSU" 按钮。
    -   连接成功后，"TOSU" 状态标签会显示 "Connected"。

6.  **配置并开始游戏:**
    -   在 "Miss 模式"、"PP 模式" 和 "奖励模式" 标签页中，根据您的偏好启用模式、选择波形、通道和阈值。**您的设置会自动保存，无需手动点击保存按钮**。
    -   点击界面中央的巨大状态图标（连接后默认为停止标志），使其变为“工作中”的图标。
    -   现在，您可以开始玩 osu! 并感受真实的体感反馈了！
    -   要暂停反馈，再次点击中央的状态图标即可。

### ⚙️ 模式详解

-   **Miss 模式:** 在您断连时进行惩罚。非常适合用来训练稳定性。
-   **PP 模式:** 在您因失误导致潜在 PP 大幅下降时进行惩罚。这能让您切身感受到在高价值谱面段失误的“痛”。
-   **奖励模式:** 在您达成连击或 PP 里程碑时给予奖励，为您的精彩表现提供正向激励。
-   **设置文件:** 您的自定义配置保存在程序目录下的 `settings/user_settings.json` 文件中。如果需要，您可以备份或手动编辑此文件。

### 👨‍💻 致开发者

本项目使用 Python 编写，源代码已完全提供。如果您想从源码运行：

1.  克隆本仓库。
2.  确保您的 Python 环境中安装了必要的库，主要包括 `customtkinter`, `pydglab-ws`, `websocket-client`, `qrcode`, `Pillow`。
3.  直接运行 `main.py` 即可。
4.  打包命令参考：`nuitka --standalone --onefile ^  --windows-icon-from-ico=assets/app.ico ^  --include-data-dir=assets=assets ^  --include-data-dir=settings=settings ^  --enable-plugin=tk-inter ^  --include-module=websockets ^  --include-module=websockets.legacy ^  --include-package=websockets ^ --windows-console-mode=disable main.py`

### 📜 许可证

本项目采用 MIT 许可证。

### 🙏 致谢

-   **[tosu](https://github.com/tosuapp/tosu):** 感谢其提供了至关重要的实时游戏数据（TOSU服务）。
-   **[pydglab-ws](https://pypi.org/project/pydglab-ws/):** 感谢其出色的库，让与 DG-Lab 设备的通信变得简单直接。
-   **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter):** 感谢其构建了这个漂亮的现代化图形界面。
-   **[Nuitka](https://nuitka.net/):** 感谢这个优秀的 Python 编译器，使得打包分发变得可能。
