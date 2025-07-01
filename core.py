# core.py (修改后)

from dglab_handler import DGLabHandler
from tosu_handler import TOSUHandler
import os # 新增
import subprocess # 新增

class AppController:
    def __init__(self):
        self.ui = None
        self.dglab = DGLabHandler(self._on_dglab_status_change, self._on_dglab_qr_generated)
        self.tosu = TOSUHandler(self._on_tosu_data, self._on_tosu_status_change)
        
        # Application State
        self.is_monitoring = False
        self.prev_pp = None
        self.prev_combo = None
        self.last_reward_combo = 0
        self.last_reward_pp = 0.0
        self.processed_miss_count = 0
        
    def set_ui(self, ui_instance):
        self.ui = ui_instance

    def start_dglab(self, ip_address):
        self.dglab.start(ip_address)

    def connect_to_tosu(self):
        # 现在允许独立连接
        if not self.tosu.is_connected:
            self.tosu.connect()

    def toggle_monitoring(self):
        is_starting = not self.is_monitoring
        
        if is_starting:
            if not self.tosu.is_connected:
                self.ui.show_message("警告", "请先连接到 TOSU")
                return False
            if not self.dglab.is_connected:
                self.ui.show_message("警告", "请先确保 DG-Lab 设备已连接")
                return False

        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.prev_pp = None
            self.prev_combo = None
            self.last_reward_combo = 0
            self.last_reward_pp = 0.0
            self.processed_miss_count = 0
            self.log_event("监控已启动。")
        else:
            self.log_event("监控已停止。")
        
        self.ui.update_monitoring_status(self.is_monitoring)
        return self.is_monitoring

    def _on_dglab_status_change(self, status, message=""):
        self.log_event(f"DG-Lab: {message or status}")
        if self.ui:
            self.ui.root.after(0, self.ui.update_dglab_status, status, message)

    def _on_dglab_qr_generated(self, qr_url):
        if self.ui:
            self.ui.root.after(0, self.ui.display_qr_code, qr_url)

    def _on_tosu_status_change(self, status):
        log_message = f"TOSU: {status}"
        if status == "connected":
            log_message = "TOSU: 已连接到 gosumemory"
        elif status == "disconnected":
            log_message = "TOSU: 连接已断开"
        elif status == "connecting":
            log_message = "TOSU: 正在连接..."

        self.log_event(log_message)
        if self.ui:
            self.ui.root.after(0, self.ui.update_tosu_status, status)
        
        if status == "disconnected" and not self.tosu._is_closing:
            self.log_event("TOSU: 10秒后尝试重新连接...")
            # 尝试启动 tosu.exe
            # tosu_exe_path = os.path.join(os.path.dirname(__file__), "tosu.exe")
            # try:
            #     # 使用 Popen 实现非阻塞执行，并分离进程
            #     subprocess.Popen([tosu_exe_path], creationflags=subprocess.DETACHED_PROCESS, close_fds=True)
            #     self.log_event(f"尝试启动 {tosu_exe_path}")
            # except FileNotFoundError:
            #     self.log_event(f"错误: 找不到 {tosu_exe_path}，无法启动 tosu.exe。请确保 tosu.exe 在同一目录下。")
            # except Exception as e:
            #     self.log_event(f"启动 tosu.exe 时发生错误: {e}")

            self.ui.root.after(10000, self.tosu.connect)

    def _on_tosu_data(self, data):
        gameplay = data.get("gameplay", {})
        pp_data = gameplay.get("pp", {})
        leaderboard_data = gameplay.get("leaderboard", {})
        accuracy_str = gameplay.get("accuracy")
        current_pp_str = pp_data.get("current")
        ourplayer_data = leaderboard_data.get("ourplayer", {}) if leaderboard_data else {}
        current_combo_str = ourplayer_data.get("combo")
        current_miss_count = gameplay.get("hits", {}).get("0", 0)
        if self.ui:
            self.ui.root.after(0, self.ui.update_game_data, current_pp_str, current_combo_str, accuracy_str,str(current_miss_count))
        
        if self.is_monitoring:
            self.check_triggers(current_pp_str, current_combo_str, accuracy_str, current_miss_count)

    def check_triggers(self, pp_str, combo_str, accuracy_str=None, current_miss_count=0):
        settings = self.ui.get_current_settings()
        
        try:
            current_pp = float(pp_str) if pp_str is not None and pp_str != '' else None
            current_combo = int(combo_str) if combo_str is not None and combo_str != '' else None
            current_accuracy = float(accuracy_str) if accuracy_str is not None and accuracy_str != '' else None # Accuracy check 可按需启用
        except (ValueError, TypeError):
            return

        # --- 歌曲结束判断 (准确度为100) ---
        if current_accuracy == 100.0 and self.prev_pp is not None and self.prev_pp > 0:
            # self.log_event("检测到准确度100% (游戏结束或未开始)，跳过波形触发并重置奖励基线。")
            self.last_reward_combo = 0
            self.last_reward_pp = 0.0
            self.prev_pp = current_pp
            self.prev_combo = current_combo
            self.processed_miss_count = current_miss_count
            return

        # Miss Mode
        if settings['miss_mode_enabled']:
            miss_triggered = False
            
            # --- 优先通过 Combo 值判断 Miss，并立即发送波形 ---
            if self.prev_combo is not None and current_combo is not None:
                if self.prev_combo > 0 and current_combo == 0:
                    self.log_event(f"触发: Miss (连击归零: {self.prev_combo} -> {current_combo})")
                    miss_triggered = True
                elif current_combo < self.prev_combo and self.prev_combo > 0:       
                    self.log_event(f"触发: Miss (连击下降: {self.prev_combo} -> {current_combo})")
                    miss_triggered = True
            
            if miss_triggered:
                # 只有当 Miss 是由 Combo 触发时，才发送一次波形并更新 processed_miss_count
                miss_channels = settings.get('miss_channels', [])
                miss_waveform = settings.get('miss_waveform', '')

                if not miss_channels:
                    miss_channels = ['A', 'B']
                    self.log_event("Miss 模式通道未配置，使用默认通道: A, B。")
                if not miss_waveform:
                    miss_waveform = '呼吸'
                    self.log_event(f"Miss 模式波形未配置，使用默认波形: '{miss_waveform}'。")

                for ch in miss_channels:
                    success = self.dglab.send_pulses(ch, miss_waveform)
                    if success:
                        self.log_event(f"发送: Miss 波形 '{miss_waveform}' 到通道 {ch} (通过 Combo 触发)")
                    else:
                        self.log_event(f"发送失败: Miss 波形 '{miss_waveform}' 到通道 {ch} (通过 Combo 触发)。")
                
                # 由于 Combo 触发的 Miss 只是一个信号，这里只加1
                # 真正的 Miss 数量同步将在后续的 current_miss_count 检查中完成
                self.processed_miss_count = max(self.processed_miss_count, current_miss_count) # 确保至少更新到当前 miss 计数
            
            # --- 检查 Miss 计数是否增加，补发漏掉的波形 ---
            if current_miss_count > self.processed_miss_count:
                misses_to_send = current_miss_count - self.processed_miss_count
                self.log_event(f"触发: Miss (通过 Miss 计数补发 {misses_to_send} 个波形)")
                
                miss_channels = settings.get('miss_channels', [])
                miss_waveform = settings.get('miss_waveform', '')
                
                if not miss_channels:
                    miss_channels = ['A', 'B']
                    self.log_event("Miss 模式通道未配置，使用默认通道: A, B。")
                if not miss_waveform:
                    miss_waveform = '呼吸'
                    self.log_event(f"Miss 模式波形未配置，使用默认波形: '{miss_waveform}'。")

                for i in range(misses_to_send):
                    for ch in miss_channels:
                        success = self.dglab.send_pulses(ch, miss_waveform)
                        if success:
                            self.log_event(f"补发: Miss 波形 '{miss_waveform}' 到通道 {ch} (第 {i + 1} 个补发 Miss)")
                        else:
                            self.log_event(f"补发失败: Miss 波形 '{miss_waveform}' 到通道 {ch} (第 {i + 1} 个补发 Miss)。")
                self.processed_miss_count = current_miss_count # 更新已处理的miss数量
        # PP Mode
        if settings['pp_mode_enabled']: 
            if self.prev_pp is not None and current_pp is not None:
                pp_drop = self.prev_pp - current_pp
                if pp_drop >= settings['pp_threshold']:
                    self.log_event(f"触发: PP 减少 (下降 {pp_drop:.2f}, 阈值 {settings['pp_threshold']:.2f})")                    
                    pp_channels = settings.get('pp_channels', [])
                    pp_waveform = settings.get('pp_waveform', '')

                    if not pp_channels:
                        pp_channels = ['A', 'B']
                        self.log_event("PP 模式通道未配置，使用默认通道: A, B。")
                    if not pp_waveform:
                        pp_waveform = '呼吸'
                        self.log_event(f"PP 模式波形未配置，使用默认波形: '{pp_waveform}'。")

                    for ch in pp_channels:
                        success = self.dglab.send_pulses(ch, pp_waveform)
                        if success:
                            self.log_event(f"发送: PP 波形 '{pp_waveform}' 到通道 {ch}")
                        else:
                            self.log_event(f"发送失败: PP 波形 '{pp_waveform}' 到通道 {ch}。")
            # else:
            #     self.log_event("PP 模式：无法计算PP下降，因为上次或当前PP值无效。")   
        # reward mode       
        # Combo模式下，单独判断断连，重置奖励基线
        if settings['combo_mode_enabled'] and self.prev_combo is not None and current_combo is not None:
            if current_combo < self.prev_combo and self.prev_combo > 0:
                self.log_event(f"Combo奖励模式: 检测到断连({self.prev_combo} -> {current_combo})，重置奖励基线为阈值 {settings['combo_threshold']}")
                self.last_reward_combo = settings['combo_threshold']
        # 连击奖励优化：补发所有跨越的奖励
        if settings['combo_mode_enabled'] and current_combo is not None and current_combo > self.last_reward_combo:
            while current_combo >= self.last_reward_combo + settings['combo_threshold']:
                self.last_reward_combo += settings['combo_threshold']
                self.log_event(f"触发: 连击奖励 (连击达到 {self.last_reward_combo})")
                reward_combo_channels = settings.get('reward_combo_channels', [])
                reward_combo_waveform = settings.get('reward_combo_waveform', '')
                if not reward_combo_channels:
                    reward_combo_channels = ['A', 'B']
                    self.log_event("连击奖励模式通道未配置，使用默认通道: A, B。")
                if not reward_combo_waveform:
                    reward_combo_waveform = '呼吸' # 使用 '呼吸' 作为默认波形
                    self.log_event(f"连击奖励模式波形未配置，使用默认波形: '{reward_combo_waveform}'。")
                for ch in reward_combo_channels:
                    success = self.dglab.send_pulses(ch, reward_combo_waveform)
                    if success:
                        self.log_event(f"发送: 连击奖励波形 '{reward_combo_waveform}' 到通道 {ch}")
                    else:
                        self.log_event(f"发送失败: 连击奖励波形 '{reward_combo_waveform}' 到通道 {ch}。")
        # PP奖励优化：补发所有跨越的奖励
        if settings['pp_reward_enabled'] and current_pp is not None and current_pp > self.last_reward_pp:
            while current_pp >= self.last_reward_pp + settings['pp_increase_threshold']:
                self.last_reward_pp += settings['pp_increase_threshold']
                self.log_event(f"触发: PP 奖励 (PP 增加至 {self.last_reward_pp:.2f})")
                reward_pp_channels = settings.get('reward_pp_channels', [])
                reward_pp_waveform = settings.get('reward_pp_waveform', '')
                if not reward_pp_channels:
                    reward_pp_channels = ['A', 'B']
                    self.log_event("PP奖励模式通道未配置，使用默认通道: A, B。")
                if not reward_pp_waveform:
                    reward_pp_waveform = '呼吸' # 使用 '呼吸' 作为默认波形
                    self.log_event(f"PP奖励模式波形未配置，使用默认波形: '{reward_pp_waveform}'。")
                for ch in reward_pp_channels:
                    success = self.dglab.send_pulses(ch, reward_pp_waveform)
                    if success:
                        self.log_event(f"发送: PP 奖励波形 '{reward_pp_waveform}' 到通道 {ch}")
                    else:
                        self.log_event(f"发送失败: PP 奖励波形 '{reward_pp_waveform}' 到通道 {ch}。")

        self.prev_pp = current_pp
        self.prev_combo = current_combo

    def send_test_pulse(self, channel, waveform):
        # We need to get the right waveform depending on the channel
        # For simplicity, let's assume test buttons use a shared waveform selector
        self.log_event(f"测试: 发送波形 '{waveform}' 到通道 {channel}")
        success = self.dglab.send_pulses(channel, waveform)
        if not success:
            self.log_event(f"测试失败: 无法发送波形到通道 {channel}")

    def simulate_miss_pp_mode(self):
        """
        模拟Miss模式和PP模式的触发，发送相应的波形。
        用于测试按钮。强制启用模式并使用默认波形和通道，以便于调试。
        """
        if not self.dglab.is_connected:
            self.log_event("模拟失败: DG-Lab 设备未连接。")
            self.ui.show_message("错误", "请先确保 DG-Lab 设备已连接才能模拟。")
            return

        settings = self.ui.get_current_settings()
        
        # 强制启用Miss模式和PP模式进行模拟
        # miss_mode_enabled = settings.get('miss_mode_enabled', False) # 移除此行
        # pp_mode_enabled = settings.get('pp_mode_enabled', False) # 移除此行

        miss_channels = settings.get('miss_channels', [])
        miss_waveform = settings.get('miss_waveform', '')

        pp_channels = settings.get('pp_channels', [])
        pp_waveform = settings.get('pp_waveform', '')

        # 如果通道未配置，使用默认通道 'A' 和 'B'
        if not miss_channels:
            miss_channels = ['A', 'B']
            self.log_event("Miss 模式通道未配置，使用默认通道: A, B。")
        
        if not miss_waveform:
            miss_waveform = '呼吸' # 使用 '呼吸' 作为默认Miss波形
            self.log_event(f"Miss 模式波形未配置，使用默认波形: '{miss_waveform}'。")

        if not pp_channels:
            pp_channels = ['A', 'B']
            self.log_event("PP 模式通道未配置，使用默认通道: A, B。")

        if not pp_waveform:
            pp_waveform = '呼吸' # 使用 '呼吸' 作为默认PP波形
            self.log_event(f"PP 模式波形未配置，使用默认波形: '{pp_waveform}'。")


        self.log_event("------ 开始模拟 Miss/PP 模式触发 (强制启用) ------")

        # 始终尝试模拟Miss模式
        self.log_event(f"模拟 Miss 模式: 尝试向通道 {miss_channels} 发送波形 '{miss_waveform}'")
        try:
            for ch in miss_channels:
                success = self.dglab.send_pulses(ch, miss_waveform)
                if success:
                    self.log_event(f"模拟 Miss 模式: 成功发送波形 '{miss_waveform}' 到通道 {ch}")
                else:
                    self.log_event(f"模拟 Miss 模式: 发送波形 '{miss_waveform}' 到通道 {ch} 失败。")
        except Exception as e:
            self.log_event(f"模拟 Miss 模式时发生错误: {e}")
            self.ui.show_message("模拟错误", f"模拟 Miss 模式时发生错误: {e}")
        

        # 始终尝试模拟PP模式
        self.log_event(f"模拟 PP 模式: 尝试向通道 {pp_channels} 发送波形 '{pp_waveform}'")
        try:
            for ch in pp_channels:
                success = self.dglab.send_pulses(ch, pp_waveform)
                if success:
                    self.log_event(f"模拟 PP 模式: 成功发送波形 '{pp_waveform}' 到通道 {ch}")
                else:
                    self.log_event(f"模拟 PP 模式: 发送波形 '{pp_waveform}' 到通道 {ch} 失败。")
        except Exception as e:
            self.log_event(f"模拟 PP 模式时发生错误: {e}")
            self.ui.show_message("模拟错误", f"模拟 PP 模式时发生错误: {e}")

        self.log_event("------ 模拟 Miss/PP 模式触发结束 ------")


    def log_event(self, message):
        if self.ui:
            self.ui.root.after(0, self.ui.add_log_entry, message)

    def shutdown(self):
        self.log_event("应用正在关闭...")
        self.dglab.stop()
        self.tosu.disconnect()
