# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

from pathlib import Path
import re
from urllib.parse import quote, urlencode, urljoin, urlsplit
from urllib.request import urlopen

import std
import config_store
import requests
import datetime

import shutil
import os
import subprocess
import tarfile
import tempfile
import logging
from os.path import expanduser
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import QThread
from PyQt6 import QtCore
import PyQt6.QtCore

from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QApplication
import main


UPDATE_REPOSITORY_HOST = "github.com"
UPDATE_REPOSITORY_PATH = "/bastonc/LinLog-unstable.git"
logger = logging.getLogger(__name__)


class internetWorker(QThread):
    image_ready = QtCore.pyqtSignal(str)

    def __init__(self, window, settings, parrent=None):
        super().__init__()
        self.internet_search_window = window
        self.image_ready.connect(window.set_image_path)
        self.callsign = None
        self.settings = settings

    def set_callsign_for_search(self, callsign):
        self.callsign = callsign

    def run(self):
        info_from_internet_array = self.get_image_from_server()
        image_path = info_from_internet_array.get('img')
        if image_path:
            self.image_ready.emit(image_path)

    def get_image_from_server(self):
        '''
        метод загружает изображение с qrz.com
        принимает self.callsign - как позывной
        '''
        url_found = self.settings['qrz-com']

        # print(self.callsign)
        parameter_to_byte = urlencode({
            "tquery": self.callsign or "",
            "mode": "callsign",
        }).encode("utf-8")
        data_dictionary = {}
        try:
            with urlopen(url_found, data=parameter_to_byte, timeout=20) as response:
                html = response.read().decode("utf-8", errors="replace")
            soup = BeautifulSoup(html, 'html.parser')
            img = soup.find(id="mypic")
            file_name = (self.callsign or "unknown").replace("/", "_").replace("\\", "_")
            if not img or not img.get('src'):
                img = None
            elif img['src'].split('/')[-1] == self.settings['qrz-none']:
                img = None
        except Exception:
            logger.debug("QRZ image lookup failed; trying the fallback service", exc_info=True)
            img = None

        try:
            if img:
                image_url = urljoin(url_found, img['src'])
                if urlsplit(image_url).scheme not in {"http", "https"}:
                    raise ValueError("Unsupported image URL scheme")
                with urlopen(image_url, timeout=20) as response:
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > 20 * 1024 * 1024:
                        raise ValueError("Image exceeds 20 MiB limit")
                    image_data = response.read(20 * 1024 * 1024 + 1)
                if len(image_data) > 20 * 1024 * 1024:
                    raise ValueError("Image exceeds 20 MiB limit")
                image_path = Path(__file__).parent / "image" / f"{file_name}.jpg"
                image_path.write_bytes(image_data)
                data_dictionary.update({'img': str(image_path)})
            else:
                dict_qrz_ru = self.search_qrz_ru()
                data_dictionary.update({'name': dict_qrz_ru['name'], 'qth': dict_qrz_ru['qth'], 'loc': dict_qrz_ru['loc']})

        # print(data_dictionary)
        except Exception:
            logger.warning("Unable to retrieve callsign information from QRZ services", exc_info=True)

        return data_dictionary

    def get_id_qrz_ru(self):
        login_data = urlencode({
            "u": "<username>",
            "p": "<password>",
            "agent": "LinuxLog",
        }).encode("utf-8")
        with urlopen("http://api.qrz.ru/login", data=login_data, timeout=20) as response:
            print("QRZ_RU status:", response.status)
            html = response.read().decode("utf-8", errors="replace")
        "http: // api.qrz.ru / login?u = < username > & p = < password > & agent = < agent >"
        soup = BeautifulSoup(html, 'xml')
        id_qrz = soup.session_id
        return id_qrz

    def search_qrz_ru(self):

        self.id_rqz_ru = self.get_id_qrz_ru()

        out_dict={}
        url_found_qrz_ru = self.settings['qrz-ru']
        parameter_to_byte = urlencode({
            "id": self.id_rqz_ru,
            "callsign": (self.callsign or "").replace("/", "_"),
        }).encode("utf-8")

        with urlopen(url_found_qrz_ru, data=parameter_to_byte, timeout=20) as response:
            print("QRZ_RU status:", response.status)
            html = response.read().decode("utf-8", errors="replace")
        #print("QRZ_RU html:", html)
        soup = BeautifulSoup(html, 'html.parser')
        info_block = soup.find(id="infoBlock")
        name_clear = info_block.b.text.split(" ")[0]
        print("QRZ_RU html:", name_clear)
        content_div_dirty = info_block.div.text.split(" ")
        content_div=[]
        for content_elem in content_div_dirty:
            if content_elem !='':
                content_div.append(content_elem)

        print("QRZ_RU QTH:", content_div)
        qth_clear = content_div[3].replace(',','')
        loc_clear = content_div[6].replace("#", '').replace("\n", '')
        out_dict.update({'name': name_clear, 'qth': qth_clear, 'loc': loc_clear})
        return out_dict

