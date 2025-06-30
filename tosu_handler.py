# tosu_handler.py

import websocket
import json
import threading
import config

class TOSUHandler:
    def __init__(self, data_callback, status_callback):
        self.ws = None
        self.thread = None
        self.is_connected = False
        self._is_closing = False
        self.on_data = data_callback
        self.on_status_change = status_callback

    def connect(self):
        if self.is_connected:
            return
        self._is_closing = False
        self.on_status_change("connecting")
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        self.ws = websocket.WebSocketApp(config.TOSU_WS_URL,
                                         on_open=self._on_open,
                                         on_message=self._on_message,
                                         on_error=self._on_error,
                                         on_close=self._on_close)
        self.ws.run_forever(ping_interval=10, ping_timeout=5)

    def _on_open(self, ws):
        self.is_connected = True
        self.on_status_change("connected")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.on_data(data)
        except json.JSONDecodeError:
            pass # Ignore non-JSON messages
        except Exception as e:
            print(f"Error processing TOSU message: {e}")

    def _on_error(self, ws, error):
        print(f"TOSU WebSocket error: {error}")
        # on_close will handle the state change
    
    def _on_close(self, ws, close_status_code, close_msg):
        if self._is_closing:
            return
        self.is_connected = False
        self.on_status_change("disconnected")

    def disconnect(self):
        self._is_closing = True
        if self.ws:
            self.ws.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.is_connected = False