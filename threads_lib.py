import re
import socket
from time import sleep

from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot, QObject


class Set_connect_thread(QThread):

    connect_socket_signal = pyqtSignal(object)
    error_connect_thread_signal = pyqtSignal(object)
    error_connect_signal = pyqtSignal(object)

    def __init__(self, host, port):
        super().__init__()
        self.HOST = host
        self.PORT = port
        self.telnet_socket = None
        self.try_connect = True

    def get_status_socket(self):
        return self.telnet_socket

    def close_socket(self):
        if self.telnet_socket is not None:
            try:
                self.telnet_socket.close()
            except OSError:
                pass
            self.telnet_socket = None

    def stop_tying_connect(self):
        self.try_connect = False

    def run(self):
        while self.try_connect:
            connection = None
            try:
                print(f"Try connected to {self.HOST}:{self.PORT} id thread: {id(self)}")
                connection = socket.create_connection((self.HOST, int(self.PORT)), timeout=10)
                connection.settimeout(None)
                if not self.try_connect:
                    connection.close()
                    return
                self.telnet_socket = connection
                self.connect_socket_signal.emit(connection)
                return
            except (OSError, ValueError, TypeError):
                if connection is not None:
                    try:
                        connection.close()
                    except OSError:
                        pass
                self.error_connect_thread_signal.emit("Error")
                print(f"Except connection to {self.HOST}:{self.PORT}")
                self.msleep(2000)


class RigctlMainLoop(QThread):

    timeout_signal = pyqtSignal()
    rigctl_stop_loop_signal = pyqtSignal(object)
    frequency_signal = pyqtSignal(object)
    vfo_signal = pyqtSignal(object)
    mode_signal = pyqtSignal(object)
    ptt_signal = pyqtSignal(object)

    def __init__(self, socket: socket.socket, sleep_time, encoding):
        super().__init__()
        self.incoming_string = None
        self.freq_cache = None
        self.vfo_cache = None
        self.mode_cache = None
        self.ptt_cache = None
        self.run_flag = True
        self.restart = True
        self.sleep_time = sleep_time
        self.encoding = encoding
        self.socket = socket

    def command_transaction(self, command):
        try:
            self.socket.sendall(str(command + "\n").encode("ascii"))
            read_answer = self.socket.recv(1024)
            return bytes.decode(read_answer, self.encoding, errors="ignore").replace("\n", "")
        except (OSError, UnicodeError):
            return False


    def set_runing_flag(self, flag: bool):
        self.run_flag = flag
    def is_frequency(self, input_string):
        if input_string is not None and input_string.isdigit():
            return True

    def is_vfo(self, input_string):
        if input_string is not None and input_string in ("VFOA", "VFOB"):
            return True

    def is_mode(self, input_string):
        if input_string is not None and input_string in ("USB", "LSB", "AM", "CWR", "CW", "FM",
                                                         "PKTUSB", "PKTLSB",  "DIGI"):
            return True

    def get_frequency(self):
        freq = self.command_transaction("f")
        if not freq:
            return freq
        if self.is_frequency(freq) and freq != self.freq_cache:
            self.frequency_signal.emit(freq)
            self.freq_cache = freq

    def get_vfo(self):
        vfo = self.command_transaction("v")
        if not vfo:
            return vfo
        if self.is_vfo(vfo) and vfo != self.vfo_cache:
            self.vfo_signal.emit(vfo)
            self.vfo_cache = vfo
            return True
            # print(f"VFO: {vfo}")

    def get_mode(self):
        mode = self.command_transaction("m")
        if not mode:
            return mode
        if mode not in (None, ""):
            mode = re.sub(r"\d*", "", mode).strip()
            if self.is_mode(mode) and mode != self.mode_cache:
                self.mode_signal.emit(mode)
                self.mode_cache = mode
                # print(f"MODE: {mode}")

    def get_ptt(self):
        ptt = self.command_transaction("t")
        if not ptt:
            return ptt
        # print(f"ptt: {ptt}")
        if ptt in ("0", "1") and ptt != self.ptt_cache:
            self.ptt_signal.emit(ptt)
            self.ptt_cache = ptt
            # print(f"MODE: {mode}")


    @pyqtSlot(object)
    def rigctl_incoming_string(self, incoming_string):
        self.incoming_string = incoming_string
        # print(self.incoming_string)

    def set_restart_flag(self, stop_value: bool):
        self.restart = stop_value

    def stop_main_loop(self):
        self.set_runing_flag(False)

    def run(self):
        while self.run_flag:
            if self.get_vfo() == False:
                # print(f"If get vfo")
                break
            if self.get_frequency() == False:
                # print(f"If get freq")
                break
            if self.get_mode() == False:
                # print(f"If get mode")
                break
            if self.get_ptt() == False:
                # print(f"If get mode")
                break
            sleep(self.sleep_time)
        self.stop_main_loop()
        if self.restart:
            self.rigctl_stop_loop_signal.emit(self)

class Rigctl_thread(QThread):
    rigctl_ready_signal = pyqtSignal(object)
    def __init__(self, host, port):
        super().__init__()
        self.HOST = host
        self.PORT = port
        self.socket = None
        self.socket_connect = None
        self.repeat_connection = 20
        self.counter_repeat_connection = 0

    def get_socket_connect(self):
        self.socket_connect = Set_connect_thread(self.HOST, self.PORT)
        self.socket_connect.connect_socket_signal.connect(self.connect_ok)
        self.socket_connect.error_connect_thread_signal.connect(self.not_connect)
        if self.socket_connect.get_status_socket() is not None:
            self.socket_connect.close_socket()
        self.socket_connect.start()

    @pyqtSlot(object)
    def connect_ok(self, socket_obj: socket.socket):
        self.socket = socket_obj
        self.socket.settimeout(5)
        self.socket_connect.stop_tying_connect()
        self.rigctl_ready_signal.emit(self.socket)


    @pyqtSlot(object)
    def not_connect(self, input_string):
        self.counter_repeat_connection += 1
        self.socket_connect.close_socket()
        self.socket = None

    def socket_shutdown(self):
        if self.socket_connect is not None:
            self.socket_connect.stop_tying_connect()
            self.socket_connect.close_socket()
        if self.socket is not None:
            self.socket.close()


    def run(self):
        self.get_socket_connect()