class Eqsl_send(QtCore.QObject):
    error_message = QtCore.pyqtSignal(str)
    sent_ok = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()

    def __init__(self, settingsDict, recordObject, std, parent_window):
        super().__init__()
        self.recordObject = recordObject
        self.settingsDict = settingsDict
        self.std = std
        self.parrent_window = parent_window

    def run(self):
        try:
            self._send_record()
        except Exception as error:
            self.error_message.emit(f"Can't send eQSL: {error}")
        finally:
            self.finished.emit()
            QtCore.QThread.currentThread().quit()

    def _send_record(self):

        api_url_eqsl = 'https://www.eQSL.cc/qslcard/importADIF.cfm'
        data_qso_string = '<BAND:' + str(len(self.recordObject['BAND'])) + '>' + str(
            self.recordObject['BAND']) + ' <CALL:' + str(len(self.recordObject['CALL'])) + '>' + str(
            self.recordObject['CALL']) + ' <MODE:' + str(len(self.recordObject['MODE'])) + '>' + str(
            self.recordObject['MODE']) + ' <QSO_DATE:' + str(len(self.recordObject['QSO_DATE'])) + '>' + str(
            self.recordObject['QSO_DATE']) + ' <RST_RCVD:' + str(len(self.recordObject['RST_RCVD'])) + '>' + str(
            self.recordObject['RST_RCVD']) + ' <RST_SENT:' + str(len(self.recordObject['RST_SENT'])) + '>' + str(
            self.recordObject['RST_SENT']) + ' <TIME_ON:' + str(len(self.recordObject['TIME_ON'])) + '>' + str(
            self.recordObject['TIME_ON']) + ' <EOR>'
        try:
            request_eqsl = requests.post(
                api_url_eqsl,
                data={
                    'EQSL_USER': self.settingsDict['eqsl_user'],
                    'EQSL_PSWD': self.settingsDict['eqsl_password'],
                },
                files={'Filename': ('qso.adi', data_qso_string.encode('utf-8'), 'text/plain')},
                timeout=30,
            )
            request_eqsl.raise_for_status()

            response_text = BeautifulSoup(request_eqsl.text, 'html.parser').get_text(' ', strip=True)
            result = re.search(r"Result:\s*(\d+)\s+out of\s+(\d+)\s+records? added", response_text, re.IGNORECASE)
            if result and result.group(1) == result.group(2) == '1':
                self.sent_ok.emit()
            elif result:
                self.error_message.emit(f"eQSL accepted {result.group(1)} of {result.group(2)} records")
            else:
                self.error_message.emit(response_text or "eQSL returned an unrecognized response")
        except requests.RequestException:
            self.error_message.emit("Can't send eQSL. Check the internet connection and try again.")


