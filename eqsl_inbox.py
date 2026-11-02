import subprocess
import sys
import time
from pathlib import Path
from time import sleep
from urllib.parse import urlencode, urljoin, urlsplit
import re

import requests
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QTableWidgetItem, QPushButton, QCheckBox, QTableWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QSize
from bs4 import BeautifulSoup

import internetworker
import main
import parse
import std



class ConnectionToEqsl(QThread):
    get_base_html = pyqtSignal(object)
    get_adi_file = pyqtSignal(object)
    get_html_img_eqsl = pyqtSignal(object)
    get_img_eqsl = pyqtSignal(object)
    outbox_adi = pyqtSignal(object)
    error_connection = pyqtSignal()

    def __init__(self, parrent_window):
        super().__init__(parrent_window)
        self.url = ""
        self.signal = ""

    def set_attribute(self, url, signal):
        self.url = url
        self.signal = signal

    def run(self):
        if self.isInterruptionRequested():
            return
        try:
            response_from_server = requests.get(self.url, timeout=30)
            if self.isInterruptionRequested():
                return
            if self.signal == "base_html":
                self.get_base_html.emit(response_from_server)
            elif self.signal == "adi_file":
                self.get_adi_file.emit(response_from_server)
            elif self.signal == "get_eqsl_html_img":
                self.get_html_img_eqsl.emit(response_from_server)
            elif self.signal == "get_img_eqsl":
                self.get_img_eqsl.emit(response_from_server)
            elif self.signal == "outbox_link":
                self.outbox_adi.emit(response_from_server)

        except requests.RequestException:
            if not self.isInterruptionRequested():
                self.error_connection.emit()


