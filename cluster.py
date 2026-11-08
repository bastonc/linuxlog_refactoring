import re
import socket
from threading import Lock

from PyQt6.QtCore import QThread, pyqtSignal


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SPOT_TIME_RE = re.compile(r"\b\d{4}Z\b", re.IGNORECASE)


def _clean_cluster_line(raw_line):
    """Remove ANSI/control characters and surrounding whitespace."""
    line = ANSI_ESCAPE_RE.sub("", raw_line)
    line = CONTROL_CHAR_RE.sub("", line)
    return line.strip()


def _is_spot_line(line):
    """Return True for DX spot lines, including ones with a trailing comment."""
    upper = line.upper()
    if not upper.startswith("DX"):
        return False
    return upper.startswith("DX DE ") or bool(SPOT_TIME_RE.search(upper))


class ClusterThread(QThread):
    reciev_spot_signal = pyqtSignal(object)
    reciev_string_signal = pyqtSignal(object)
    connected_signal = pyqtSignal()
    disconnected_signal = pyqtSignal()
    bell_bell_signal = pyqtSignal(object)

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
        self.cluster_connect_flag = False
        connection.settimeout(1)

        # Send the callsign right away.  Some clusters prompt for it, others
        # accept it as the first command; both variants work this way.
        connection.sendall((self.call + "\n").encode("ascii", errors="ignore"))
        self.cluster_connect_flag = True
        self.connected_signal.emit()

        while not self._stop_requested:
            try:
                received = connection.recv(4096)
            except socket.timeout:
                continue
            if not received:
                raise ConnectionError("Telnet server closed the connection")

            buffer += received.decode(self.settings_dict['encodeStandart'], errors="ignore")
            lines = buffer.split("\n")
            buffer = lines.pop()
            for raw_line in lines:
                # A trailing BEL is used by some clusters to mark a needed
                # spot; keep the line itself free of control characters.
                beep = "\x07" in raw_line
                line = _clean_cluster_line(raw_line)
                if not line:
                    continue
                if _is_spot_line(line):
                    self.reciev_spot_signal.emit(line)
                    if beep:
                        self.bell_bell_signal.emit(line)
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
            except Exception:
                # Sleep/wake, network changes and broken sockets must not kill
                # the worker thread permanently; report and retry instead.
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
