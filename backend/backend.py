from streamcontroller_plugin_tools import BackendBase

from loguru import logger as log

from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosed
from websockets.sync import client
import threading

from ..messages import Request, response_factory


class Backend(BackendBase):
    def __init__(self):
        super().__init__()
        self.callback = None

        self.start_ws_thread()

    def set_callback(self, f):
        self.callback = f

    def start_ws_thread(self):
        self.listening = True
        self.thread = threading.Thread(target=self.ws_thread)
        self.thread.start()

    def ws_thread(self):
        while self.listening:
            settings = self.frontend.get_settings()
            host = settings.get("ip", "localhost")
            port = settings.get("port", 40404)
            try:
                self.ws: client.ClientConnection = client.connect(
                    f"ws://{host}:{port}?n=gg_kekemui_veadosc"
                )

                for message in self.ws:
                    self.on_recv(message)
            except InvalidURI | InvalidHandshake | OSError | TimeoutError:
                log.info("Unable to connect")
            except ConnectionClosed:
                log.info("Websocket closed")

    def on_recv(self, message):
        event = response_factory(message)
        if event and self.callback:
            self.callback(event)
        pass

    def restart(self):
        self.listening = False
        self.thread.join()
        self.start_ws_thread()

    def send_request(self, request: Request):
        self.ws.send(request.to_request_string())


backend = Backend()