class EqslWindow(QWidget):
    def __init__(self, settings_dict, db, log_window):
        super().__init__()
        self.db = db
        self.settings_dict = settings_dict
        self.log_window = log_window
        self.adi_normalizer = parse.adi_normilzer
        self.CONFIRMED = "Confirmed"
        self.ADDED = "In log"
        self.SEND = "Sent"
        self.base_url_eqsl = "https://www.eQSL.cc"
        self.auth_parameters = {
            "UserName": self.settings_dict['eqsl_user'],
            "Password": self.settings_dict['eqsl_password'],
        }
        self.url_get_link_to_adi = f"/qslcard/DownloadInBox.cfm"
        self.upload_qsl_url = "/qslcard/DownloadADIF.cfm"
        uic.loadUi(Path(__file__).parent/"eqsl_inbox.ui", self)
        style = "background-color:" + self.settings_dict['background-color'] + "; color:" + settings_dict[
            'color'] + ";"
        self.setStyleSheet(style)
        self.setWindowTitle("eQSL Inbox")
        self.tableWidget.setFixedWidth(775)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowOpacity(float(self.settings_dict['logWindow-opacity']))
        self.setWindowIcon(QIcon('logo.png'))
        self.status_lbl.setText("")
        self.chek_btn.clicked.connect(self.get_new_eqsl)
        self.img_name = "default"
        self.path = Path(__file__).parent/"eqsl"
        self.date_chkbx.stateChanged.connect(self.state_date)
        self.date_start_lbl.hide()
        self.date_finish_lbl.hide()
        self.calendar_start.hide()
        self.calendar_start.setFixedWidth(300)
        self.calendar_finish.hide()
        self.calendar_finish.setFixedWidth(300)
        self.unconfirmed_chkbx.stateChanged.connect(self.unconfirmed_activate)
        self.confirmed_chkbx.stateChanged.connect(self.confirmed_activate)
        self.upload_chkbx.stateChanged.connect(self.upload_activate)
        self.date_start = None
        self.date_finish = None
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self.add_to_log_action)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.confirm_action)
        self.all_confirm = True
        self.all_add = True
        self.all_qso_list = []
        self._connection_threads = []
        self._closing = False
        self.close_btn.clicked.connect(self.close)
        self.show()

    def connection_to_eqsl_thread(self, url, signal="base_html"):
        """
        Method for start new thread where connecting to eqsl server
        :param url:
        :param signal:
        :return:
        """
        if self._closing:
            return
        worker = ConnectionToEqsl(self)
        worker.set_attribute(url=url, signal=signal)
        worker.get_base_html.connect(self.processing_answer_eqsl)
        worker.get_adi_file.connect(self.processing_adi_file)
        worker.get_html_img_eqsl.connect(self.processing_html_img_eqsl)
        worker.get_img_eqsl.connect(self.processing_img_eqsl)
        worker.outbox_adi.connect(self.processing_link_outbox_adi)
        worker.error_connection.connect(self.error_connection_processing)
        worker.finished.connect(lambda worker=worker: self._connection_finished(worker))
        worker.finished.connect(worker.deleteLater)
        self._connection_threads.append(worker)
        worker.start()

    def _connection_finished(self, worker):
        if worker in self._connection_threads:
            self._connection_threads.remove(worker)
        if self._closing and not any(thread.isRunning() for thread in self._connection_threads):
            self.close()

    def prepare_close(self):
        self._closing = True
        active_threads = [thread for thread in self._connection_threads if thread.isRunning()]
        for thread in active_threads:
            thread.requestInterruption()
        return not active_threads

    def closeEvent(self, event):
        if not self.prepare_close():
            event.ignore()
            return
        event.accept()

    def eqsl_url(self, path, parameters=None):
        query = dict(self.auth_parameters)
        if parameters:
            query.update(parameters)
        return f"{self.base_url_eqsl}{path}?{urlencode(query)}"

    # Slot for processing html with links to ADI file
    @pyqtSlot(object)
    def processing_answer_eqsl(self, answer_from_eqsl):
        if self._closing:
            return
        if answer_from_eqsl.status_code == 200:
            self.status_lbl.setStyleSheet(f"color: {self.settings_dict['color']}")
            self.status_lbl.setText("Complete")
            adi_url = self.get_url_adi_file(answer_from_eqsl)
            self.connection_to_eqsl_thread(adi_url, signal="adi_file")
        else:
            self.status_lbl.setStyleSheet("color: #885555;")
            self.status_lbl.setText("Not connected")
            self.chek_btn.setEnabled(True)

    # Slot for processing link to outbox ADI
    @pyqtSlot(object)
    def processing_link_outbox_adi(self, answer_from_eqsl):
        if self._closing:
            return
        if answer_from_eqsl.status_code != 200:
            self.error_connection_processing()
            return
        self.status_lbl.setStyleSheet(f"color: {self.settings_dict['color']}")
        self.status_lbl.setText("Complete")
        self.get_url_adi_file(answer_from_eqsl)
    # Slot for processing ADI file
    @pyqtSlot(object)
    def processing_adi_file(self, answer_from_eqsl):
        if self._closing:
            return
        if answer_from_eqsl.status_code == 200:
            self.status_lbl.setStyleSheet(f"color: {self.settings_dict['color']}")
            self.status_lbl.setText("Complete")
            # self.adi_normalizer(tags=answer_from_eqsl.text,
            #                     fields_adi_standart=self.settings_dict['adi_fields'],
            #                     settings_dict=self.settings_dict)
            with (Path(__file__).parent / "eqsl_import.adi").open("w", encoding="utf-8") as f:
                f.write(answer_from_eqsl.text)
            self.output_adi_to_table(answer_from_eqsl.text)
        else:
            self.status_lbl.setStyleSheet("color: #BB4444;")
            self.status_lbl.setText("Not connected")

    # Slot fo processing html with link to image of eQSL
    @pyqtSlot(object)
    def processing_html_img_eqsl(self, response):
        if self._closing:
            return
        image_source = self.get_url_img_eqsl(response)
        if not image_source:
            self.error_connection_processing()
            return
        img_url = urljoin(self.base_url_eqsl + "/", image_source)
        parsed_url = urlsplit(img_url)
        if parsed_url.scheme != "https" or parsed_url.hostname not in {"eqsl.cc", "www.eqsl.cc"}:
            self.error_connection_processing()
            return
        self.connection_to_eqsl_thread(img_url, signal="get_img_eqsl")

    # Slot fo processing image of eQSL
    @pyqtSlot(object)
    def processing_img_eqsl(self, response):
        if self._closing:
            return
        try:
            if response.status_code != 200:
                raise OSError("Image download failed")
            image_path = (self.path / self.img_name).resolve()
            if image_path.parent != self.path.resolve():
                raise ValueError("Invalid eQSL image filename")
            image_path.write_bytes(response.content)
            self.status_lbl.setStyleSheet(f"color: {self.settings_dict['color']}")
            self.status_lbl.setText("Complete")
        except (OSError, ValueError):
            self.img_name = "default.png"
        self.show_image_eqsl(f'{self.path}/{self.img_name}')

    # slot for processing connection error
    @pyqtSlot()
    def error_connection_processing(self):
        if self._closing:
            return
        self.chek_btn.setEnabled(True)
        self.status_lbl.setStyleSheet("color: #BB4444;")
        self.status_lbl.setText("Connection error")

    def get_new_eqsl(self):
        self.chek_btn.setEnabled(False)
        self.status_lbl.setStyleSheet(f"color: {self.settings_dict['color']}")
        self.status_lbl.setText("Connecting to eQSL.cc")
        if self.unconfirmed_chkbx.isChecked():
            parameters = {"UnconfirmedOnly": "1"}
        elif self.confirmed_chkbx.isChecked():
            parameters = {"ConfirmedOnly": "1"}
        elif self.upload_chkbx.isChecked():
            parameters = {}
            path = self.upload_qsl_url
        else:
            parameters = {}
        if not self.upload_chkbx.isChecked():
            path = self.url_get_link_to_adi
        if self.date_chkbx.isChecked():
            self.date_start = self.calendar_start.selectedDate()
            self.date_finish = self.calendar_finish.selectedDate()
            # ММ/ДД/ГГГГ
            parameters["LimitDateLo"] = f"{self.date_start.month():02}/{self.date_start.day():02}/{self.date_start.year()}"
            parameters["LimitDateHi"] = f"{self.date_finish.month():02}/{self.date_finish.day():02}/{self.date_finish.year()}"
        url_eqsl = self.eqsl_url(path, parameters)
        self.connection_to_eqsl_thread(url_eqsl)

    def get_url_adi_file(self, answer_form_eqsl):
        soup = BeautifulSoup(answer_form_eqsl.text, 'html.parser')
        links = soup.findAll("a")
        for link in links:
            if str(link).find(".adi") != -1:
                return str(link["href"]).replace("../", self.base_url_eqsl + "/")

    def output_adi_to_table(self, answer_from_eqsl, mode='eqsl_server'):
        self.all_confirm_chkbox = QCheckBox("All")
        self.all_confirm_chkbox.stateChanged.connect(self.all_state_confirm)
        self.all_confirm_chkbox.setChecked(self.all_confirm)
        self.all_add_chkbox = QCheckBox("All")
        self.all_add_chkbox.stateChanged.connect(self.all_state_add)
        self.all_add_chkbox.setChecked(self.all_add)
        self.tableWidget.setRowCount(0)
        self.tableWidget.insertRow(0)
        if not self.upload_chkbx.isChecked():
            self.tableWidget.setCellWidget(0, 6, self.all_confirm_chkbox)
        self.tableWidget.setCellWidget(0, 7, self.all_add_chkbox)
        if mode == 'eqsl_server':
            self.all_confirm_chkbox.setChecked(True)
            self.all_add_chkbox.setChecked(True)
            self.all_confirm = self.get_confirm_chkbx_state()
            self.all_add = self.get_add_chkbx_state()
            strings = str(answer_from_eqsl).split("\n")
            self.all_qso_list.clear()
            for string in strings:
                qso_dict = parse.parseStringAdi(string, self.settings_dict['adi_fields'], self.settings_dict)
                if qso_dict.get("CALL"):
                    self.all_qso_list.append(qso_dict) if qso_dict is not None else None
        for row, qso in enumerate(self.all_qso_list, start=1):
            show_btn = QPushButton("Show QSL")
            show_btn.clicked.connect(lambda button_show_eqsl, qso_dict=qso: self.get_image_eqsl(qso_dict))
            add_in_base_checkbox = QCheckBox()
            add_in_base_checkbox.setChecked(self.all_add)
            confirm_checkbox = QCheckBox()
            confirm_checkbox.setChecked(self.all_confirm)
            records = self.search_in_log(qso)
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            self.tableWidget.setItem(row, 0, QTableWidgetItem(qso['QSO_DATE']))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(qso['TIME_ON']))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(qso['CALL']))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(qso['BAND']))
            self.tableWidget.setItem(row, 4, QTableWidgetItem(qso['MODE']))
            self.tableWidget.setCellWidget(row, 5, show_btn)
            if self.upload_chkbx.isChecked():
                self.tableWidget.setHorizontalHeaderItem(6, QTableWidgetItem("Sent"))
                self.tableWidget.setItem(row, 6, QTableWidgetItem(self.SEND))
                qso["EQSL_QSL_SENT"] = "Y"
            else:
                if self.confirmed_chkbx.isChecked():
                    self.tableWidget.setItem(row, 6, QTableWidgetItem(self.CONFIRMED))
                elif qso.get("EQSL_QSL_SENT") == "Y":
                    self.tableWidget.setItem(row, 6, QTableWidgetItem(self.CONFIRMED))
                elif self.unconfirmed_chkbx.isChecked():
                    self.tableWidget.setCellWidget(row, 6, confirm_checkbox)
                elif not self.confirmed_chkbx.isChecked() and \
                        not self.unconfirmed_chkbx.isChecked() and \
                        records != () and records[0]["EQSL_QSL_SENT"] == "Y":
                    self.tableWidget.setItem(row, 6, QTableWidgetItem(self.CONFIRMED))
                else:
                    self.tableWidget.setCellWidget(row, 6, confirm_checkbox)
            if records != ():
                self.tableWidget.setItem(row, 7, QTableWidgetItem(self.ADDED))
            else:
                self.tableWidget.setCellWidget(row, 7, add_in_base_checkbox)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
        self.add_btn.setEnabled(True)
        self.confirm_btn.setEnabled(True)
        self.chek_btn.setEnabled(True)

    def get_image_eqsl(self, qso: dict):
        image_name = "_".join(str(qso.get(field, "")) for field in ("CALL", "MODE", "BAND", "QSO_DATE"))
        image_name = re.sub(r"[^A-Za-z0-9_.-]", "_", image_name)[:180] + ".jpg"
        self.img_name = image_name
        image_path = self.path / image_name
        if image_path.is_file():
            self.show_image_eqsl(str(image_path))
        else:
            self.status_lbl.setStyleSheet(f"color: {self.settings_dict['color']}")
            self.status_lbl.setText("Getting eQSL from eQSL.cc")
            get_img_url = self.eqsl_url("/qslcard/GeteQSL.cfm", {
                "CallsignFrom": qso['CALL'],
                "QSOBand": qso['BAND'],
                "QSOMode": qso['MODE'],
                "QSOYear": qso['QSO_DATE'][:4],
                "QSOMonth": qso['QSO_DATE'][4:6],
                "QSODay": qso['QSO_DATE'][6:],
                "QSOHour": qso['TIME_ON'][:2],
                "QSOMinute": qso['TIME_ON'][2:],
            })
            self.connection_to_eqsl_thread(get_img_url, signal="get_eqsl_html_img")

    def get_url_img_eqsl(self, answer_form_eqsl):
        soup = BeautifulSoup(answer_form_eqsl.text, 'html.parser')
        img = soup.find("img")
        return img.get("src") if img else None

    def show_image_eqsl(self, path):
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, path])

    def check_run_thread(self):
        self.prepare_close()

    def state_date(self):
        if self.date_chkbx.isChecked():
            date_start = self.calendar_start.selectedDate()
            date_finish = self.calendar_finish.selectedDate()
            self.date_chkbx.setText(
                f"Use data:\n{date_start.month()}/{date_start.day()}/{date_start.year()} - {date_finish.month()}/{date_finish.day()}/{date_finish.year()}")
            self.calendar_start.show()
            self.calendar_finish.show()
            self.date_start_lbl.show()
            self.date_finish_lbl.show()
            self.calendar_start.selectionChanged.connect(self.set_date_event)
            self.calendar_finish.selectionChanged.connect(self.set_date_event)

        else:
            self.date_chkbx.setText("Use data")
            self.calendar_start.hide()
            self.date_start_lbl.hide()
            self.calendar_finish.hide()
            self.date_finish_lbl.hide()

    def unconfirmed_activate(self):
        if self.unconfirmed_chkbx.isChecked():
            self.confirmed_chkbx.setChecked(False)
            self.upload_chkbx.setChecked(False)

    def confirmed_activate(self):
        if self.confirmed_chkbx.isChecked():
            self.unconfirmed_chkbx.setChecked(False)
            self.upload_chkbx.setChecked(False)

    def upload_activate(self):
        if self.upload_chkbx.isChecked():
            self.confirmed_chkbx.setChecked(False)
            self.unconfirmed_chkbx.setChecked(False)


    def set_date_event(self):
        date_start = self.calendar_start.selectedDate()
        date_finish = self.calendar_finish.selectedDate()
        self.date_chkbx.setText(f"Use data:\n{date_start.month()}/{date_start.day()}/{date_start.year()} - {date_finish.month()}/{date_finish.day()}/{date_finish.year()}")

    def add_to_log_action(self):
        qso_for_add = self.get_checked_qso(index_cell=7)

        for qso in qso_for_add:
            if self.confirmed_chkbx.isChecked() or qso.get("confirmed"):
                qso["EQSL_QSL_SENT"] = "Y"
            else:
                qso["EQSL_QSL_SENT"] = "N"
            self.db.record_qso_to_base(qso_dict=qso, mode="import")
        self.output_adi_to_table(self.all_qso_list, mode='refresh')
        self.log_window.refresh_data()

    def confirm_action(self):
        self.status_lbl.setStyleSheet(f"color: {self.settings_dict['color']}")
        self.status_lbl.setText("Confirmation")
        file_name = "eqsl_c.adi"
        self.all_confirm_qso_list = self.get_checked_qso(6)
        main.Adi_file(self.settings_dict['APP_VERSION'], self.settings_dict).record_dict_qso(self.all_confirm_qso_list,
                                                                                             self.settings_dict['adi_fields'],
                                                                                             file_name)
        send_thread = internetworker.Eqsl_send_file(self, file_name, self.settings_dict)
        send_thread.eqsl_send_file_answer.connect(self.processing_row)
        send_thread.error_connection.connect(self.error_eqsl)
        send_thread.start()

    @pyqtSlot(object)
    def processing_row(self, input_object):
        """
        set checkbox confirm into "Confirmed"
        :return:
        """
        self.status_lbl.setStyleSheet(f"color: {self.settings_dict['color']}")
        self.status_lbl.setText("Complited")
        for qso in self.all_qso_list:
            for qso_confirmed in self.all_confirm_qso_list:
                if qso == qso_confirmed:
                    qso["EQSL_QSL_SENT"] = "Y"
                    record_qso = self.search_in_log(qso)
                    if record_qso != ():
                        qso["TIME_ON"] = std.std().adi_time_add_seconds(qso["TIME_ON"])
                        qso["QSO_DATE"] = std.std().adi_date_to_std_date(qso["QSO_DATE"])
                        self.db.edit_qso(int(record_qso[0]["id"]), qso)
                        qso["TIME_ON"] = qso["TIME_ON"][:4]
                        qso["QSO_DATE"] = qso["QSO_DATE"].replace("-", "")
        self.output_adi_to_table(self.all_qso_list, mode="refresh")
        self.log_window.refresh_data()


    @pyqtSlot(object)
    def error_eqsl(self, error_msg):
        """
        set checkbox confirm in to chekable checkbox
        :return:
        """
        self.status_lbl.setStyleSheet("color: #BB4444;")
        self.status_lbl.setText(error_msg)

    def get_checked_qso(self, index_cell):
        """
        Method return list with all full data qso who checked in QTableWidget
        :param index_cell: num of collumn with checkbox
        :return: list with checked qso
        """
        all_qso = []
        for row in range(1, self.tableWidget.rowCount()):
            add_ckbx = self.tableWidget.cellWidget(row, index_cell)
            if add_ckbx is not None and add_ckbx.isChecked():
                for qso in self.all_qso_list:
                    if qso["CALL"] == self.tableWidget.item(row, 2).text() and \
                        qso["QSO_DATE"] == self.tableWidget.item(row, 0).text() and \
                        qso["MODE"] == self.tableWidget.item(row, 4).text() and \
                        qso["BAND"] == self.tableWidget.item(row, 3).text() and \
                        qso["TIME_ON"] == self.tableWidget.item(row, 1).text():
                        if self.tableWidget.cellWidget(row, 6) is None:
                            qso["confirmed"] = True
                        else:
                            qso["confirmed"] = False
                        if self.tableWidget.cellWidget(row, 7) is None:
                            qso["added"] = True
                        else:
                            qso["added"] = False
                        qso["OPERATOR"] = self.settings_dict["my-call"]
                        all_qso.append(qso)
        return all_qso

    def all_state_confirm(self):
        if self.all_confirm_chkbox.isChecked():
            self.all_confirm = True
            self.all_set_checked(6)
        else:
            self.all_confirm = False
            self.all_set_unchecked(6)

    def all_state_add(self):
        if self.all_add_chkbox.isChecked():
            self.all_add = True
            self.all_set_checked(7)
        else:
            self.all_add = False
            self.all_set_unchecked(7)


    def all_set_checked(self, cell_index):
        for row in range(self.tableWidget.rowCount()):
            chkbx = self.tableWidget.cellWidget(row, cell_index)
            if chkbx is not None and not chkbx.isChecked():
                chkbx.setChecked(True)

    def all_set_unchecked(self, cell_index):
        for row in range(self.tableWidget.rowCount()):
            chkbx = self.tableWidget.cellWidget(row, cell_index)
            if chkbx is not None and chkbx.isChecked():
                chkbx.setChecked(False)

    def get_add_chkbx_state(self):
        if self.all_add_chkbox.isChecked():
            return True
        return False

    def get_confirm_chkbx_state(self):
        if self.all_confirm_chkbox.isChecked():
            return True
        return False

    def search_in_log(self, qso):
        date = qso['QSO_DATE'][:4] + "-" + qso['QSO_DATE'][4:6] + "-" + qso['QSO_DATE'][6:]
        if len(qso['TIME_ON']) == 4:
            time_qso = qso['TIME_ON'][:2] + ":" + qso['TIME_ON'][2:] + ":00"
        else:
            time_qso = qso['TIME_ON'][:2] + ":" + qso['TIME_ON'][2:4] + ":" + qso['TIME_ON'][4:]
        #print("date:", date)
        records = self.db.search_qso_by_full_data(call=qso['CALL'], date=date, time_qso=time_qso, band=qso['BAND'],
                                                  mode=qso['MODE'])
        return records
