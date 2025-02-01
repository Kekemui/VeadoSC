from loguru import logger as log
from time import sleep

from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosed
from websockets.sync import client
import threading

from .messages import Request, response_factory, SubscribeStateEventsRequest
from .utils import Subject


class VeadoController(Subject):
    def __init__(self, plugin_base):
        super().__init__()
        self.frontend = plugin_base
        self.ws = None

        self.start_ws_thread()

    def start_ws_thread(self):
        self.listening = True
        self.thread = threading.Thread(
            target=self.ws_thread, name="gg_kekemui_veadosc_wst", daemon=True
        )
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

                self.send_request(SubscribeStateEventsRequest())

                for message in self.ws:
                    self.on_recv(message)
            except (InvalidURI, InvalidHandshake, OSError, TimeoutError):
                log.info("Unable to connect")
                sleep(10)
            except ConnectionClosed:
                log.info("Websocket closed")
            self.ws = None

    def on_recv(self, message):
        event = response_factory(message)
        log.info(f"Received event {type(event)}")
        if event:
            self.notify(event=event)

    # Untested / unexercised
    def restart(self):
        self.listening = False
        if self.ws:
            self.ws.close()
        self.thread.join()
        self.start_ws_thread()

    def send_request(self, request: Request):
        if not self.ws:
            log.info("Received request to publish with no active connection, ignoring")
            return
        reqstr = request.to_request_string()
        self.ws.send(reqstr)
