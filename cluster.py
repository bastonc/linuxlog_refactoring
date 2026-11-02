import socket
from operator import truediv
from threading import Lock

from PyQt6.QtCore import QThread, pyqtSignal


class ClusterThread(QThread):
    reciev_spot_signal = pyqtSignal(object)
    reciev_string_signal = pyqtSignal(object)
    connected_signal = pyqtSignal()
    disconnected_signal = pyqtSignal()
    bell_bell_signal = pyqtSignal()

    def __init__(self, settings_dict, parent=None):
        super().__init__(parent)
        self.settings_dict = settings_dict
        self.host = settings_dict['telnet-host']
        self.port = settings_dict['telnet-port']
        self.call = settings_dict['my-call']
        self.telnet_socket = None
        self.cluster_connect_flag = False
        self._stop_requested = False
        self._socket_lock = Lock()

    def _set_socket(self, connection):
        with self._socket_lock:
            self.telnet_socket = connection

    def send_to_telnet(self, message):
        with self._socket_lock:
            connection = self.telnet_socket
            if connection is None:
                raise ConnectionError("Telnet is not connected")
            connection.sendall((str(message) + "\n").encode("ascii"))

    def get_cluster_connect_status(self):
        return self.cluster_connect_flag

    def start(self):
        self._stop_requested = False
        super().start()

    def stop(self):
        self._stop_requested = True
        with self._socket_lock:
            connection = self.telnet_socket
            self.telnet_socket = None
        if connection is not None:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                connection.close()
            except OSError:
                pass

    def _read_connection(self, connection):
        buffer = ""
        logged_in = False
        self.cluster_connect_flag = False
        connection.settimeout(1)

        while not self._stop_requested:
            try:
                received = connection.recv(4096)
            except socket.timeout:
                continue
            if not received:
                raise ConnectionError("Telnet server closed the connection")

            buffer += received.decode(self.settings_dict['encodeStandart'], errors="ignore")
            if not logged_in:
                prompt = buffer.lower()
                if "login:" in prompt or "please enter your call:" in prompt:
                    connection.sendall((self.call + "\n").encode("ascii"))
                    logged_in = True
                    self.cluster_connect_flag = True
                    self.connected_signal.emit()
            lines = buffer.split("\n")
            buffer = lines.pop()
            for raw_line in lines:
                beep = False
                if raw_line.endswith(""):
                    beep = True
                line = raw_line.rstrip("\r")
                if not line:
                    continue
                print(logged_in, bytes(raw_line))
                if logged_in and line.startswith("DX") and line.endswith("Z"):
                    self.reciev_spot_signal.emit(line)
                    if beep:
                        self.bell_bell_signal.emit()
                else:
                    self.reciev_string_signal.emit(
                        line.encode(self.settings_dict['encodeStandart'], errors="ignore")
                    )

    def run(self):
        while not self._stop_requested:
            connection = None
            try:
                connection = socket.create_connection((self.host, int(self.port)), timeout=2)
                self._set_socket(connection)
                self._read_connection(connection)
            except (OSError, ValueError, TypeError, ConnectionError):
                if not self._stop_requested:
                    self.disconnected_signal.emit()
            finally:
                self.cluster_connect_flag = False
                if connection is not None:
                    self._set_socket(None)
                    try:
                        connection.close()
                    except OSError:
                        pass
            if not self._stop_requested:
                self.msleep(2000)
