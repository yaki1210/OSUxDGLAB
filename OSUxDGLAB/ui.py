# ui.py (完全重写)

import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import qrcode
import datetime
import os
import sys

import config
import utils

class OSUApp:
    def __init__(self, controller):
        self.controller = controller

        # --- Setup Root Window ---
        self.root = ctk.CTk()
        self.root.title("OSUxDGLab")
        self.root.geometry("1000x650") # 修改为横向默认大小
        self.root.resizable(True, True) # 允许窗口自定义大小

        # --- Theming ---
        ctk.set_appearance_mode("dark")
        self.accent_color = config.FG_COLOR # #FFE99D
        self.bg_color = config.BG_COLOR # #171717

        # --- Apply Mica/Acrylic effect on Windows 11 ---
        self._setup_transparent_window()

        # --- Load Assets ---
        current_dir = os.path.dirname(__file__)
        assets_dir = os.path.join(current_dir, "assets")
        # 设置窗口图标
        try:
            icon_path = os.path.join(assets_dir, "app.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                print(f"警告: 无法找到图标文件: {icon_path}")
        except Exception as e:
            print(f"设置图标时发生错误: {e}")
        # 确保图片存在，否则使用占位符
        try:
            self.qr_icon = ctk.CTkImage(Image.open(os.path.join(assets_dir, "qr_code.png")), size=(32, 32))
        except FileNotFoundError:
            print("警告: 无法加载 qr_code.png，使用默认图标。")
            self.qr_icon = None # 可以替换为默认的CTkImage或None
        try:
            self.refresh_icon = ctk.CTkImage(Image.open(os.path.join(assets_dir, "refresh.png")), size=(32, 32))
        except FileNotFoundError:
            print("警告: 无法加载 refresh.png，使用默认图标。")
            self.refresh_icon = None # 可以替换为默认的CTkImage或None

        # Load new status icons
        try:
            self.waiting_icon = ctk.CTkImage(Image.open(os.path.join(assets_dir, "waiting.png")), size=(64, 64))
        except FileNotFoundError:
            print("警告: 无法加载 waiting.png，使用默认图标。")
            self.waiting_icon = None
        try:
            self.stoping_icon = ctk.CTkImage(Image.open(os.path.join(assets_dir, "stoping.png")), size=(64, 64))
        except FileNotFoundError:
            print("警告: 无法加载 stoping.png，使用默认图标。")
            self.stoping_icon = None
        try:
            self.working_icon = ctk.CTkImage(Image.open(os.path.join(assets_dir, "working.png")), size=(64, 64))
        except FileNotFoundError:
            print("警告: 无法加载 working.png，使用默认图标。")
            self.working_icon = None

        # --- UI Variables ---
        self.dg_ip = ctk.StringVar(value=utils.get_local_ip())
        self.qr_url = None
        self.qr_photo = None
        
        # --- Create Widgets ---
        self._create_widgets()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.controller.start_dglab(self.dg_ip.get())

    def run(self):
        self.root.mainloop()

    def _setup_transparent_window(self):
        # For Windows 11 Mica/Acrylic effect
        try:
            if sys.platform == "win32":
                from ctypes import windll, byref, c_int
                # 设置应用程序的用户模型 ID (AppUserModelID) 以确保任务栏图标显示
                my_app_id = u"com.luxunus.OSUxDGLAB" # 替换为你的应用程序的唯一ID
                windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)
                # 可选：设置 DWMWA_WINDOW_CORNER_PREFERENCE 为圆角 (2 for rounded, 3 for small rounded)
                # value = c_int(2)
                # windll.dwmapi.DwmSetWindowAttribute(self.root.winfo_id(), 33, byref(value), 4) # DWMWA_WINDOW_CORNER_PREFERENCE
        except Exception as e:
            print(f"无法设置窗口透明度: {e}")


    def _create_widgets(self):
        # 调整根窗口的网格布局，支持横向扩展
        self.root.grid_columnconfigure((0, 1), weight=1) # 两列，每列权重为1
        self.root.grid_rowconfigure(0, weight=1) # 一行，权重为1 (主要内容区域)

        # --- 左侧控制面板 ---
        left_panel_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        left_panel_frame.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        left_panel_frame.grid_columnconfigure(0, weight=1)
        left_panel_frame.grid_rowconfigure((4, 5), weight=1) # 让Tabview和Log区域可扩展

        # DG-Lab IP 和连接状态
        dglab_section_frame = ctk.CTkFrame(left_panel_frame, fg_color="transparent")
        dglab_section_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        dglab_section_frame.grid_columnconfigure(0, weight=1)

        ip_entry_frame = ctk.CTkFrame(dglab_section_frame, fg_color="transparent")
        ip_entry_frame.grid(row=0, column=0, sticky="ew", pady=(0,5))
        ip_entry_frame.grid_columnconfigure(0, weight=1)

        ip_entry = ctk.CTkEntry(ip_entry_frame, textvariable=self.dg_ip, width=150,
                                fg_color=config.ACCENT_COLOR, text_color=self.accent_color,
                                border_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        ip_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # 刷新二维码按钮（图标替代文字，鼠标悬停显示文字）
        refresh_button = ctk.CTkButton(ip_entry_frame, image=self.refresh_icon, text="", width=30, height=30,
                                       command=lambda: self.controller.start_dglab(self.dg_ip.get()),
                                       fg_color="transparent", hover_color=config.BUTTON_ACTIVE_BG, corner_radius=config.BUTTON_CORNER_RADIUS) # 透明背景，圆角
        
        if self.refresh_icon: refresh_button.pack(side="left", padx=5)
        else: refresh_button.configure(text="刷新", width=60).pack(side="left", padx=5) # 兼容无图标

        # 二维码按钮（图标替代文字，鼠标悬停显示文字）
        qr_button = ctk.CTkButton(ip_entry_frame, image=self.qr_icon, text="", width=30, height=30,
                                  command=self._open_qr_window,
                                  fg_color="transparent", hover_color=config.BUTTON_ACTIVE_BG, corner_radius=config.BUTTON_CORNER_RADIUS) # 透明背景，圆角

        if self.qr_icon: qr_button.pack(side="left")
        else: qr_button.configure(text="二维码", width=60).pack(side="left") # 兼容无图标

        self.dglab_status_label = ctk.CTkLabel(dglab_section_frame, text="DG-Lab: 初始化中...", text_color=self.accent_color)
        self.dglab_status_label.grid(row=1, column=0, sticky="w", pady=(5,0))

        # TOSU 控制和状态
        tosu_section_frame = ctk.CTkFrame(left_panel_frame, fg_color="transparent")
        tosu_section_frame.grid(row=1, column=0, pady=(10, 10), sticky="ew")
        tosu_section_frame.grid_columnconfigure(0, weight=1)

        self.tosu_status_label = ctk.CTkLabel(tosu_section_frame, text="TOSU: 已断开", text_color=self.accent_color)
        self.tosu_status_label.grid(row=0, column=0, sticky="w")
        
        self.connect_tosu_button = ctk.CTkButton(tosu_section_frame, text="连接 TOSU", command=self.controller.connect_to_tosu,
                                                 fg_color=config.CONNECT_COLOR, hover_color=config.CONNECT_COLOR_HOVER,
                                                 text_color=config.BUTTON_FG_COLOR, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        self.connect_tosu_button.grid(row=0, column=1, padx=(10,0), sticky="e")


        # --- 游戏数据显示 (PP, Combo) ---
        data_display_frame = ctk.CTkFrame(left_panel_frame, fg_color="transparent")
        data_display_frame.grid(row=2, column=0, padx=0, pady=(0, 10), sticky="ew")
        data_display_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.pp_label = ctk.CTkLabel(data_display_frame, text="PP: N/A", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.accent_color)
        self.pp_label.grid(row=0, column=0, sticky="e", padx=10)
        self.combo_label = ctk.CTkLabel(data_display_frame, text="Combo: N/A", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.accent_color)
        self.combo_label.grid(row=0, column=1, sticky="w", padx=10)
        # self.accuracy_label = ctk.CTkLabel(data_display_frame, text="准确度: N/A", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.accent_color)
        # self.accuracy_label.grid(row=1, column=0, columnspan=2, pady=(5,0), sticky="n") # Placed below PP and Combo
        # self.miss_count_label = ctk.CTkLabel(data_display_frame, text="Miss: N/A", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.accent_color)
        # self.miss_count_label.grid(row=1, column=1, sticky="w", padx=10, pady=(5,0))

        # Status icon below PP and Combo, now also the toggle button
        self.status_icon_label = ctk.CTkLabel(left_panel_frame, text="", image=self.waiting_icon, fg_color="transparent")
        self.status_icon_label.grid(row=3, column=0, pady=(10, 0), sticky="n") # 保持在PP和Combo下方
        self.status_icon_label.bind("<Button-1>", lambda event: self.controller.toggle_monitoring()) # 绑定点击事件
        # self._add_tooltip(self.status_icon_label, "点击开始/停止监控") # 添加工具提示

        # --- 模式配置标签页 ---
        tab_view = ctk.CTkTabview(left_panel_frame, fg_color=config.ACCENT_COLOR,
                                  segmented_button_selected_color=config.ACCENT_COLOR, # 选中后不改变背景颜色
                                  segmented_button_selected_hover_color=config.ACCENT_COLOR_HOVER, # 选中后悬停颜色
                                  segmented_button_unselected_color=config.ACCENT_COLOR,
                                  segmented_button_unselected_hover_color=config.ACCENT_COLOR_HOVER,
                                  text_color=self.accent_color,
                                  corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        tab_view.grid(row=4, column=0, padx=0, pady=10, sticky="nsew") # 填充剩余空间, 保持 row=4
        
        waveforms = list(config.PULSE_DATA.keys())
        
        self.miss_widgets = self._create_mode_tab(tab_view.add("Miss 模式"), "MISS", waveforms)
        self.pp_widgets = self._create_mode_tab(tab_view.add("PP 模式"), "PP", waveforms)
        self.reward_widgets = self._create_mode_tab(tab_view.add("奖励模式"), "reward", waveforms)

        # --- 右侧日志和控制面板 ---
        right_panel_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        right_panel_frame.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        right_panel_frame.grid_columnconfigure(0, weight=1)
        right_panel_frame.grid_rowconfigure(1, weight=1) # 让Log区域可扩展

        # 控制按钮 (全屏/恢复，测试通道)
        control_buttons_frame = ctk.CTkFrame(right_panel_frame, fg_color="transparent")
        control_buttons_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        control_buttons_frame.grid_columnconfigure((0, 1), weight=1) # 两列

        # # 全屏/恢复按钮
        # self.fullscreen_button = ctk.CTkButton(control_buttons_frame, text="全屏", command=self._toggle_fullscreen,
        #                                       fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
        #                                       text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        # self.fullscreen_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        # self.restore_button = ctk.CTkButton(control_buttons_frame, text="恢复", command=self._restore_window,
        #                                     fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
        #                                     text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        # self.restore_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        # self.restore_button.pack_forget() # 默认隐藏

        # 测试波形选择器
        test_waveform_frame = ctk.CTkFrame(control_buttons_frame, fg_color="transparent")
        # 由于删除了全屏/恢复按钮，测试波形选择器现在应该在第0行
        test_waveform_frame.grid(row=0, column=0, columnspan=2, pady=5, sticky="ew") # 将row从1改为0
        test_waveform_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(test_waveform_frame, text="测试波形:", text_color=self.accent_color).grid(row=0, column=0, sticky="w", padx=(0,5))
        self.test_waveform_var = ctk.StringVar(value=waveforms[0] if waveforms else "")
        test_waveform_menu = ctk.CTkOptionMenu(test_waveform_frame, variable=self.test_waveform_var, values=waveforms,
                                                fg_color=config.ACCENT_COLOR, button_color=config.ACCENT_COLOR,
                                                button_hover_color=config.ACCENT_COLOR_HOVER,
                                                dropdown_fg_color=config.ACCENT_COLOR, dropdown_hover_color=config.ACCENT_COLOR_HOVER,
                                                text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        test_waveform_menu.grid(row=0, column=1, sticky="ew", padx=(5,0))

        # 测试通道按钮
        test_channels_frame = ctk.CTkFrame(control_buttons_frame, fg_color="transparent")
        # 由于删除了全屏/恢复按钮，测试通道按钮现在应该在第1行
        test_channels_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew") # 将row从2改为1
        test_channels_frame.grid_columnconfigure((0, 1), weight=1)

        test_a_button = ctk.CTkButton(test_channels_frame, text="测试通道 A", command=lambda: self.controller.send_test_pulse('A', self.test_waveform_var.get()),
                                       fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                                       text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        test_a_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        test_b_button = ctk.CTkButton(test_channels_frame, text="测试通道 B", command=lambda: self.controller.send_test_pulse('B', self.test_waveform_var.get()),
                                       fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                                       text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        test_b_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        test_miss_pp_button = ctk.CTkButton(control_buttons_frame, text="测试 Miss/PP 模式", command=self.controller.simulate_miss_pp_mode,
                                            fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                                            text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        test_miss_pp_button.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew") # 新增一行，跨两列
        
        # save_settings_button = ctk.CTkButton(control_buttons_frame, text="保存当前设置 (调试)", command=self._save_current_settings_to_file,
        #                                      fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
        #                                      text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS)
        # save_settings_button.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew") # 放置在新的一行

        # 日志区域
        log_frame = ctk.CTkFrame(right_panel_frame, fg_color=config.ACCENT_COLOR, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_box = ctk.CTkTextbox(log_frame, state="disabled", text_color=self.accent_color, activate_scrollbars=True,
                                      fg_color=config.BG_COLOR, border_color=config.ACCENT_COLOR, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        self.log_box.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        log_buttons_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_buttons_frame.grid(row=1, column=0, sticky="ew", pady=(5,0))
        log_buttons_frame.grid_columnconfigure((0,1), weight=1)

        save_log_button = ctk.CTkButton(log_buttons_frame, text="保存日志", command=self._save_log,
                                         fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                                         text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        save_log_button.grid(row=0, column=0, padx=(0, 5), sticky="w")
        clear_log_button = ctk.CTkButton(log_buttons_frame, text="清空日志", command=self._clear_log,
                                         fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                                         text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        clear_log_button.grid(row=0, column=1, padx=(5, 0), sticky="e")


    def _create_mode_tab(self, tab, mode_name, waveforms):
        tab.grid_columnconfigure(1, weight=1)
        widgets = {}

        # Enable Switch
        if mode_name != 'reward':
            widgets['enabled_var'] = ctk.BooleanVar(value=(mode_name == 'MISS'))
            display_mode_name = mode_name.title()
            if mode_name == 'PP':
                display_mode_name = 'PP'
            elif mode_name == 'MISS': 
                display_mode_name = 'Miss'

            ctk.CTkSwitch(tab, text=f"启用 {display_mode_name} 模式", variable=widgets['enabled_var'],                          onvalue=True, offvalue=False, text_color=self.accent_color,
                          button_color=config.ACCENT_COLOR_HOVER, button_hover_color=config.ACCENT_COLOR_HOVER,
                          progress_color=self.accent_color).grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w")
        
            # 波形和通道设置 (仅用于 Miss 和 PP 模式)
            # Waveform
            ctk.CTkLabel(tab, text="波形:", text_color=self.accent_color).grid(row=1, column=0, padx=10, pady=5, sticky="w")
            widgets['waveform_var'] = ctk.StringVar(value='潮汐' if mode_name in ['MISS', 'PP'] else '呼吸')
            ctk.CTkOptionMenu(tab, variable=widgets['waveform_var'], values=waveforms,
                              fg_color=config.ACCENT_COLOR, button_color=config.ACCENT_COLOR,
                              button_hover_color=config.ACCENT_COLOR_HOVER,
                              dropdown_fg_color=config.ACCENT_COLOR, dropdown_hover_color=config.ACCENT_COLOR_HOVER,
                              text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS).grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="ew") # 圆角

            # Channels
            ctk.CTkLabel(tab, text="通道:", text_color=self.accent_color).grid(row=2, column=0, padx=10, pady=5, sticky="w")
            channel_frame = ctk.CTkFrame(tab, fg_color="transparent")
            channel_frame.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="w")
            widgets['ch_a_var'] = ctk.BooleanVar(value=True)
            widgets['ch_b_var'] = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(channel_frame, text="A", variable=widgets['ch_a_var'],
                            fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                            text_color=self.accent_color, checkbox_width=20, checkbox_height=20, corner_radius=config.BUTTON_CORNER_RADIUS).pack(side="left", padx=5) # 圆角
            ctk.CTkCheckBox(channel_frame, text="B", variable=widgets['ch_b_var'],
                            fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                            text_color=self.accent_color, checkbox_width=20, checkbox_height=20, corner_radius=config.BUTTON_CORNER_RADIUS).pack(side="left", padx=5) # 圆角

        # Mode-specific settings
        if mode_name == 'PP':
            widgets['threshold_var'], _, _ = self._create_linked_slider_entry(tab, "PP 下降阈值:", 3, (0.01, 10.0), 1.00)
        elif mode_name == 'reward':
            # 奖励模式的独立启用开关，放在同一行
            reward_switches_frame = ctk.CTkFrame(tab, fg_color="transparent")
            reward_switches_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w")
            reward_switches_frame.grid_columnconfigure((0, 1), weight=1) # 两列

            widgets['combo_enabled_var'] = ctk.BooleanVar(value=False)
            combo_switch = ctk.CTkSwitch(reward_switches_frame, text="启用连击奖励模式", variable=widgets['combo_enabled_var'],
                                         onvalue=True, offvalue=False, text_color=self.accent_color,
                                         button_color=config.ACCENT_COLOR_HOVER, button_hover_color=config.ACCENT_COLOR_HOVER,
                                         progress_color=self.accent_color)
            combo_switch.grid(row=0, column=0, padx=5, sticky="w")

            widgets['pp_enabled_var'] = ctk.BooleanVar(value=False)
            pp_switch = ctk.CTkSwitch(reward_switches_frame, text="启用PP奖励模式", variable=widgets['pp_enabled_var'],
                                      onvalue=True, offvalue=False, text_color=self.accent_color,
                                      button_color=config.ACCENT_COLOR_HOVER, # 恢复按钮颜色为 config.ACCENT_COLOR
                                      button_hover_color=config.ACCENT_COLOR_HOVER,
                                      progress_color=self.accent_color)
            pp_switch.grid(row=0, column=1, padx=5, sticky="w")


            # 连击奖励设置的容器
            combo_settings_frame = ctk.CTkFrame(tab, fg_color="transparent")
            combo_settings_frame.grid_columnconfigure(1, weight=1) # 允许第二列扩展
            
            # PP奖励设置的容器
            pp_settings_frame = ctk.CTkFrame(tab, fg_color="transparent")
            pp_settings_frame.grid_columnconfigure(1, weight=1) # 允许第二列扩展


            # Combo 奖励设置
            ctk.CTkLabel(combo_settings_frame, text="连击奖励波形:", text_color=self.accent_color).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            widgets['combo_waveform_var'] = ctk.StringVar(value='潮汐')
            ctk.CTkOptionMenu(combo_settings_frame, variable=widgets['combo_waveform_var'], values=waveforms,
                              fg_color=config.ACCENT_COLOR, button_color=config.ACCENT_COLOR,
                              button_hover_color=config.ACCENT_COLOR_HOVER,
                              dropdown_fg_color=config.ACCENT_COLOR, dropdown_hover_color=config.ACCENT_COLOR_HOVER,
                              text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS).grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

            ctk.CTkLabel(combo_settings_frame, text="连击奖励通道:", text_color=self.accent_color).grid(row=1, column=0, padx=10, pady=5, sticky="w")
            combo_channel_frame = ctk.CTkFrame(combo_settings_frame, fg_color="transparent")
            combo_channel_frame.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="w")
            widgets['combo_ch_a_var'] = ctk.BooleanVar(value=True)
            widgets['combo_ch_b_var'] = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(combo_channel_frame, text="A", variable=widgets['combo_ch_a_var'],
                            fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                            text_color=self.accent_color, checkbox_width=20, checkbox_height=20, corner_radius=config.BUTTON_CORNER_RADIUS).pack(side="left", padx=5)
            ctk.CTkCheckBox(combo_channel_frame, text="B", variable=widgets['combo_ch_b_var'],
                            fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                            text_color=self.accent_color, checkbox_width=20, checkbox_height=20, corner_radius=config.BUTTON_CORNER_RADIUS).pack(side="left", padx=5)

            widgets['combo_threshold_var'], _, _ = self._create_linked_slider_entry(combo_settings_frame, "连击阈值:", 2, (1, 1000), 100, is_int=True)


            # PP 奖励设置
            ctk.CTkLabel(pp_settings_frame, text="PP奖励波形:", text_color=self.accent_color).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            widgets['pp_reward_waveform_var'] = ctk.StringVar(value='呼吸')
            ctk.CTkOptionMenu(pp_settings_frame, variable=widgets['pp_reward_waveform_var'], values=waveforms,
                              fg_color=config.ACCENT_COLOR, button_color=config.ACCENT_COLOR,
                              button_hover_color=config.ACCENT_COLOR_HOVER,
                              dropdown_fg_color=config.ACCENT_COLOR, dropdown_hover_color=config.ACCENT_COLOR_HOVER,
                              text_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS).grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

            ctk.CTkLabel(pp_settings_frame, text="PP奖励通道:", text_color=self.accent_color).grid(row=1, column=0, padx=10, pady=5, sticky="w")
            pp_reward_channel_frame = ctk.CTkFrame(pp_settings_frame, fg_color="transparent")
            pp_reward_channel_frame.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="w")
            widgets['pp_reward_ch_a_var'] = ctk.BooleanVar(value=True)
            widgets['pp_reward_ch_b_var'] = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(pp_reward_channel_frame, text="A", variable=widgets['pp_reward_ch_a_var'],
                            fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                            text_color=self.accent_color, checkbox_width=20, checkbox_height=20, corner_radius=config.BUTTON_CORNER_RADIUS).pack(side="left", padx=5)
            ctk.CTkCheckBox(pp_reward_channel_frame, text="B", variable=widgets['pp_reward_ch_b_var'],
                            fg_color=config.ACCENT_COLOR, hover_color=config.ACCENT_COLOR_HOVER,
                            text_color=self.accent_color, checkbox_width=20, checkbox_height=20, corner_radius=config.BUTTON_CORNER_RADIUS).pack(side="left", padx=5)

            widgets['pp_increase_var'], _, _ = self._create_linked_slider_entry(pp_settings_frame, "PP增加阈值:", 2, (0.01, 100.0), 10.00)

            # 函数来控制设置内容的显示/隐藏
            def toggle_combo_settings():
                if widgets['combo_enabled_var'].get():
                    combo_settings_frame.grid(row=1, column=0, columnspan=3, sticky="ew") # 调整行号
                else:
                    combo_settings_frame.grid_forget()

            def toggle_pp_settings():
                # PP设置的起始行会根据连击设置的可见性而变化
                if widgets['pp_enabled_var'].get():
                    # 如果连击设置关闭，PP设置从第2行开始，否则从第3行开始
                    pp_settings_frame.grid(row=2 if not widgets['combo_enabled_var'].get() else 3, column=0, columnspan=3, sticky="ew")
                else:
                    pp_settings_frame.grid_forget()

            # 绑定命令
            widgets['combo_enabled_var'].trace_add("write", lambda *args: toggle_combo_settings())
            widgets['pp_enabled_var'].trace_add("write", lambda *args: toggle_pp_settings())

            # 初始调用以设置可见性
            toggle_combo_settings()
            toggle_pp_settings()
            
        return widgets

    def _create_linked_slider_entry(self, parent, label, row, range_tuple, default_val, is_int=False):
        var = ctk.IntVar(value=int(default_val)) if is_int else ctk.DoubleVar(value=default_val)
        
        ctk.CTkLabel(parent, text=label, text_color=self.accent_color).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        def update_entry(value):
            formatted_value = f"{int(float(value))}" if is_int else f"{float(value):.2f}"
            entry.delete(0, "end")
            entry.insert(0, formatted_value)

        def update_slider(event=None):
            try:
                val = int(entry.get()) if is_int else float(entry.get())
                if range_tuple[0] <= val <= range_tuple[1]:
                    slider.set(val)
                else:
                    update_entry(slider.get()) # Revert if out of bounds
            except ValueError:
                update_entry(slider.get()) # Revert if invalid input
        
        slider = ctk.CTkSlider(parent, from_=range_tuple[0], to=range_tuple[1], variable=var, command=update_entry,
                               fg_color=config.ACCENT_COLOR, progress_color=self.accent_color, button_color=self.accent_color,
                               button_hover_color=config.ACCENT_COLOR_HOVER)
        slider.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        entry = ctk.CTkEntry(parent, textvariable=ctk.StringVar(value=f"{default_val}"), width=70,
                             fg_color=config.ACCENT_COLOR, text_color=self.accent_color,
                             border_color=self.accent_color, corner_radius=config.BUTTON_CORNER_RADIUS) # 圆角
        entry.grid(row=row, column=2, padx=10, pady=5, sticky="e")
        entry.bind("<Return>", update_slider)
        entry.bind("<FocusOut>", update_slider)
        
        return var, slider, entry

    # --- Public Methods (called by Controller) ---
    def get_current_settings(self):
        def get_channels(widgets_dict, prefix=''): # 恢复 prefix 参数，并设置默认值
            channels = []
            # 根据是否存在 prefix 构建键名
            ch_a_key = f'{prefix}_ch_a_var' if prefix else 'ch_a_var'
            ch_b_key = f'{prefix}_ch_b_var' if prefix else 'ch_b_var'

            if widgets_dict.get(ch_a_key) and widgets_dict[ch_a_key].get(): channels.append('A')
            if widgets_dict.get(ch_b_key) and widgets_dict[ch_b_key].get(): channels.append('B')
            return channels

        settings = {
            'miss_mode_enabled': self.miss_widgets['enabled_var'].get(),
            'miss_waveform': self.miss_widgets['waveform_var'].get(),
            'miss_channels': get_channels(self.miss_widgets, ''), # 显式传递空字符串

            'pp_mode_enabled': self.pp_widgets['enabled_var'].get(),
            'pp_waveform': self.pp_widgets['waveform_var'].get(),
            'pp_channels': get_channels(self.pp_widgets, ''), # 显式传递空字符串
            'pp_threshold': self.pp_widgets['threshold_var'].get(),

            # 奖励模式的独立启用开关
            'combo_mode_enabled': self.reward_widgets['combo_enabled_var'].get(),
            'pp_reward_enabled': self.reward_widgets['pp_enabled_var'].get(),
            'combo_threshold': self.reward_widgets['combo_threshold_var'].get(),
            'pp_increase_threshold': self.reward_widgets['pp_increase_var'].get(),
            
            'reward_combo_waveform': self.reward_widgets['combo_waveform_var'].get(),
            'reward_combo_channels': get_channels(self.reward_widgets, 'combo_ch'), # 传递正确的 'combo_ch' 前缀
            'reward_pp_waveform': self.reward_widgets['pp_reward_waveform_var'].get(),
            'reward_pp_channels': get_channels(self.reward_widgets, 'pp_reward_ch'), # 传递正确的 'pp_reward_ch' 前缀
        }
        # Add test waveform to settings for controller to use
        settings['test_waveform'] = self.test_waveform_var.get()
        return settings

    def _add_tooltip(self, widget, text):
        tooltip_window = None
        def enter(event):
            nonlocal tooltip_window
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            tooltip_window = ctk.CTkToplevel(widget)
            tooltip_window.wm_overrideredirect(True)
            tooltip_window.wm_geometry(f"+{x}+{y}")
            label = ctk.CTkLabel(tooltip_window, text=text,
                                 fg_color=config.ACCENT_COLOR, text_color=self.accent_color,
                                 corner_radius=config.BUTTON_CORNER_RADIUS, padx=5, pady=3)
            label.pack()

        def leave(event):
            nonlocal tooltip_window
            if tooltip_window:
                tooltip_window.destroy()
                tooltip_window = None

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    # def _toggle_fullscreen(self):
    #     if self.root.attributes("-fullscreen"):
    #         self.root.attributes("-fullscreen", False)
    #         self.fullscreen_button.pack(side="left", padx=(0,5), fill="x", expand=True) # Fullscreen is now 0-col
    #         self.restore_button.pack_forget()
    #     else:
    #         self.root.attributes("-fullscreen", True)
    #         self.fullscreen_button.pack_forget()
    #         self.restore_button.pack(side="left", padx=(0,5), fill="x", expand=True) # Restore is now 0-col

    # def _restore_window(self):
    #     self.root.attributes("-fullscreen", False)
    #     # Restore original geometry
    #     self.root.geometry("1000x600")
    #     self.fullscreen_button.pack(side="left", padx=(0,5), fill="x", expand=True) # Fullscreen is now 0-col
    #     self.restore_button.pack_forget()
        
    def update_dglab_status(self, status, message):
        self.dglab_status_label.configure(text=f"DG-Lab: {message or status}", text_color=config.CONNECTED_COLOR if status == "connected" else config.CONNECT_FAIL_COLOR)
        # Update the status icon based on DG-Lab connection and monitoring status
        self._update_status_icon(self.controller.dglab.is_connected, self.controller.is_monitoring)
        
    def update_tosu_status(self, status):
        status_map = {"connecting": ("Connecting...", "orange"), "connected": ("Connected", "#FFE99D"), "disconnected": ("Disconnected", "red")}
        text, color = status_map.get(status, ("Unknown", "gray"))
        self.tosu_status_label.configure(text=f"TOSU: {text}", text_color=color)

    def update_game_data(self, pp_str, combo_str,accuracy_str,miss_count_str):
        self.pp_label.configure(text=f"PP: {pp_str if pp_str else 'N/A'}")
        self.combo_label.configure(text=f"Combo: {combo_str if combo_str else 'N/A'}")
        # self.accuracy_label.configure(text=f"准确度: {accuracy_str or 'N/A'}")
        # self.miss_count_label.configure(text=f"Miss: {miss_count_str or 'N/A'}")

    def update_monitoring_status(self, is_on):
        self._update_status_icon(self.controller.dglab.is_connected, is_on)

    def _update_status_icon(self, dglab_connected, monitoring_active):
        if monitoring_active:
            self.status_icon_label.configure(image=self.working_icon)
        elif dglab_connected:
            self.status_icon_label.configure(image=self.stoping_icon)
        else:
            self.status_icon_label.configure(image=self.waiting_icon)
          
    def display_qr_code(self, url):
        self.qr_url = url
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").resize((500, 500))
            self.qr_photo = ImageTk.PhotoImage(img)
            self.add_log_entry("二维码已生成。点击左上角图标查看。")
        except Exception as e:
            self.add_log_entry(f"错误: 生成二维码失败 - {e}")

    def add_log_entry(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{timestamp}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def show_message(self, title, message):
        # This can be replaced with a custom Toplevel dialog for better styling
        from tkinter import messagebox
        messagebox.showinfo(title, message, parent=self.root)

    def _save_current_settings_to_file(self):
        """将当前UI设置保存到settings文件夹下的JSON文件，用于调试。"""
        import json
        import os
        import datetime

        settings_data = self.get_current_settings()
        
        # 确保 settings 文件夹存在
        settings_dir = os.path.join(os.path.dirname(__file__), "settings")
        os.makedirs(settings_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debug_settings_{timestamp}.json"
        filepath = os.path.join(settings_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=4)
            self.add_log_entry(f"当前设置已保存到: {filepath}")
            self.show_message("设置已保存", f"当前UI设置已成功保存到:\n{filename}")
        except Exception as e:
            self.add_log_entry(f"错误: 保存设置文件失败 - {e}")
            self.show_message("保存错误", f"保存当前设置时发生错误:\n{e}")
    # --- Private UI Actions ---
    def _open_qr_window(self):
        if not self.qr_photo:
            self.add_log_entry("警告: 二维码尚未准备好。")
            return

        qr_window = ctk.CTkToplevel(self.root)
        qr_window.title("DG-Lab QR Code")
        qr_window.geometry("300x300")
        qr_window.resizable(False, False)
        qr_window.transient(self.root)
        qr_window.grab_set()

        label = ctk.CTkLabel(qr_window, image=self.qr_photo, text="")
        label.pack(expand=True, fill="both", padx=20, pady=20)

    def _save_log(self):
        content = self.log_box.get("1.0", "end-1c")
        if not content:
            self.add_log_entry("日志为空，无需保存。")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Log File"
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.add_log_entry(f"日志已保存到: {filepath}")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.add_log_entry("日志已清除。")

    def on_closing(self):
        self.controller.shutdown()
        self.root.destroy()