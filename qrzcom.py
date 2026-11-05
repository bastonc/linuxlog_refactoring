import xml.dom.minidom
from xml.parsers.expat import ExpatError
from threading import Event
from urllib.parse import quote

import requests
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

import std


class RequestToServer(QObject):
    answer_data = pyqtSignal(object)
    key_data = pyqtSignal(object)
    error_connection = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.url = None
        self.signal = None
        self.stop_flag = False

    def stop(self):
        self.stop_flag = True

    def set_attributes(self, url, signal, post_data=None):
        self.url = url
        self.signal = signal
        self.post_data = post_data or {}

    def get_to_server(self):
        try:
            answer = requests.get(self.url, timeout=30)
            if answer.status_code == 200:
                if self.signal == "callsign_info":
                    self.answer_data.emit(answer)
                elif self.signal == "key":
                    self.key_data.emit(answer)
            else:
                self.error_connection.emit("Error connection to qrz.com")
        except requests.RequestException:
            self.error_connection.emit("Error connection to qrz.com")
        finally:
            self.stop_flag = True
            self.deleteLater()

    def post_to_server(self):
        try:
            answer = requests.post(self.url, data=self.post_data, timeout=30)
            if answer.status_code == 200:
                self.answer_data.emit(answer)
            else:
                self.error_connection.emit(answer)
        except requests.RequestException:
            self.error_connection.emit("Error connection")
        finally:
            QThread.currentThread().quit()


class QrzComApiThread(QThread):

    data_reciev_signal = pyqtSignal(object)
    answer_data = pyqtSignal(object)
    key_data = pyqtSignal(object)
    error_connection = pyqtSignal(object)

    def __init__(self, username, password, parent=None):
        super().__init__(parent)
        self.username = username
        self.password = password
        self.qrz_key = None
        self.callsign = None
        self.cache_callsign = None
        self.url = None
        self.signal = None
        self.post_data = None
        self._request_callsign = None
        self.run_signal = True
        self._stop_event = Event()
        #self.worker_class = RequestToServer()

    def get_to_server(self):
        try:
            answer = requests.get(self.url, timeout=30)
            if answer.status_code == 200:
                if self.signal == "callsign_info":
                    self.cache_callsign = self._request_callsign
                    self.answer_data.emit(answer)
                elif self.signal == "key":
                    self.key_data.emit(answer)
                return True
            else:
                self.error_connection.emit("Not 200 (HTTPS) from qrz.com")
                return False
        except requests.RequestException:
            #self.set_run_signal(False)
            self.error_connection.emit("Network error to qrz.com")
            return False
        #finally:
            #self.stop_flag = True
            #self.deleteLater()
    def get_actual_key(self):
        username = quote(self.username, safe="")
        password = quote(self.password, safe="")
        url = f"https://xmldata.qrz.com/xml/?username={username};password={password};agent=Linuxlog"
        self.set_attrubute(url, "key")
        self.get_to_server()

    def set_attrubute(self, url: str, signal: str, post_data=None):
        self.url = url
        self.signal = signal
        self.post_data = post_data or {}

    def get_callsign_info(self, callsign):
        callsign = str(callsign)
        if self.qrz_key is not None:
            key = quote(str(self.qrz_key), safe="")
            self._request_callsign = callsign
            encoded_callsign = quote(callsign, safe="")
            url = f"https://xmldata.qrz.com/xml/current/?s={key};callsign={encoded_callsign}"
            self.set_attrubute(url, "callsign_info")
            self.get_to_server()
        else:
            print("qrz.com key is None")

    def get_callsign_info_auto(self, callsign):
        self.callsign = callsign
    def set_run_signal(self, run_signal: bool):
        self.run_signal = run_signal
        if not run_signal:
            self._stop_event.set()

    def set_key(self, key):
        self.qrz_key = key
    def run(self):
        while self.run_signal and not self._stop_event.is_set():
            if self.qrz_key is None:
                self.get_actual_key()
                if self.qrz_key is None:
                    if self._stop_event.wait(2):
                        break
                    continue
            if self.callsign and self.callsign != self.cache_callsign:
                self.get_callsign_info(self.callsign)
                if self.callsign != self.cache_callsign and self._stop_event.wait(2):
                    break
            else:
                self._stop_event.wait(0.1)


