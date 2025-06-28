# dglab_handler.py

import asyncio
import threading
from pydglab_ws.server import DGLabWSServer
from pydglab_ws import Channel, RetCode
import config

class DGLabHandler:
    def __init__(self, status_callback, qr_callback):
        self.loop = None
        self.server_thread = None
        self.client = None
        self.is_connected = False
        self.on_status_change = status_callback
        self.on_qr_generated = qr_callback

    def start(self, ip_address):
        if self.server_thread and self.server_thread.is_alive():
            print("DG-Lab server thread is already running.")
            return

        self.loop = asyncio.new_event_loop()
        self.server_thread = threading.Thread(
            target=self._run_server, args=(ip_address,), daemon=True
        )
        self.server_thread.start()

    def _run_server(self, ip_address):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._main_server(ip_address))
        except Exception as e:
            print(f"DG-Lab server loop encountered an error: {e}")
        finally:
            self.loop.close()

    async def _main_server(self, ip_address):
        ws_url = f"ws://{ip_address}:{config.DGLAB_SERVER_PORT}"
        self.on_status_change("starting", f"启动服务器 ({ip_address})...")
        
        try:
            async with DGLabWSServer(config.DGLAB_SERVER_IP, config.DGLAB_SERVER_PORT, 60) as server:
                self.client = server.new_local_client()
                qr_url = self.client.get_qrcode(ws_url)
                self.on_qr_generated(qr_url)
                self.on_status_change("waiting", "等待 DG-Lab 连接...")

                await self.client.bind()
                self.is_connected = True
                self.on_status_change("connected", f"已连接设备")

                async for data in self.client.data_generator():
                    if data == RetCode.CLIENT_DISCONNECTED:
                        self.is_connected = False
                        self.on_status_change("disconnected", "DG-Lab 已断开")
                        await self.client.bind()
                        self.is_connected = True
                        self.on_status_change("connected", f"已重连设备")
                    else:
                        print(f"收到设备数据：{data}")

        except OSError as e:
            self.on_status_change("error", f"服务器启动失败: {e}")
        except Exception as e:
            self.on_status_change("error", f"服务器错误: {e}")
        finally:
            self.is_connected = False
            self.on_status_change("stopped", "DG-Lab 服务器已停止")

    def send_pulses(self, channel_str, waveform_name):
        if not self.client or not self.is_connected:
            return False

        pulse_data = config.PULSE_DATA.get(waveform_name)
        if not pulse_data:
            print(f"错误: 无法找到波形 '{waveform_name}'")
            return False

        channel = Channel.A if channel_str.upper() == 'A' else Channel.B
        
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.client.add_pulses(channel, *pulse_data), self.loop
            )
            # We can optionally wait for the result, but for triggers it's better to be non-blocking
            # future.result(timeout=1.0) 
            return True
        except Exception as e:
            print(f"发送波形到 DG-Lab 失败: {e}")
            return False

    def stop(self):
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2.0)