class Eqsl_services(QtCore.QObject):
    send_ok = QtCore.pyqtSignal()
    error_signal = QtCore.pyqtSignal()

    def __init__(self, settingsDict, recordObject, std, parent_window):
        super().__init__()
        self.recordObject = recordObject
        self.settingsDict = settingsDict
        self.std = std
        self.parrent_window = parent_window
        self.check_auth_data()
        self.input_form_key = 0

    def send_qso_to_qrz(self):
        """Upload this QSO using the user's QRZ Logbook application key."""
        app_key = str(self.settingsDict.get('qrz-com-app-key') or '').strip()
        if not app_key:
            self.error_signal.emit()
            return None

        adi_fields = (
            ('BAND', self.recordObject.get('BAND', '')),
            ('CALL', self.recordObject.get('CALL', '')),
            ('FREQ', main.Adi_file._format_adif_frequency(self.recordObject.get('FREQ'))),
            ('MODE', self.recordObject.get('MODE', '')),
            ('QSO_DATE', self.recordObject.get('QSO_DATE', '')),
            ('TIME_ON', self.recordObject.get('TIME_ON', '')),
            ('RST_RCVD', self.recordObject.get('RST_RCVD', '')),
            ('RST_SENT', self.recordObject.get('RST_SENT', '')),
            ('OPERATOR', self.recordObject.get('OPERATOR', '')),
            ('NAME', self.recordObject.get('NAME', '')),
            ('QTH', self.recordObject.get('QTH', '')),
            ('COMMENTS', self.recordObject.get('COMMENT', self.recordObject.get('COMMENTS', ''))),
            ('TIME_OFF', self.recordObject.get('TIME_OFF', '')),
        )
        adif_record = ''.join(main._format_adi_field(name, value) for name, value in adi_fields) + '<EOR>'
        try:
            response = requests.post(
                'https://logbook.qrz.com/api',
                data={'KEY': app_key, 'ACTION': 'INSERT', 'ADIF': adif_record},
                timeout=30,
            )
            response.raise_for_status()
            return response
        except requests.RequestException:
            self.error_signal.emit()
            return None

    def check_auth_data(self):
        if self.settingsDict['eqsl_user'] == '' or self.settingsDict['eqsl_password'] == '':
            self.enter_auth_data()
        else:
            self.start_sending()

    def enter_auth_data(self):
        desktop = QApplication.primaryScreen().availableGeometry()
        self.window_auth = QWidget()
        self.window_auth.setGeometry(int(desktop.width() / 2) - 100, int(desktop.height() / 2) - 50, 200, 100)
        self.window_auth.setWindowTitle("Enter eQSL auth data")
        styleform = "background :" + self.settingsDict['form-background'] + "; font-weight: bold; color:" + \
                    self.settingsDict['color-table'] + ";"

        style = "QWidget{background-color:" + self.settingsDict['background-color'] + "; color:" + self.settingsDict[
            'color'] + ";}"
        self.window_auth.setStyleSheet(style)

        # Login element
        self.login_label = QLabel("login")
        self.login_input = QLineEdit()
        self.login_input.setFixedWidth(100)
        self.login_input.setFixedHeight(30)
        self.login_input.setStyleSheet(styleform)

        login_layer = QHBoxLayout()
        login_layer.addWidget(self.login_label)
        login_layer.addWidget(self.login_input)
        # Password element
        self.password_label = QLabel("Password")
        self.password_input = QLineEdit()
        self.password_input.setFixedWidth(100)
        self.password_input.setFixedHeight(30)
        self.password_input.setStyleSheet(styleform)
        password_layer = QHBoxLayout()
        password_layer.addWidget(self.password_label)
        password_layer.addWidget(self.password_input)

        # Button elements
        ok_button = QPushButton("Ok")
        ok_button.setFixedWidth(70)
        ok_button.setFixedHeight(30)
        ok_button.setStyleSheet(style)
        ok_button.clicked.connect(self.return_data)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedWidth(70)
        cancel_button.setFixedHeight(30)
        cancel_button.setStyleSheet(style)
        cancel_button.clicked.connect(self.window_auth.close)
        buttons_layer = QHBoxLayout()
        buttons_layer.addWidget(cancel_button)
        buttons_layer.addWidget(ok_button)
        main_layout = QVBoxLayout()
        main_layout.addLayout(login_layer)
        main_layout.addLayout(password_layer)
        main_layout.addLayout(buttons_layer)
        self.window_auth.setLayout(main_layout)
        self.window_auth.show()

    def return_data(self):
        self.settingsDict['eqsl_user'] = self.login_input.text().strip()
        self.settingsDict['eqsl_password'] = self.password_input.text().strip()
        # main.Settings_file().update_file_to_disk()
        self.window_auth.close()
        self.input_form_key = 1
        self.start_sending()

    def start_sending(self):
        self.send_thread = QtCore.QThread()
        self.send_eqsl = Eqsl_send(settingsDict=self.settingsDict,
                                   recordObject=self.recordObject,
                                   std=self.std,
                                   parent_window=self.parrent_window)
        self.send_eqsl.moveToThread(self.send_thread)
        self.send_eqsl.error_message.connect(self.show_message)
        self.send_eqsl.sent_ok.connect(self.send_complited)
        self.send_eqsl.finished.connect(self.send_eqsl.deleteLater)
        self.send_thread.finished.connect(self.send_thread.deleteLater)
        self.send_thread.started.connect(self.send_eqsl.run)
        self.send_thread.start()

    @QtCore.pyqtSlot(str)
    def show_message(self, string: str):
        std.std.message(self.parrent_window, string, "<p style='color: red;'>ERROR</p>")
        if self.input_form_key == 1:
            self.settingsDict['eqsl_user'] = ''
            self.settingsDict['eqsl_password'] = ''
        self.error_signal.emit()

    @QtCore.pyqtSlot()
    def send_complited(self):
        if self.input_form_key == 1:
            main.settings_file.save_all_settings(main.settings_file, self.settingsDict)
        self.send_ok.emit()