class QrzComApi(QObject):
    data_info = pyqtSignal(object)
    qrz_com_error = pyqtSignal(object)
    qrz_com_connect = pyqtSignal(bool)

    def __init__(self, username: str, password: str, parent=None):
        print(f"Starting qrz.com connecting")
        super().__init__(parent)
        self.username = username
        self.password = password
        self.qrz_com_thread = QrzComApiThread(self.username, self.password, parent=self)
        self.qrz_com_thread.answer_data.connect(self.reciever_data)
        self.qrz_com_thread.key_data.connect(self.set_key)
        self.qrz_com_thread.error_connection.connect(self.error_connection)
        self.qrz_com_thread.start()

    def get_callsign_info(self, callsign):
        self.qrz_com_thread.get_callsign_info_auto(callsign)

    def stop_thread(self):
        self.qrz_com_thread.set_run_signal(False)
        if self.qrz_com_thread.isRunning():
            return self.qrz_com_thread.wait(8500)
        return True

    @pyqtSlot(object)
    def reciever_data(self, data):
        self.worker_thread = None
        result_dict = self.xml_parse_info(data.text)
        if result_dict is None:
            self.qrz_com_error.emit("Malformed response from QRZ.com")
            self.qrz_com_connect.emit(False)
        elif result_dict.get("error") == "Invalid key":
            self.qrz_com_thread.set_key(None)
            self.qrz_com_connect.emit(False)
        else:
            self.data_info.emit(result_dict)

    @pyqtSlot(object)
    def set_key(self, data):
        try:
            xml_dom = xml.dom.minidom.parseString(data.content)
            errors = xml_dom.getElementsByTagName('Error')
            keys = xml_dom.getElementsByTagName('Key')
        except (ExpatError, TypeError, ValueError, AttributeError):
            self.qrz_com_error.emit("Malformed response from QRZ.com")
            self.qrz_com_connect.emit(False)
            return

        if errors:
            self.qrz_com_thread.set_run_signal(False)
            error_text = "QRZ.com returned an error"
            if errors[0].childNodes:
                error_text = errors[0].childNodes[0].data
            std.std().message(error_text, "QRZ.COM ERROR")
        elif not keys or not keys[0].childNodes:
            self.qrz_com_error.emit("QRZ.com response did not contain an API key")
            self.qrz_com_connect.emit(False)
        else:
            self.key = keys[0].childNodes[0].data
            self.qrz_com_thread.set_key(self.key)
            self.qrz_com_connect.emit(True)

    @pyqtSlot(object)
    def error_connection(self, error_maessage):
        #self.stop_thread()
        print(f"qrz.com error: {error_maessage}")
        #self.qrz_com_thread.set_run_signal(False)
        self.qrz_com_connect.emit(False)

    @staticmethod
    def xml_parse_info(xml_string):
        try:
            xml_dom = xml.dom.minidom.parseString(xml_string)
        except (ExpatError, TypeError, ValueError):
            return None

        def tag_text(tag_name):
            elements = xml_dom.getElementsByTagName(tag_name)
            if not elements or elements[0].firstChild is None:
                return None
            return elements[0].firstChild.nodeValue

        error_text = tag_text('Error')
        if error_text is None:
            return {
                "call": tag_text('call'),
                "f_name": tag_text('fname'),
                "s_name": tag_text('name'),
                "qth": tag_text('addr2'),
                "grid": tag_text('grid'),
                "lat": tag_text('lat'),
                "lon": tag_text('lon'),
            }
        if "Timeout" in error_text or "Invalid" in error_text:
            return {"error": "Invalid key"}
        return None

class QrzLogbook(QObject):
    def __init__(self, settings_dict):
        super(QrzLogbook, self).__init__()
        self.settings_dict = settings_dict
        self.api_url_post = "https://logbook.qrz.com/api"

    def request_to_server(self, post_data):
        self.worker_thread = QThread()
        self.worker_class = RequestToServer()
        self.worker_class.set_attributes(self.api_url_post, post_data["ACTION"], post_data=post_data)
        self.worker_class.moveToThread(self.worker_thread)
        self.worker_class.answer_data.connect(self.reciever_data)
        self.worker_class.error_connection.connect(self.error_connection)
        self.worker_thread.started.connect(self.worker_class.post_to_server)
        self.worker_thread.finished.connect(self.worker_class.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def send_qso_to_logbook(self, qso_adi_string):
        post_data = {"KEY": self.settings_dict['qrz-com-app-key'],
                     "ACTION": "INSERT",
                     "ADIF": str(qso_adi_string)}
        self.request_to_server(post_data)

    @pyqtSlot(object)
    def reciever_data(self, obj):
        print(f"Reciever POST answer: {obj.text}")

    @pyqtSlot(object)
    def error_connection(self, obj):
        print(f"Reciever POST error_connection: {obj}")