class Eqsl_send_file(QThread):
    eqsl_send_file_answer = QtCore.pyqtSignal(object)
    error_connection = QtCore.pyqtSignal(object)
    def __init__(self, parent, file_name, settings_dict):
        super().__init__(parent)
        self.file_name = file_name
        self.settings_dict = settings_dict
        self.url_post = "https://www.eQSL.cc/qslcard/ImportADIF.cfm"

    def run(self):
        values = {'EQSL_USER': self.settings_dict['eqsl_user'],
                  'EQSL_PSWD': self.settings_dict['eqsl_password']}
        try:
            file_path = Path(__file__).parent / self.file_name
            with file_path.open('rb') as upload_file:
                answer = requests.post(
                    self.url_post,
                    files={'Filename': upload_file},
                    data=values,
                    timeout=60,
                )
            if answer.status_code == 200:
                self.eqsl_send_file_answer.emit(answer)
            else:
                self.error_connection.emit("Connection error")
        except (OSError, requests.RequestException):
            self.error_connection.emit("Network error (Exception)")


class check_update(QThread):

    def __init__(self, APP_VERSION, settingsDict, parrentWindow):
        super().__init__()
        self.version = APP_VERSION
        self.settingsDict = settingsDict
        self.parrent = parrentWindow

    def run(self):

        server_url_get = 'http://357139-vds-bastonsv.gmhost.pp.ua'
        path_directory_updater_app = "/upd/"

        action = (
            server_url_get
            + path_directory_updater_app
            + quote(str(self.version), safe="")
            + "/"
            + quote(str(self.settingsDict['my-call']), safe="")
        )
        try:
            response = requests.get(action, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            std.std.message(self.parrent, "Sorry\ntimeout server.", "UPDATER")
            self._finish_update_check()
            return

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            version_node = soup.find(id="version")
            repository_node = soup.find(id="git_path")
            if version_node is None or repository_node is None:
                std.std.message(self.parrent, "You have latest version", "UPDATER")
                self._finish_update_check()
                return
            version = version_node.get_text(strip=True)
            repository = repository_node.get_text(strip=True)
        except (ValueError, AttributeError):
            std.std.message(self.parrent, "You have latest version", "UPDATER")
            self._finish_update_check()
            return

        update_result = QMessageBox.question(
            self.parrent, "LinuxLog | Updater",
            f"Found new version {version} install it?",
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.Yes,
        )
        if update_result != QMessageBox.Yes:
            self._finish_update_check()
            return

        self.parrent.check_update.setText("Updating")
        try:
            self._install_update(repository, version)
        except (OSError, subprocess.SubprocessError, ValueError, tarfile.TarError) as error:
            std.std.message(self.parrent, f"Update failed: {error}", "UPDATER")
            self._finish_update_check()
            return

        std.std.message(self.parrent, f"Update to v.{version} completed\nPlease restart LinuxLog", "UPDATER")
        self.version = version
        self._finish_update_check()
        self.parrent.text.setText("Version:" + version + "\n\nBaston Sergey\nbastonsv@gmail.com")

    def _finish_update_check(self):
        self.parrent.check_update.setText("> Check update <")
        self.parrent.check_update.setEnabled(True)

    def _install_update(self, repository, version):
        """Prepare an update beside the installation, then swap it in atomically."""
        home = Path(expanduser("~"))
        install_dir = home / "linlog"
        backup_dir = home / "linlog-old"
        source_dir = Path.cwd()

        repository_url = urlsplit(repository.strip())
        if (
            repository_url.scheme != "https"
            or repository_url.netloc.lower() != UPDATE_REPOSITORY_HOST
            or repository_url.path.rstrip("/") != UPDATE_REPOSITORY_PATH
            or repository_url.query
            or repository_url.fragment
        ):
            raise ValueError("Updater must use the official LinuxLog HTTPS repository")
        with tempfile.TemporaryDirectory(prefix=".linuxlog-update-", dir=home) as temp_name:
            temp_dir = Path(temp_name)
            staging_dir = temp_dir / "staging"
            settings_backup = temp_dir / "user-files"
            settings_backup.mkdir()
            for pattern in ("*.adi", "*.rules"):
                for source in source_dir.glob(pattern):
                    if source.is_file():
                        shutil.copy2(source, settings_backup / source.name)
            current_settings = source_dir / "settings.cfg"
            if current_settings.is_file():
                shutil.copy2(current_settings, settings_backup / current_settings.name)

            if install_dir.is_dir():
                backup_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                safe_version = "".join(char for char in version if char.isalnum() or char in "._-")
                archive = backup_dir / f"linlog-{safe_version}-{timestamp}.tar.gz"
                with tarfile.open(archive, "w:gz") as tar:
                    tar.add(install_dir, arcname=install_dir.name)

            subprocess.run(["git", "clone", "--", repository, str(staging_dir)], check=True, timeout=300)
            for pattern in ("*.adi", "*.rules"):
                for source in settings_backup.glob(pattern):
                    shutil.copy2(source, staging_dir / source.name)
            self._merge_settings(staging_dir / "settings.cfg")

            previous_dir = home / f".linlog-previous-{os.getpid()}"
            if previous_dir.exists():
                raise FileExistsError(f"Previous update directory already exists: {previous_dir}")
            if install_dir.exists():
                install_dir.rename(previous_dir)
            try:
                staging_dir.rename(install_dir)
            except OSError:
                if previous_dir.exists() and not install_dir.exists():
                    previous_dir.rename(install_dir)
                raise
            if previous_dir.exists():
                shutil.rmtree(previous_dir)

    def _merge_settings(self, settings_path):
        if not settings_path.is_file():
            return
        config_store.update_settings(self.settingsDict, path=settings_path)

class Clublog(QtCore.QObject):

    sent_qso_ok = QtCore.pyqtSignal(object)
    sent_qso_no = QtCore.pyqtSignal(object)
    del_qso_ok = QtCore.pyqtSignal(object)
    del_qso_no = QtCore.pyqtSignal(object)
    delete_requested = QtCore.pyqtSignal(object)
    export_requested = QtCore.pyqtSignal(str)
    export_completed = QtCore.pyqtSignal(object)
    network_error = QtCore.pyqtSignal()
    operation_error = QtCore.pyqtSignal(str)
    operation_finished = QtCore.pyqtSignal()

    def __init__(self, settingsDict, adi_string=None):
        super().__init__()
        self.key = "1262ee63ad3b25917b695cb78b3d3bdcfd8e2ff8"
        self.adi_string = adi_string
        #self.data = data_for_tx
        self.settingsDict = settingsDict
        self.upload_file_url = "https://clublog.org/putlogs.php"
        self.add_record_url = "https://clublog.org/realtime.php"
        self.delete_record_url = "https://clublog.org/delete.php"

    def export_file(self, file, clear=None):
        '''
         Export ADI file to Club log
         url -  https://clublog.org/putlogs.php
         method POST
         data in request:
            email: A registered email address in Club Log
            password: The password to authenticate the email login
            callsign: Optionally, the callsign into which the logs should be uploaded.
                        If not set, the primary callsign of the account is used.
            clear: If a value of 1 is given, the log will be flushed before the new upload is processed. In all other cases, including if this field is absent, the log will be merged.
            file: A multipart/form-data upload which is used to POST the ADIF file with the form. The filename should be an ADIF, LGS or a ZIP file containing one of those.
            api: An API key to access this interface (protecting it from abuse), which you can obtain by emailing the helpdesk.

        :return: result 0 - Ok, 1 - error
        '''
        multipart_data = {
            "email": self.settingsDict['email-clublog'],
            "password": self.settingsDict['pass-clublog'],
            "callsign": self.settingsDict['my-call'],
            "api": self.key,
        }
        if clear is not None:
            multipart_data["clear"] = "1"

        file_path = Path(__file__).parent / file
        with file_path.open('rb') as upload_file:
            file_data = {"file": ('log.ADI', upload_file, 'text/plain')}
            response = requests.post(
                self.upload_file_url,
                files=file_data,
                data=multipart_data,
                timeout=60,
            )
        return response

    def export_file_async(self, file):
        try:
            response = self.export_file(file)
            self.export_completed.emit(response)
        except (OSError, KeyError, requests.RequestException) as error:
            self.operation_error.emit(f"Club Log export failed: {error}")
        finally:
            self.operation_finished.emit()

    def add_record(self):
        try:
            multipart_data = {
                "email": self.settingsDict['email-clublog'],
                "password": self.settingsDict['pass-clublog'],
                "callsign": self.settingsDict['my-call'],
                "adif": self.adi_string,
                "api": self.key,
            }
            response = requests.post(self.add_record_url, data=multipart_data, timeout=30)
            if response.status_code == 200:
                self.sent_qso_ok.emit(response)
            else:
                self.sent_qso_no.emit(response)
            return response
        except requests.RequestException:
            self.network_error.emit()
            return None
        except (KeyError, TypeError, ValueError):
            self.operation_error.emit("QSO data is incomplete or invalid for Club Log upload")
            return None
        finally:
            self.operation_finished.emit()

    def del_record(self, record_object):
        '''
        Delete record from club log
        :param record_object: dict - object with data about QSO
        All data in dict: records_number, QSO_DATE, TIME_ON, FREQ, CALL, MODE, RST_RCVD, RST_SENT
        NAME, QTH, OPERATOR, BAND, COMMENTS, TIME_OFF, EQSL_QSL_SENT
        :return: response from server
        '''
        try:
            date = record_object['date']
            date_formated = date[0:4] + '-' + date[4:6] + '-' + date[6:8]
            time = std.std.std_time(self, record_object['time'])
            if len(time) not in (4, 6):
                raise ValueError("QSO time is invalid")
            time_formated = time[0:2] + ':' + time[2:4] + ':' + (time[4:] or "00")
            date_time = date_formated + " " + time_formated
            multipart_data = {
                "email": self.settingsDict['email-clublog'],
                "password": self.settingsDict['pass-clublog'],
                "callsign": self.settingsDict['my-call'],
                "dxcall": record_object['call'],
                "datetime": date_time,
                "bandid": record_object['band'].replace("M", '').strip(),
                "api": self.key,
            }
            response = requests.post(self.delete_record_url, data=multipart_data, timeout=30)
            if response.status_code == 200:
                self.del_qso_ok.emit(response)
            else:
                self.del_qso_no.emit(response)
            return response
        except requests.RequestException:
            self.network_error.emit()
            return None
        except (KeyError, TypeError, ValueError):
            self.operation_error.emit("QSO data is incomplete or invalid for Club Log deletion")
            return None
        finally:
            self.operation_finished.emit()
