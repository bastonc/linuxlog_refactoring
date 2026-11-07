#!/usr/bin/python3
# -*- coding: utf-8 -*-
import signal
import sys
import logging



import re
import os
import datetime
import traceback
import subprocess
import tempfile
import numpy as np
import sounddevice as sd
import ext
import cat
from pathlib import  Path
import PyQt6.QtCore
from PyQt6.QtWidgets import QApplication, QInputDialog, QProgressBar, QCheckBox, QMenu, QMessageBox, \
    QWidget, \
    QMainWindow, QTableWidget, QTabWidget, QTableWidgetItem, \
    QLineEdit, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QPlainTextEdit, QFrame, \
    QDialog, QFormLayout, QDialogButtonBox
from PyQt6.QtCore import pyqtSignal, QObject, QEvent
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QAction
from PyQt6 import QtGui, QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QThread, QTimer


def SIGSEGV_signal_arises(signalNum, stack):
    logger.debug(f"{signalNum} : SIGSEGV arises")
    # Your code

signal.signal(signal.SIGSEGV, SIGSEGV_signal_arises)

import json
import requests
import pymysql
from decimal import Decimal
from urllib.parse import quote, urljoin, urlsplit

from functools import lru_cache, partial
from pymysql.cursors import DictCursor, SSDictCursor
# from gi.repository import Notify, GdkPixbuf

from time import gmtime, strftime, localtime

import internetworker
import time
import tci
import eqsl_inbox
import config_store
import std
import parse
import settings
import qth_map
from event_bus import publish, subscribe
from qth_locator import (
    distance_km,
    latlon_to_locator,
    locator_from_callsign,
    locator_to_latlon,
    normalize_locator,
)
from cluster import ClusterThread
from qrzcom import QrzLogbook, QrzComApi
from rigctl import Rigctl_sender
from threads_lib import Rigctl_thread, RigctlMainLoop


def _format_adi_field(name, value):
    value = "" if value is None else str(value)
    return f"<{name}:{len(value)}>{value}"


def _run_project_script(script_name, *arguments):
    script_path = Path(__file__).parent / script_name
    return subprocess.call(
        [sys.executable, str(script_path), *arguments],
        cwd=str(script_path.parent),
    )


# Frequencies in Hz.  Keeping the table in one place avoids several slightly
# different copies of the same band data throughout the file.
BAND_FREQUENCIES_HZ = {
    "160": 1_800_000,
    "80": 3_500_000,
    "40": 7_000_000,
    "30": 10_000_000,
    "20": 14_000_000,
    "17": 18_000_000,
    "15": 21_000_000,
    "12": 24_890_000,
    "10": 28_000_000,
    "6": 50_000_000,
    "2": 144_500_000,
    "144": 144_500_000,
}

# Maps modes reported by rigctl/TCI to the modes used by the log form.
RADIO_MODE_ALIASES = {
    "lsb": "SSB",
    "usb": "SSB",
    "am": "AM",
    "sam": "AM",
    "dsb": "DSB",
    "cw": "CW",
    "cwr": "CW",
    "nfm": "FM",
    "wfm": "FM",
    "fm": "FM",
    "digl": "DIGI",
    "digu": "DIGI",
    "drm": "DIGI",
    "wspr": "DIGI",
    "ft8": "DIGI",
    "ft4": "DIGI",
    "jt65": "DIGI",
    "jt9": "DIGI",
    "rtty": "DIGI",
    "bpsk": "DIGI",
    "pktusb": "DIGI",
    "pktlsb": "DIGI",
}

# Upper bounds (in dBm) of the S-meter steps.  A value below a bound belongs
# to that step; anything above the last bound is 9+60.
S_METER_STEPS = (
    (-115, "1"),
    (-109, "2"),
    (-103, "3"),
    (-97, "4"),
    (-91, "5"),
    (-85, "6"),
    (-79, "7"),
    (-73, "8"),
    (-68, "9"),
    (-63, "9+5"),
    (-58, "9+10"),
    (-53, "9+15"),
    (-48, "9+20"),
    (-43, "9+25"),
    (-38, "9+30"),
    (-33, "9+35"),
    (-28, "9+40"),
    (-23, "9+45"),
    (-18, "9+50"),
    (-13, "9+55"),
)

# Columns shown in the "repeats" (search) window.
SEARCH_TABLE_FIELDS = (
    ("id", "No"),
    ("QSO_DATE", "Date"),
    ("TIME_ON", "Time"),
    ("BAND", "Band"),
    ("CALL", "Call"),
    ("MODE", "Mode"),
    ("RST_RCVD", "Rstr"),
    ("RST_SENT", "Rsts"),
    ("NAME", "Name"),
    ("QTH", "Qth"),
    ("COMMENT", "Comments"),
    ("TIME_OFF", "Time_off"),
    ("EQSL_QSL_SENT", "Eqsl_sent"),
)

KEYBOARD_LAYOUT_TRANSLATION = str.maketrans({
    "Й": "Q", "Ц": "W", "У": "E", "К": "R", "Е": "T", "Н": "Y", "Г": "U",
    "Ш": "I", "Щ": "O", "З": "P", "Х": "", "Ъ": "",
    "Ф": "A", "Ы": "S", "В": "D", "А": "F", "П": "G", "Р": "H", "О": "J",
    "Л": "K", "Д": "L", "Ж": ":", "Э": "",
    "Я": "Z", "Ч": "X", "С": "C", "М": "V", "И": "B", "Т": "N", "Ь": "M",
    "Б": "", "Ю": "", ".": "/",
})

LOWERCASE_LETTER_RE = re.compile(r"[a-zа-я]")
CYRILLIC_UPPER_RE = re.compile(r"[А-Я]")
DIGITS_RE = re.compile(r"\D")


@lru_cache(maxsize=128)
def _csv_list(value):
    """Split a comma separated setting once per distinct value."""
    return tuple(part.strip() for part in str(value).split(",") if part.strip())


def format_frequency_hz(value):
    """Format a frequency in Hz as groups of three digits (14.070.000)."""
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        return ""
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    if len(head) > 3:
        head = f"{head[:-3]}.{head[-3:]}"
    return f"{head}.{tail}"


def format_table_date(value):
    """Normalize a database/ADIF date for display in the QSO table."""
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text


def format_table_time(value):
    """Normalize a database/ADIF time for display in the QSO table."""
    normalized = parse.normalize_adi_time(value)
    if not normalized:
        return ""
    return f"{normalized[:2]}:{normalized[2:4]}:{normalized[4:]}"


logger = logging.getLogger(__name__)


class SortableQTableWidgetItem(QTableWidgetItem):
    """Table item that sorts by an explicit key instead of its display text.

    The QSO table mixes numeric columns (id, frequency, time) with text
    columns, and empty cells should not break sorting.  Passing a prepared
    key keeps the sort predictable while the visible value stays unchanged.
    """

    def __init__(self, text, sort_key=None):
        super().__init__(text)
        self._sort_key = str(text).casefold() if sort_key is None else sort_key

    def __lt__(self, other):
        if isinstance(other, SortableQTableWidgetItem):
            try:
                return self._sort_key < other._sort_key
            except TypeError:
                return str(self._sort_key) < str(other._sort_key)
        return super().__lt__(other)


class Settings_file:
    def update_file_to_disk(self):
        settings = getattr(self, "settings_dict", None)
        if settings is None:
            settings = getattr(self, "settingsDict", {})
        return config_store.update_settings(settings)


class Adi_file:

    def __init__(self, app_version, settingsDict, filename='log.adi'):
        self.APP_VERSION = app_version
        self.settingsDict = settingsDict
        self.filename = filename
        try:
            with open(Path(__file__).parent / self.filename, 'r', encoding='utf-8') as file:
                self.strings_in_file = file.readlines()
        except FileNotFoundError:
            self.strings_in_file = []

    def get_last_string(self):
        return len(self.strings_in_file)

    @staticmethod
    def _line_index(row_number, line_count):
        row_text = str(row_number).strip()
        if not row_text.isdecimal():
            raise ValueError("ADIF row number must be a positive integer")
        line_index = int(row_text) - 1
        if not 0 <= line_index < line_count:
            raise IndexError("ADIF row number is outside the file")
        return line_index

    def _write_lines_atomically(self, lines):
        path = (Path(__file__).parent / self.filename).resolve(strict=True)
        file_mode = os.stat(path).st_mode & 0o777
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                file.writelines(lines)
                file.flush()
                os.fsync(file.fileno())
            os.chmod(temporary_name, file_mode)
            os.replace(temporary_name, path)
        except Exception:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise

    @staticmethod
    def rename_adi(old_name, new_name):
        os.rename(old_name, new_name)

    def store_changed_qso(self, obj):
        '''
        1. Function recived object in format (ch.1)
        2. Building string for log.adi file
        3. Read all strings
        4. ReWrite string in log.adi file
        chapter 1
        :param object: {'BAND': '40M', 'CALL': 'UR4LGA', 'FREQ': 'Freq: 7028500', 'MODE': 'ESSB',
        'OPERATOR': 'UR4LGA', 'QSO_DATE': '20191109', 'TIME_ON': '224058', 'RST_RCVD': '59',
         'RST_SENT': '59', 'NAME': '', 'QTH': '', 'COMMENTS': '', 'TIME_OFF': '224058',
         'eQSL_QSL_RCVD': 'Y', 'EOR': 'R\n',
         'string_in_file': '186', 'records_number': '89'}

        :return:
        '''

        fields = (
            "BAND", "CALL", "FREQ", "MODE", "OPERATOR", "QSO_DATE", "TIME_ON",
            "RST_RCVD", "RST_SENT", "NAME", "QTH", "COMMENTS", "TIME_OFF",
            "EQSL_QSL_SENT", "CLUBLOG_QSO_UPLOAD_STATUS",
        )
        values = {field: obj.get(field, "") for field in fields}
        values["FREQ"] = self._format_adif_frequency(values["FREQ"])
        stringToAdiFile = "".join(_format_adi_field(field, values[field]) for field in fields) + "<EOR>\n"

        line_index = self._line_index(obj['string_in_file'], len(self.strings_in_file))
        self.strings_in_file[line_index] = stringToAdiFile
        self._write_lines_atomically(self.strings_in_file)

        # logger.debug("this:", self.strings_in_file[int(object['string_in_file'])-1])

    def delete_qso_from_file(self, row_in_file):
        with open(Path(__file__).parent / self.filename, 'r', encoding='utf-8') as file:
            # file.seek(0, 2)
            lines_in_file = file.readlines()

        line_index = self._line_index(row_in_file, len(lines_in_file))
        lines_in_file[line_index] = ''
        self._write_lines_atomically(lines_in_file)

    def get_header(self):

        '''
        This function returned string with cariage return
        :return: string header with cariage return
        '''

        self.header_string = "ADIF from LinLog Light v." + self.APP_VERSION + " \n"
        self.header_string += "Copyright 2019-" + strftime("%Y", gmtime()) + "  Baston V. Sergey\n"
        self.header_string += "Header generated on " + strftime("%d/%m/%y %H:%M:%S", gmtime()) + " by " + \
                              self.settingsDict[
                                  'my-call'] + "\n"
        self.header_string += "File output restricted to QSOs by : All Operators - All Bands - All Modes \n"
        self.header_string += "<PROGRAMID:6>LinLog\n"
        self.header_string += "<PROGRAMVERSION:" + str(len(self.APP_VERSION)) + ">" + self.APP_VERSION + "\n"
        self.header_string += "<EOH>\n\n"
        return self.header_string

    def get_all_qso(self):
        return self.strings_in_file

    @staticmethod
    def band_to_freq(band):
        """Return the default frequency (Hz) for an ADIF band value."""
        band_number = DIGITS_RE.sub("", str(band or ""))
        return BAND_FREQUENCIES_HZ.get(band_number, "")

    @staticmethod
    def _format_adif_frequency(value):
        """Convert legacy Hz/kHz/MHz values into ADIF's MHz representation."""
        frequency_text = str(value or "").strip()
        if frequency_text.lower().startswith("freq:"):
            frequency_text = frequency_text.split(":", 1)[1].strip()
        frequency_text = re.sub(r"\s*hz$", "", frequency_text, flags=re.IGNORECASE).strip()
        frequency_hz = std.std().std_freq(frequency_text)
        if not frequency_hz:
            return ""
        frequency_mhz = Decimal(frequency_hz) / Decimal(1_000_000)
        formatted = format(frequency_mhz, "f")
        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")
        return formatted

    def record_dict_qso(self, list_data, fields_list, name_file='log.adi'):
        '''
        This function recieve List (list_data) with Dictionary with QSO-data
        Dictionary including all field in ADIF format:
        call
        name
        qth
        rst_send
        rst_reciev
        band
        mode
        comment
        :param list_data: List with Dictionary with QSO-data
        :return:
        '''
        with open(Path(__file__).parent/name_file, 'w', encoding='utf-8') as file:
            file.write(self.get_header())
            for qso in list_data:
                raw_time_on = qso.get('TIME_ON')
                time_on = parse.normalize_adi_time(raw_time_on)
                if not time_on:
                    # Keep the original value in diagnostic files such as
                    # bad_adi.adi so the cause of the problem is visible.
                    time_on = str(raw_time_on or '').strip().replace(":", "")

                raw_time_off = qso.get('TIME_OFF')
                time_off = parse.normalize_adi_time(raw_time_off)
                if not time_off:
                    time_off = str(raw_time_off or '').strip().replace(":", "")
                if not time_off:
                    time_off = time_on

                raw_date = qso.get('QSO_DATE')
                qso_date = parse.normalize_adi_date(raw_date)
                if not qso_date:
                    qso_date = str(raw_date or '').strip().replace("-", "")

                frequency = qso.get("FREQ")
                if frequency in (None, ""):
                    frequency = self.band_to_freq(qso.get("BAND", ""))
                frequency = self._format_adif_frequency(frequency)

                values = (
                    ("BAND", qso.get('BAND', "")),
                    ("CALL", qso.get('CALL', "")),
                    ("FREQ", frequency),
                    ("MODE", qso.get('MODE', "")),
                    ("OPERATOR", qso.get('OPERATOR', "")),
                    ("QSO_DATE", qso_date),
                    ("TIME_ON", time_on),
                    ("RST_RCVD", qso.get('RST_RCVD', "")),
                    ("RST_SENT", qso.get('RST_SENT', "")),
                    ("NAME", qso.get('NAME', "")),
                    ("QTH", qso.get('QTH', "")),
                    ("COMMENTS", qso.get('COMMENT', qso.get('COMMENTS', ""))),
                    ("TIME_OFF", time_off),
                    ("EQSL_QSL_RCVD", qso.get('EQSL_QSL_RCVD', "")),
                    ("EQSL_QSL_SENT", qso.get('EQSL_QSL_SENT', "")),
                    ("CLUBLOG_QSO_UPLOAD_STATUS", qso.get('CLUBLOG_QSO_UPLOAD_STATUS', "")),
                )
                file.write(" ".join(_format_adi_field(field, value) for field, value in values) + " <EOR>\n")


    def create_adi(self, name):
        with open(Path(__file__).parent / name, 'w', encoding='utf-8') as file:
            file.write(self.get_header())


class Filter_event_table_qso(QObject):

    def eventFilter(self, widget, event):
        if event.type() == QEvent.Type.Wheel and widget.rowCount():
            scroll_bar = widget.verticalScrollBar()
            if scroll_bar.value() >= scroll_bar.maximum():
                logWindow.append_record()
        # Let the table handle the wheel event normally.  The old version
        # consumed it, which made scrolling impossible.
        return False


class Filter(QObject):

    def __init__(self, window_internetSearch, settings_dict):
        super().__init__()
        self.internet_search = window_internetSearch
        self.settings_dict = settings_dict
        self.previous_call = None
        self.img_search = internetworker.internetWorker(window=self.internet_search,
                                                        settings=self.settings_dict)

    def eventFilter(self, widget, event):
        if event.type() == QEvent.Type.FocusOut:
            # logger.debug(f"widget {widget}")
            textCall = logForm.inputCall.text()

            if textCall != '' and textCall != self.previous_call:
                self.previous_call = textCall
                # Focus-out performs the lookup immediately; cancel a pending debounce.
                logForm._lookup_timer.stop()
                logForm._pending_lookup = ""
                foundList = db.search_qso_in_base(textCall)
                if foundList:
                    logForm.set_data_qso(foundList)
                else:
                    logForm.get_info_from_qrz(textCall)
                freq = logForm.get_freq()
                country = logForm.get_country(textCall)
                # logger.debug(country)
                if country != []:
                    logForm.set_country_label(country[0] + ' <h6 style="font-size: 10px;">ITU: ' + country[1] + '</h6>')

                if settingsDict['search-internet-window'] == 'True':

                    self.previous_call = textCall
                    self.img_search.set_callsign_for_search(textCall)
                    self.img_search.start()
                    if settingsDict['tci'] == 'enable':
                        try:
                            tci_sndr.set_spot(textCall, freq)
                        except Exception:
                            logger.debug("Filter: Can't connect to TCI-server")

            if textCall == '' or textCall == ' ':
                pixmap = QPixmap('logo.png')

            return False

        if event.type() == QEvent.Type.FocusIn:

            if logForm.inputCall.text() == '':
                if settingsDict['mode-swl'] != 'enable':
                    logForm.inputRstS.setText('59')
                    logForm.inputRstR.setText('59')
                else:
                    logForm.inputRstR.setText('SWL')
                # return False so that the widget will also handle the event
                # otherwise it won't focus out
            return False

        else:
            # we don't care about other events
            return False



class Log_Window_2(QWidget):

    def __init__(self, settings_dict=None):
        super().__init__()
        self.settings_dict = settings_dict if settings_dict is not None else globals().get("settingsDict", {})
        self.allCollumn = ['QSO_DATE', 'BAND', 'FREQ', 'CALL', 'MODE', 'RST_RCVD', 'RST_SENT', 'TIME_ON',
                           'NAME', 'QTH', 'COMMENT', 'TIME_OFF', 'EQSL_QSL_SENT', 'CLUBLOG_QSO_UPLOAD_STATUS', 'id', 'select']  #todo add field, 'select' for multi select
        self.fill_flag = 0
        self.qso_last_id = None
        self.select_id_list = []
        self._last_checkbox_row = None
        self._checkbox_bulk_updating = False
        self._clublog_workers = {}
        self._column_index = {field: index for index, field in enumerate(self.allCollumn)}
        self._table_color = QColor(self.settings_dict["color-table"])
        self._eqsl_color = QColor(self.settings_dict["eqsl-sent-color"])
        self._loaded_rows = 0
        self._oldest_loaded_id = None
        self._populating_table = False
        self._sort_column = None
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._page_size = 100
        self._select_item_style = (
            "QTableWidget::indicator"
            "{ border : 1px solid " + self.settings_dict["color-table"] + "; "
            "width: 10px;"
            "height: 10px;"
            "border-radius: 3px; }"
            "QTableWidget::indicator:checked"
            "{border: 2px solid rgb(255, 90, 90);"
            "width: 10px;"
            "height: 10px;"
            "border-radius: 5px;"
            "background-color:" + self.settings_dict["color-table"] + ";"
            "}"
        )
        self.read_base_string = ReadStringDb(db=db, parent=self)
        self.read_base_string.records_from_base.connect(self.fill_qso_table)
        self.read_base_string.fill_complite.connect(self.fill_complited)
        self.tableWidget_qso = QTableWidget()
        self.qrz_com_logbook = QrzLogbook(self.settings_dict)
        self.std_class = std.std()
        self.initUI()
        self.refresh_data()

    def initUI(self):
        '''
            Design of log window

        '''
        self.setGeometry(int(self.settings_dict['log-window-left']),
                         int(self.settings_dict['log-window-top']),
                         int(self.settings_dict['log-window-width']),
                         int(self.settings_dict['log-window-height']))

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)
        self.setWindowTitle("General log")
        self.setWindowIcon(QIcon(f'{Path(__file__).parent }/logo.png'))
        if self.settings_dict['border_wnd'] == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(float(self.settings_dict['logWindow-opacity']))
        style = "background-color:" + self.settings_dict['background-color'] + "; color:" + self.settings_dict[
            'color'] + ";"
        self.setStyleSheet(style)
        self.event_qso_table = Filter_event_table_qso()
        self.tableWidget_qso.installEventFilter(self.event_qso_table)
        self.tableWidget_qso.move(0, 0)
        self.tableWidget_qso.verticalHeader().hide()
        style_table = "background-color:" + self.settings_dict['form-background'] + "; color:" + self.settings_dict[
            'color-table'] + "; font: 12px;  gridline-color: " + self.settings_dict['solid-color'] + ";"
        self.tableWidget_qso.setStyleSheet(style_table + self._select_item_style)
        fnt = self.tableWidget_qso.font()
        fnt.setPointSize(9)
        self.tableWidget_qso.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableWidget_qso.customContextMenuRequested.connect(self.context_menu)
        self.tableWidget_qso.setFont(fnt)
        self.tableWidget_qso.setColumnCount(len(self.allCollumn))
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)
        self.tableWidget_qso.setSortingEnabled(False)
        self.tableWidget_qso.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.tableWidget_qso.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_header = self.tableWidget_qso.horizontalHeader()
        table_header.setSectionsClickable(True)
        table_header.setSortIndicatorShown(True)
        table_header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        table_header.sectionClicked.connect(self.sort_qso_table)
        self.tableWidget_qso.itemChanged.connect(self.qso_item_changed)

        # MENU LOG WINDOW Lay
        button_style = "font-size: 9px;"
        self.filter_button = QPushButton("Filter")
        self.filter_button.setStyleSheet(button_style)
        self.filter_button.setFixedWidth(50)
        self.filter_button.setFixedHeight(20)
        self.filter_button.clicked.connect(self.filter_log_pressed)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setFixedWidth(50)
        self.refresh_button.setFixedHeight(20)
        self.refresh_button.setStyleSheet(button_style)
        self.refresh_button.clicked.connect(self.refresh_data_button)

        # Multi delete button
        self.multi_delete_qso_button = QPushButton("Delete")
        self.multi_delete_qso_button.setFixedWidth(50)
        self.multi_delete_qso_button.setFixedHeight(20)
        self.multi_delete_qso_button.setStyleSheet(button_style)
        self.multi_delete_qso_button.clicked.connect(self.multi_delete_qso)

        # Multi export button
        self.multi_export_button = QPushButton("Export to ADI")
        self.multi_export_button.setFixedWidth(70)
        self.multi_export_button.setFixedHeight(20)
        self.multi_export_button.setStyleSheet(button_style)
        self.multi_export_button.clicked.connect(self.multi_export_qso)

        # Multi send eqsl button
        self.multi_send_eqsl_button = QPushButton("Send eQSL")
        self.multi_send_eqsl_button.setFixedWidth(60)
        self.multi_send_eqsl_button.setFixedHeight(20)
        self.multi_send_eqsl_button.setStyleSheet(button_style)
        self.multi_send_eqsl_button.clicked.connect(self.multi_send_eqsl)

        # Multi send to clublog button
        self.multi_send_clublog_button = QPushButton("Send to ClubLog")
        self.multi_send_clublog_button.setFixedWidth(80)
        self.multi_send_clublog_button.setFixedHeight(20)
        self.multi_send_clublog_button.setStyleSheet(button_style)
        self.multi_send_clublog_button.clicked.connect(self.multi_send_clublog)

        # Setup multi-function layer
        self.multi_lay = QHBoxLayout()
        self.multi_lay.addStretch()
        self.multi_lay.addWidget(self.multi_export_button)
        self.multi_lay.addWidget(self.multi_send_eqsl_button)
        self.multi_lay.addWidget(self.multi_send_clublog_button)
        self.multi_lay.addWidget(self.multi_delete_qso_button)
        self.multi_lay.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.multi_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        # self.multi_lay.setGeometry(QRect(0, 0, 300, 10))

        # QProgress Bar
        self.load_bar = QProgressBar()
        self.load_bar.setGeometry(30, 40, 200, 25)
        # self.load_bar.setFixedHeight(10)
        self.load_bar.setStyleSheet(style)

        # QLabel header
        self.header_label = QLabel()
        self.header_label.setFont(QtGui.QFont('SansSerif', 9))
        self.menu_log_button = QHBoxLayout()
        self.menu_log_button.addWidget(self.refresh_button)
        self.menu_log_button.addWidget(self.load_bar)
        self.multi_frame = QFrame()
        self.multi_frame.setLayout(self.multi_lay)
        self.multi_frame.setFixedHeight(30)
        self.multi_frame.hide()
        self.menu_log_button.addWidget(self.multi_frame)
        self.menu_log_button.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Set layouts
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.menu_log_button)
        self.layout.addWidget(self.tableWidget_qso)
        self.setLayout(self.layout)


    # def mouseDoubleClickEvent(self, event):
    #     self.setWindowTitle("LinuxLog")

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.RightButton:
            self.x = self.width()
            self.y = self.height()
            self.resize_wnd = event.pos()
            self.flag_button = "right"
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()
            self.flag_button = "left"

    def mouseMoveEvent(self, event):
        if self.flag_button == "left":
            x = int(event.globalPosition().x())
            y = int(event.globalPosition().y())
            x_w = self.offset.x()
            y_w = self.offset.y()
            self.move(x - x_w, y - y_w)
        if self.flag_button == "right":
            x_r = self.resize_wnd.x() - event.pos().x()
            y_r = self.resize_wnd.y() - event.pos().y()
            self.resize(self.x - x_r, self.y - y_r)

    def append_qso(self):
        self.append_record()

    @staticmethod
    def _sort_key(field, text):
        """Return a value that sorts the given QSO column naturally."""
        if field in ('id', 'FREQ'):
            digits = DIGITS_RE.sub("", text)
            return int(digits) if digits else -1
        if field in ('TIME_ON', 'TIME_OFF'):
            digits = DIGITS_RE.sub("", text)
            return int(digits) if digits else -1
        return text.casefold()

    def _make_qso_item(self, field, text):
        item = SortableQTableWidgetItem(text, self._sort_key(field, text))
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        return item

    def _populate_row(self, row, record):
        """Fill one table row from a database/ADIF record dictionary."""
        table = self.tableWidget_qso
        eqsl_sent = record.get('EQSL_QSL_SENT') == 'Y'
        for column, field in enumerate(self.allCollumn):
            if field == 'select':
                item = SortableQTableWidgetItem("", 0)
                item.setFlags(
                    Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
                item.setCheckState(Qt.CheckState.Unchecked)
                table.setItem(row, column, item)
                continue

            value = record.get(field, "")
            if field == 'QSO_DATE':
                value = format_table_date(value)
            elif field in ('TIME_ON', 'TIME_OFF'):
                value = format_table_time(value)
            elif field == 'FREQ':
                value = format_frequency_hz(value)
            elif value is None or value == "None":
                value = ""

            item = self._make_qso_item(field, str(value))
            item.setForeground(self._table_color)
            if eqsl_sent:
                item.setBackground(self._eqsl_color)
            table.setItem(row, column, item)

    @QtCore.pyqtSlot(int)
    def sort_qso_table(self, column):
        """Sort the QSO table when the user clicks a column header."""
        if column < 0 or column >= self.tableWidget_qso.columnCount():
            return
        if column == self._sort_column:
            self._sort_order = (
                Qt.SortOrder.DescendingOrder
                if self._sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._sort_column = column
            self._sort_order = Qt.SortOrder.AscendingOrder
        self.tableWidget_qso.horizontalHeader().setSortIndicator(column, self._sort_order)
        self.tableWidget_qso.sortItems(column, self._sort_order)

    @QtCore.pyqtSlot(QTableWidgetItem)
    def qso_item_changed(self, item):
        """Keep the multi-select list in sync with the select column."""
        if self._populating_table or self._checkbox_bulk_updating or item is None:
            return
        if item.column() != self._column_index['select']:
            return

        table = self.tableWidget_qso
        select_column = self._column_index['select']
        current_row = item.row()

        modifiers = QApplication.keyboardModifiers()
        shift_pressed = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if shift_pressed and self._last_checkbox_row is not None and self._last_checkbox_row != current_row:
            self._checkbox_bulk_updating = True
            try:
                state = item.checkState()
                first = min(self._last_checkbox_row, current_row)
                last = max(self._last_checkbox_row, current_row)
                for row in range(first, last + 1):
                    checkbox_item = table.item(row, select_column)
                    if checkbox_item is not None and checkbox_item.checkState() != state:
                        checkbox_item.setCheckState(state)
                self.multi_select_cheked()
                if self.select_id_list:
                    self.show_action_buttons()
                else:
                    self.hide_action_buttons()
            finally:
                self._checkbox_bulk_updating = False
            self._last_checkbox_row = current_row
            return

        id_item = table.item(current_row, self._column_index['id'])
        if id_item is None:
            return

        record_id = id_item.text()
        if item.checkState() == Qt.CheckState.Checked:
            if record_id not in self.select_id_list:
                self.select_id_list.append(record_id)
        elif record_id in self.select_id_list:
            self.select_id_list.remove(record_id)

        self._last_checkbox_row = current_row
        if self.select_id_list:
            self.show_action_buttons()
        else:
            self.hide_action_buttons()

    def append_record(self):
        """Load the next (older) page of QSOs when the user scrolls down."""
        table = self.tableWidget_qso
        if self.fill_flag or not table.rowCount():
            return
        # The load thread streams the whole table; do not request the same
        # rows again when the user scrolls to the bottom afterwards.
        total = getattr(self, "allRows", 0)
        if isinstance(total, int) and total and self._loaded_rows >= total:
            return
        if self._oldest_loaded_id is None:
            return

        page = db.getRange(self._oldest_loaded_id, self._page_size)
        if not page:
            return

        table.setUpdatesEnabled(False)
        self._populating_table = True
        try:
            first_row = table.rowCount()
            table.setRowCount(first_row + len(page))
            for offset, record in enumerate(page):
                self._populate_row(first_row + offset, record)
                self._remember_oldest_id(record)
            self._loaded_rows = first_row + len(page)
            if first_row == 0:
                table.resizeColumnsToContents()
        finally:
            self._populating_table = False
            table.setUpdatesEnabled(True)

    def refresh_data_button(self):
        # self.tableWidget_qso.clear()
        self.refresh_data()

    def filter_log_pressed(self):
        self.filter_log = ext.Filter_log(self.settings_dict)
        self.filter_log.show()

    #  logger.debug("filter_log_pressed")

    def context_menu(self, point):

        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)
        context_menu = QMenu()
        style_table = f"font-size: 12px;  color: {self.settings_dict['color']}; background: {self.settings_dict['background-color']};"
        context_menu.setStyleSheet(style_table)
        # context_menu.setFixedWidth(120)
        # context_menu.set
        if self.tableWidget_qso.itemAt(point):
            index_row = self.tableWidget_qso.currentItem().row()
            call = self.tableWidget_qso.item(index_row, self._column_index['CALL']).text()
            delete_record = QAction("Delete QSO with " + call, context_menu)
            delete_record.triggered.connect(lambda:
                                            self.delete_qso(self.tableWidget_qso.currentItem().row()))
            edit_record = QAction("Edit QSO with " + call, context_menu)
            edit_record.triggered.connect(lambda:
                                          self.edit_qso(self.tableWidget_qso.currentItem().row()))
            send_eqsl = QAction("Send eQSL for " + call, context_menu)
            send_eqsl.triggered.connect(lambda:
                                        self.send_eqsl_for_call(self.tableWidget_qso.currentItem().row()))
            if self.tableWidget_qso.item(index_row, self._column_index['EQSL_QSL_SENT']).text() == "Y":
                send_eqsl.setEnabled(False)
            else:
                send_eqsl.setEnabled(True)
            # Set add to Club log menu
            send_to_clublog = QAction("Send QSO to Club log", context_menu)
            send_to_clublog.triggered.connect(lambda:
                                              self.sent_clublog_for_call(self.tableWidget_qso.currentItem().row()))
            if self.tableWidget_qso.item(index_row, self._column_index['CLUBLOG_QSO_UPLOAD_STATUS']).text() == "Y" \
                    or self.tableWidget_qso.item(index_row,
                                                 self._column_index['CLUBLOG_QSO_UPLOAD_STATUS']).text() == "M":
                send_to_clublog.setEnabled(False)
            else:
                send_to_clublog.setEnabled(True)
            # Set Delete from Club log menu
            del_from_clublog = QAction("Delete QSO from Club log", context_menu)
            del_from_clublog.triggered.connect(lambda: self.del_from_clublog(self.tableWidget_qso.currentItem().row()))
            if self.tableWidget_qso.item(index_row, self._column_index['CLUBLOG_QSO_UPLOAD_STATUS']).text() == "Y" \
                    or self.tableWidget_qso.item(index_row,
                                                 self._column_index['CLUBLOG_QSO_UPLOAD_STATUS']).text() == "M":
                del_from_clublog.setEnabled(True)
            else:
                del_from_clublog.setEnabled(False)

            # Create menu ClubLog
            clublog_menu = QMenu("Club Log")
            clublog_menu.setStyleSheet(style_table)
            clublog_menu.addAction(send_to_clublog)
            clublog_menu.addAction(del_from_clublog)

            context_menu.addAction(edit_record)
            context_menu.addAction(send_eqsl)
            context_menu.addAction(delete_record)
            # context_menu.addAction(send_to_clublog)
            context_menu.addMenu(clublog_menu)
            context_menu.exec(self.tableWidget_qso.mapToGlobal(point))

    # logger.debug(self.tableWidget_qso.mapToGlobal(point))

    def _start_clublog_worker(self, worker, operation, payload=None):
        thread = QThread(self)
        worker.moveToThread(thread)
        worker.operation_finished.connect(thread.quit)
        worker.operation_finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._clublog_workers[thread] = worker
        thread.finished.connect(lambda thread=thread: self._clublog_workers.pop(thread, None))

        if payload is None:
            thread.started.connect(getattr(worker, operation))
        else:
            worker.delete_requested.connect(worker.del_record)
            thread.started.connect(
                lambda worker=worker, payload=payload: worker.delete_requested.emit(payload)
            )
        thread.start()
        return thread

    def _find_qso_row(self, record_id):
        id_column = self._column_index.get('id')
        if id_column is None:
            return None
        return next(
            (row_index for row_index in range(self.tableWidget_qso.rowCount())
             if self.tableWidget_qso.item(row_index, id_column) is not None
             and self.tableWidget_qso.item(row_index, id_column).text() == str(record_id)),
            None,
        )

    def _response_row(self):
        """Resolve the table row belonging to the worker that emitted a signal."""
        worker = self.sender()
        record_id = getattr(worker, 'target_record_id', None)
        if record_id is not None:
            row = self._find_qso_row(record_id)
            if row is not None:
                return row
        return 0 if self.tableWidget_qso.rowCount() else None

    def sent_clublog_for_call(self, row):
        '''
        Genered ADIF string
        format:
        <BAND:3>40M<CALL:6>UR4LGA<FREQ:7>7150000<MODE:3>SSB<OPERATOR:6>UR4LGA<QSO_DATE:8>20200526
        <TIME_ON:6>073213<RST_RCVD:3>SWL<RST_SENT:2>58<NAME:6>Sergey<QTH:7>Kharkiv<COMMENTS:4>qwqw
        <TIME_OFF:6>073213<EQSL_QSL_SENT:1>N<EOR>
        :return:
        '''
        self.row = row
        row_data = self.data_from_row(row)
        if not row_data:
            return
        time_string = self.std_class.std_time(row_data["time"])

        # time_to_adi = time_string[:2]+":"+time_string[2:4]+":"+time_string[4:]
        # print ("time_to_adi", time_to_adi)
        band = str(row_data.get('band') or "").strip().upper()
        if band and not band.endswith('M'):
            band += 'M'
        adi_fields = (
            ('BAND', band),
            ('CALL', row_data.get('call')),
            ('QSO_DATE', row_data.get('date')),
            ('FREQ', Adi_file._format_adif_frequency(row_data.get('freq'))),
            ('MODE', row_data.get('mode')),
            ('OPERATOR', row_data.get('operator')),
            ('TIME_ON', time_string),
            ('RST_RCVD', row_data.get('rstR')),
            ('RST_SENT', row_data.get('rstS')),
            ('NAME', row_data.get('name')),
            ('QTH', row_data.get('qth')),
            ('COMMENTS', row_data.get('comment')),
            ('TIME_OFF', time_string),
            ('EQSL_QSL_SENT', row_data.get('EQSL_QSL_SENT')),
        )
        adi_string = ''.join(_format_adi_field(name, value) for name, value in adi_fields) + '<EOR>'

        clublog = internetworker.Clublog(self.settings_dict, adi_string=adi_string)
        clublog.target_record_id = str(self.record_id)
        clublog.sent_qso_no.connect(self.clublog_sent_no_call)
        clublog.sent_qso_ok.connect(self.clublog_sent_ok_call)
        clublog.network_error.connect(self.network_error)
        clublog.operation_error.connect(self._clublog_operation_error)
        self._start_clublog_worker(clublog, "add_record")

    def del_from_clublog(self, row):
        record_object = self.data_from_row(row)
        if not record_object:
            return
        # logger.debug("Standatrt record_object:_>", record_object)
        club_log = internetworker.Clublog(self.settings_dict)
        club_log.target_record_id = str(self.record_id)
        club_log.del_qso_ok.connect(self._clublog_delete_succeeded)
        club_log.del_qso_no.connect(self.del_from_clublog_no)
        club_log.network_error.connect(self.network_error)
        club_log.operation_error.connect(self._clublog_operation_error)
        self._start_clublog_worker(club_log, "del_record", record_object)

    @QtCore.pyqtSlot(object)
    def _clublog_delete_succeeded(self, response):
        worker = self.sender()
        record_id = getattr(worker, 'target_record_id', None)
        if record_id is None:
            return
        row = self._find_qso_row(record_id)
        if row is None:
            return
        self._apply_clublog_delete_success(response, row)

    def _apply_clublog_delete_success(self, response, row):
        logger.debug("Del response OK:_>", response)
        self.tableWidget_qso.setItem(row, self._column_index['CLUBLOG_QSO_UPLOAD_STATUS'], self._make_qso_item('CLUBLOG_QSO_UPLOAD_STATUS', "N"))
        std.std.message(self, "Club log: Delete " + response.content.decode(self.settings_dict['encodeStandart']),
                        "<p style='color: green;'><b>OK</b></p>")
        self.store_change_record(row)
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot(str)
    def _clublog_operation_error(self, message):
        std.std.message(self, message, "<p style='color: red;'><b>ERROR Club Log</b></p>")

    @QtCore.pyqtSlot(object)
    def clublog_sent_ok_call(self, response):
        worker = self.sender()
        row = self._find_qso_row(getattr(worker, 'target_record_id', ''))
        if row is None:
            return
        self.tableWidget_qso.setItem(row, self._column_index['CLUBLOG_QSO_UPLOAD_STATUS'], self._make_qso_item('CLUBLOG_QSO_UPLOAD_STATUS', 'Y'))
        self.store_change_record(row_arg=row)
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot(object)
    def clublog_sent_no_call(self, response):
        worker = self.sender()
        row = self._find_qso_row(getattr(worker, 'target_record_id', ''))
        if row is None:
            return
        self.tableWidget_qso.setItem(row, self._column_index['CLUBLOG_QSO_UPLOAD_STATUS'], self._make_qso_item('CLUBLOG_QSO_UPLOAD_STATUS', 'N'))
        # self.store_change_record(row_arg=self.row)
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot(object)
    def del_from_clublog_ok(self, response):
        current_item = self.tableWidget_qso.currentItem()
        if current_item is not None:
            self._apply_clublog_delete_success(response, current_item.row())

    @QtCore.pyqtSlot(object)
    def del_from_clublog_no(self, response):
        logger.debug("Del response NO:_>", response, response.content)
        std.std.message(self, "Club log: Delete " + response.content.decode(self.settings_dict['encodeStandart']),
                        "<p style='color: red;'><b>ERROR</b></p>")
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot()
    def network_error(self):

        std.std.message(self, "<strong>Can't do it</strong><br>Check internet connection",
                        "<p style='color: red;'><b>ERROR</b></p>")

    def data_from_row(self, row):
        id_item = self.tableWidget_qso.item(row, self._column_index['id'])
        if id_item is None:
            return {}
        self.record_id = id_item.text()
        data_from_base = db.get_record_by_id(self.record_id)
        if not data_from_base:
            return {}
        date = parse.normalize_adi_date(data_from_base[0]["QSO_DATE"])
        if not date:
            date = str(data_from_base[0]["QSO_DATE"] or "").replace("-", "")
        time_on = format_table_time(data_from_base[0]["TIME_ON"])
        time_off = format_table_time(data_from_base[0]["TIME_OFF"])
        data_from_string = {

            "date": date,
            "time": time_on,
            "call": data_from_base[0]["CALL"],
            "freq": data_from_base[0]["FREQ"],
            "rstR": data_from_base[0]["RST_RCVD"],
            "rstS": data_from_base[0]["RST_SENT"],
            "name": data_from_base[0]["NAME"],
            "qth": data_from_base[0]["QTH"],
            "band": data_from_base[0]["BAND"],
            "comment": data_from_base[0]["COMMENT"],
            "time_off": time_off,
            "EQSL_QSL_SENT": data_from_base[0]["EQSL_QSL_SENT"],
            "CLUBLOG_QSO_UPLOAD_STATUS": data_from_base[0]["CLUBLOG_QSO_UPLOAD_STATUS"],
            "mode": data_from_base[0]["MODE"],
            "operator": self.settings_dict['my-call']
        }
        # self.operator = All_records[int(data_from_string['record_number']) - 1]['OPERATOR']
        # data_from_string.update({"operator": self.operator})

        return data_from_string

    def send_eqsl_for_call(self, row):
        # row = self.tableWidget.currentItem().row()

        id_item = self.tableWidget_qso.item(row, self._column_index['id'])
        time_item = self.tableWidget_qso.item(row, self._column_index['TIME_ON'])
        if id_item is None or time_item is None:
            return
        record_id = id_item.text()

        time_formated = self.std_class.std_time(time_item.text())

        qso_data = db.get_record_by_id(record_id)
        if not qso_data:
            return
        date = str(qso_data[0]['QSO_DATE']).replace("-", "")
        time = time_formated
        call = qso_data[0]['CALL']
        freq = qso_data[0]['FREQ']
        rstR = qso_data[0]['RST_RCVD']
        rstS = qso_data[0]['RST_SENT']
        name = qso_data[0]['NAME']
        qth = qso_data[0]['QTH']
        self.operator = qso_data[0]["OPERATOR"]
        band = qso_data[0]['BAND']
        comment = qso_data[0]['COMMENT']
        time_off = qso_data[0]['TIME_OFF']
        EQSL_QSL_SENT = qso_data[0]['EQSL_QSL_SENT']
        mode = qso_data[0]['MODE']
        # self.string_in_file_edit = All_records[int(record_number) - 1]['string_in_file']
        # self.records_number_edit = All_records[int(record_number) - 1]['records_number']

        recordObject = {'records_number': str(record_id), 'QSO_DATE': date, 'TIME_ON': time, 'FREQ': freq,
                        'CALL': call, 'MODE': mode,
                        'RST_RCVD': rstR, 'RST_SENT': rstS, 'NAME': name, 'QTH': qth, 'OPERATOR': self.operator,
                        'BAND': band, 'COMMENTS': comment, 'TIME_OFF': time,
                        'EQSL_QSL_SENT': EQSL_QSL_SENT}

        self.eqsl_send = internetworker.Eqsl_services(
            settingsDict=self.settings_dict,
            recordObject=recordObject,
            std=std.std,
            parent_window=self)
        self.eqsl_send.send_ok.connect(self.procesing_row)
        self.eqsl_send.error_signal.connect(self.error_eqsl)

    @QtCore.pyqtSlot(name='send_eqsl_ok')
    def procesing_row(self):
        current_item = self.tableWidget_qso.currentItem()
        if current_item is None:
            return
        row = current_item.row()
        color = QColor(self.settings_dict['eqsl-sent-color'])
        self.tableWidget_qso.setItem(row, self._column_index['EQSL_QSL_SENT'], self._make_qso_item('EQSL_QSL_SENT', "Y"))
        for i in range(self.tableWidget_qso.columnCount()):
            item = self.tableWidget_qso.item(row, i)
            if item is not None:
                item.setBackground(color)
        self.store_change_record(row_arg=row)
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot(name='error_sent_eqsl')
    def error_eqsl(self):

        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    def edit_qso(self, row):
        id_item = self.tableWidget_qso.item(row, self._column_index['id'])
        if id_item is None:
            return
        self.record_id = id_item.text()
        qso_data = db.get_record_by_id(self.record_id)
        if not qso_data:
            return
        date = self.tableWidget_qso.item(row, self._column_index['QSO_DATE']).text()
        time = self.tableWidget_qso.item(row, self._column_index['TIME_ON']).text()
        call = self.tableWidget_qso.item(row, self._column_index['CALL']).text()
        freq = qso_data[0]['FREQ']
        rstR = self.tableWidget_qso.item(row, self._column_index['RST_RCVD']).text()
        rstS = self.tableWidget_qso.item(row, self._column_index['RST_SENT']).text()
        name = self.tableWidget_qso.item(row, self._column_index['NAME']).text()
        qth = self.tableWidget_qso.item(row, self._column_index['QTH']).text()
        self.operator_edit = qso_data[0]['OPERATOR']
        band = self.tableWidget_qso.item(row, self._column_index['BAND']).text()
        comment = self.tableWidget_qso.item(row, self._column_index['COMMENT']).text()
        time_off = self.tableWidget_qso.item(row, self._column_index['TIME_OFF']).text()
        EQSL_QSL_SENT = self.tableWidget_qso.item(row, self._column_index['EQSL_QSL_SENT']).text()

        mode = self.tableWidget_qso.item(row, self._column_index['MODE']).text()

        # GUI for edit window
        self.edit_window = QWidget()
        self.edit_window.setGeometry(int(self.settings_dict['log-window-left']),
                                     int(self.settings_dict['log-window-top']),
                                     300,
                                     500)
        self.edit_window.setWindowTitle('Edit QSO with ' + call)

        style = "background-color:" + self.settings_dict['background-color'] + "; color:" + \
                self.settings_dict['color'] + ";"
        style_table = "background-color:" + self.settings_dict['form-background'] + \
                      "; color:" + self.settings_dict['color-table'] + "; font: 12px; "
        self.edit_window.setStyleSheet(style)
        self.edit_window.setWindowOpacity(0.98)
        # Call element 1
        self.call_label = QLabel("Call")
        self.call_input = QLineEdit()
        self.call_input.setStyleSheet(style_table)
        self.call_input.setFixedWidth(100)
        self.call_input.setFixedHeight(30)
        self.call_input.setText(call)
        self.call_layer = QHBoxLayout()
        self.call_layer.addWidget(self.call_label)
        self.call_layer.addWidget(self.call_input)
        # Date element 2
        self.date_label = QLabel("Date")
        self.date_input = QLineEdit()
        self.date_input.setStyleSheet(style_table)
        self.date_input.setFixedWidth(100)
        self.date_input.setFixedHeight(30)
        self.date_input.setText(date)
        self.date_layer = QHBoxLayout()
        self.date_layer.addWidget(self.date_label)
        self.date_layer.addWidget(self.date_input)
        # Time element 3
        self.time_label = QLabel("Time")
        self.time_input = QLineEdit()
        self.time_input.setStyleSheet(style_table)
        self.time_input.setFixedWidth(100)
        self.time_input.setFixedHeight(30)
        self.time_input.setText(time)
        time_layer = QHBoxLayout()
        time_layer.addWidget(self.time_label)
        time_layer.addWidget(self.time_input)
        # Freq element 4
        self.freq_label = QLabel("Frequency")
        self.freq_input = QLineEdit()
        self.freq_input.setStyleSheet(style_table)
        self.freq_input.setFixedWidth(100)
        self.freq_input.setFixedHeight(30)
        self.freq_input.setText(freq)
        self.freq_layer = QHBoxLayout()
        self.freq_layer.addWidget(self.freq_label)
        self.freq_layer.addWidget(self.freq_input)
        # RstR element 5
        self.rstr_label = QLabel("RSt reciev")
        self.rstr_input = QLineEdit()
        self.rstr_input.setStyleSheet(style_table)
        self.rstr_input.setFixedWidth(100)
        self.rstr_input.setFixedHeight(30)
        self.rstr_input.setText(rstR)
        self.rstr_layer = QHBoxLayout()
        self.rstr_layer.addWidget(self.rstr_label)
        self.rstr_layer.addWidget(self.rstr_input)
        # RstS element 6
        self.rsts_label = QLabel("RSt sent")
        self.rsts_input = QLineEdit()
        self.rsts_input.setStyleSheet(style_table)
        self.rsts_input.setFixedWidth(100)
        self.rsts_input.setFixedHeight(30)
        self.rsts_input.setText(rstS)
        self.rsts_layer = QHBoxLayout()
        self.rsts_layer.addWidget(self.rsts_label)
        self.rsts_layer.addWidget(self.rsts_input)
        # Name element 7
        self.name_label = QLabel("Name")
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(style_table)
        self.name_input.setFixedWidth(100)
        self.name_input.setFixedHeight(30)
        self.name_input.setText(name)
        self.name_layer = QHBoxLayout()
        self.name_layer.addWidget(self.name_label)
        self.name_layer.addWidget(self.name_input)
        # QTH element 8
        self.qth_label = QLabel("QTH")
        self.qth_input = QLineEdit()
        self.qth_input.setStyleSheet(style_table)
        self.qth_input.setFixedWidth(100)
        self.qth_input.setFixedHeight(30)
        self.qth_input.setText(qth)
        self.qth_layer = QHBoxLayout()
        self.qth_layer.addWidget(self.qth_label)
        self.qth_layer.addWidget(self.qth_input)
        # Mode element 9
        self.mode_label = QLabel("Mode")
        self.mode_input = QLineEdit()
        self.mode_input.setStyleSheet(style_table)
        self.mode_input.setFixedWidth(100)
        self.mode_input.setFixedHeight(30)
        self.mode_input.setText(mode)
        self.mode_layer = QHBoxLayout()
        self.mode_layer.addWidget(self.mode_label)
        self.mode_layer.addWidget(self.mode_input)
        # Band element 10
        self.band_label = QLabel("Band")
        self.band_input = QLineEdit()
        self.band_input.setStyleSheet(style_table)
        self.band_input.setFixedWidth(100)
        self.band_input.setFixedHeight(30)
        self.band_input.setText(band)
        self.band_layer = QHBoxLayout()
        self.band_layer.addWidget(self.band_label)
        self.band_layer.addWidget(self.band_input)
        # time_off element 11
        self.timeoff_label = QLabel("Time OFF")
        self.timeoff_input = QLineEdit()
        self.timeoff_input.setStyleSheet(style_table)
        self.timeoff_input.setFixedWidth(100)
        self.timeoff_input.setFixedHeight(30)
        self.timeoff_input.setText(time_off)
        timeoff_layer = QHBoxLayout()
        timeoff_layer.addWidget(self.timeoff_label)
        timeoff_layer.addWidget(self.timeoff_input)
        # Eqsl recvd element 12
        self.eslrcvd_input = QCheckBox("eQSL send")
        self.eslrcvd_input.setStyleSheet(style)
        if EQSL_QSL_SENT == "Y":
            self.eslrcvd_input.setChecked(True)
        else:
            self.eslrcvd_input.setChecked(False)
        self.club_log_ckbx = QCheckBox('Added to Club log')
        self.club_log_ckbx.setStyleSheet(style)
        data_from_row = self.data_from_row(row)

        if data_from_row.get('CLUBLOG_QSO_UPLOAD_STATUS') in ("Y", "M"):
            self.club_log_ckbx.setChecked(True)
        else:
            self.club_log_ckbx.setChecked(False)

        eslrcvd_layer = QHBoxLayout()
        eslrcvd_layer.addWidget(self.eslrcvd_input)

        # Comment element 13
        self.comment_label = QLabel("Comment")
        self.comment_input = QLineEdit()
        self.comment_input.setStyleSheet(style_table)
        self.comment_input.setFixedWidth(100)
        self.comment_input.setFixedHeight(30)
        self.comment_input.setText(comment)
        comment_layer = QHBoxLayout()
        comment_layer.addWidget(self.comment_label)
        comment_layer.addWidget(self.comment_input)
        # Set Button
        self.save_button = QPushButton("Save QSO")
        self.save_button.setFixedHeight(30)
        self.save_button.setFixedWidth(100)
        self.save_button.clicked.connect(self.apply_edit_window)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedHeight(30)
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.clicked.connect(self.edit_window_close)
        button_layer = QHBoxLayout()
        button_layer.addWidget(self.cancel_button)
        button_layer.addWidget(self.save_button)
        # Setup all elements
        vertical_box = QVBoxLayout()
        vertical_box.addLayout(self.call_layer)
        vertical_box.addLayout(self.name_layer)
        vertical_box.addLayout(self.qth_layer)
        vertical_box.addLayout(self.rstr_layer)
        vertical_box.addLayout(self.rsts_layer)
        vertical_box.addLayout(self.mode_layer)
        vertical_box.addLayout(self.band_layer)
        vertical_box.addLayout(self.freq_layer)
        vertical_box.addLayout(self.date_layer)
        vertical_box.addLayout(time_layer)
        vertical_box.addLayout(timeoff_layer)
        vertical_box.addLayout(eslrcvd_layer)
        vertical_box.addWidget(self.club_log_ckbx)

        vertical_box.addLayout(comment_layer)
        vertical_box.addLayout(button_layer)
        # Setup vertical to widget
        self.edit_window.setLayout(vertical_box)
        self.edit_window.show()

    def edit_window_close(self):
        self.edit_window.close()

    def apply_edit_window(self):
        if self.eslrcvd_input.isChecked():
            eqsl = "Y"
        else:
            eqsl = "N"

        if self.club_log_ckbx.isChecked():
            club_log = "Y"
        else:
            club_log = "N"

        logger.debug("eqsl:_>", eqsl)
        time_format = self.time_input.text().strip().replace(":", '')
        logger.debug("Time format:_>", time_format)
        date_format = self.date_input.text().strip().replace("-", '')
        new_object = {'BAND': self.band_input.text().strip(),
                      'CALL': self.call_input.text().strip(),
                      'FREQ': self.freq_input.text().strip(),
                      'MODE': self.mode_input.text().strip(),
                      'OPERATOR': self.operator_edit,
                      'QSO_DATE': self.date_input.text().strip(),
                      'TIME_ON': self.time_input.text().strip(),
                      'RST_RCVD': self.rstr_input.text().strip(),
                      'RST_SENT': self.rsts_input.text().strip(),
                      'NAME': self.name_input.text().strip(),
                      'QTH': self.qth_input.text().strip(),
                      'COMMENT': self.comment_input.text().strip(),
                      'TIME_OFF': self.timeoff_input.text().strip(),
                      'EQSL_QSL_SENT': eqsl,
                      'CLUBLOG_QSO_UPLOAD_STATUS': club_log
                      }
        db.edit_qso(self.record_id, new_object)
        self.refresh_data()
        self.edit_window.close()

    def delete_qso(self, row):
        id_item = self.tableWidget_qso.item(row, self._column_index['id'])
        if id_item is None:
            return
        record_id = id_item.text()
        db.delete_qso(record_id)
        self.tableWidget_qso.removeRow(row)
        if record_id in self.select_id_list:
            self.select_id_list.remove(record_id)
            if not self.select_id_list:
                self.hide_action_buttons()
        # self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)
        # self.tableWidget_qso.removeRow(0)

        # self.refresh_data()

    def changeEvent(self, event):

        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            if self.isMinimized():
                self.settings_dict['log-window'] = 'False'
                # logger.debug("log-window: changeEvent:_>", self.settings_dict['log-window'])
                # telnetCluster.showMinimized()
            elif self.isVisible():
                self.settings_dict['log-window'] = 'True'
                # logger.debug("log-window: changeEvent:_>", self.settings_dict['log-window'])
            QWidget.changeEvent(self, event)

    def refresh_data(self):
        if self.fill_flag == 0:
            self.fill_flag = 1
            self._loaded_rows = 0
            self._oldest_loaded_id = None
            self.select_id_list.clear()
            self.hide_action_buttons()
            self._table_color = QColor(self.settings_dict["color-table"])
            self._eqsl_color = QColor(self.settings_dict["eqsl-sent-color"])
            # Bulk updates are much faster with painting suspended.
            self._populating_table = True
            self.tableWidget_qso.setUpdatesEnabled(False)
            self.tableWidget_qso.setRowCount(0)
            self.read_base_string.start()

    def _remember_oldest_id(self, record):
        try:
            record_id = int(record.get('id'))
        except (TypeError, ValueError):
            return
        if self._oldest_loaded_id is None or record_id < self._oldest_loaded_id:
            self._oldest_loaded_id = record_id

    @QtCore.pyqtSlot(object)
    def fill_qso_table(self, records):
        """Add one record or a batch of records to the QSO table."""
        if isinstance(records, dict):
            records = [records]
        if not records:
            return
        table = self.tableWidget_qso
        first_row = table.rowCount()
        table.setRowCount(first_row + len(records))
        self._populating_table = True
        try:
            for offset, record in enumerate(records):
                self._populate_row(first_row + offset, record)
                self._remember_oldest_id(record)
        finally:
            self._populating_table = False
        self._loaded_rows = first_row + len(records)
        total = getattr(self, "allRows", 0)
        if not isinstance(total, int):
            total = len(total or ())
        if total:
            self.load_bar.setValue(min(100, round(self._loaded_rows * 100 / total)))

    def multi_select_cheked(self):
        """Rebuild the selected-id list from the checked table items."""
        self.select_id_list.clear()
        select_column = self._column_index['select']
        id_column = self._column_index['id']
        table = self.tableWidget_qso
        for row in range(table.rowCount()):
            select_item = table.item(row, select_column)
            if select_item is None or select_item.checkState() != Qt.CheckState.Checked:
                continue
            id_item = table.item(row, id_column)
            if id_item is not None:
                self.select_id_list.append(id_item.text())

        if self.select_id_list:
            self.show_action_buttons()
        else:
            self.hide_action_buttons()

    def show_action_buttons(self):
        self.multi_frame.show()

    def hide_action_buttons(self):
        self.multi_frame.hide()

    def multi_delete_qso(self):
        db.delete_qsos(self.select_id_list)
        self.select_id_list.clear()
        self.hide_action_buttons()
        self.refresh_data()


    #todo multi delete

    def multi_export_qso(self):
        ...
    #todo multi export

    def multi_send_eqsl(self):
        ...
    #todo multi send eqsl

    def multi_send_clublog(self):
        ...
    #todo multi send clublog


    @QtCore.pyqtSlot(name='fill_complited')
    def fill_complited(self):
        table = self.tableWidget_qso
        self._populating_table = False
        # Restore the sort chosen by the user before the refresh.  Sorting is
        # applied once, after the bulk insert, instead of after every batch.
        if self._sort_column is not None:
            table.sortItems(self._sort_column, self._sort_order)
        if table.rowCount() <= 2000:
            table.resizeRowsToContents()
        table.resizeColumnsToContents()
        table.setUpdatesEnabled(True)
        self.load_bar.hide()
        self.hide_action_buttons()
        self.fill_flag = 0

    @QtCore.pyqtSlot(int, name="counter_qso")
    def counter_qso(self, val):
        logForm.counter_qso = val

    @staticmethod
    def protectionItem(text, flags):
        tableWidgetItem = QTableWidgetItem(text)
        tableWidgetItem.setFlags(flags)
        return tableWidgetItem

    def store_change_record(self, row_arg=""):
        if row_arg == '':
            current_item = self.tableWidget_qso.currentItem()
            if current_item is None:
                return
            row = current_item.row()
        else:
            try:
                row = int(row_arg)
            except (TypeError, ValueError):
                return

        def cell(field):
            item = self.tableWidget_qso.item(row, self._column_index[field])
            return item.text() if item is not None else ""

        record_id = cell('id')
        if not record_id:
            return
        new_object = {
            'BAND': cell('BAND'),
            'CALL': cell('CALL'),
            'MODE': cell('MODE'),
            'OPERATOR': self.settings_dict['my-call'],
            'QSO_DATE': cell('QSO_DATE').replace("-", ""),
            'TIME_ON': cell('TIME_ON').replace(":", ""),
            'RST_RCVD': cell('RST_RCVD'),
            'RST_SENT': cell('RST_SENT'),
            'NAME': cell('NAME'),
            'QTH': cell('QTH'),
            'COMMENT': cell('COMMENT'),
            'TIME_OFF': cell('TIME_OFF'),
            'EQSL_QSL_SENT': cell('EQSL_QSL_SENT'),
            'CLUBLOG_QSO_UPLOAD_STATUS': cell('CLUBLOG_QSO_UPLOAD_STATUS'),
        }
        db.edit_qso(record_id, new_object)

    def refresh_interface(self):
        self.setGeometry(int(self.settings_dict['log-window-left']),
                         int(self.settings_dict['log-window-top']),
                         int(self.settings_dict['log-window-width']),
                         int(self.settings_dict['log-window-height']))

        self.update_color_schemes()

    def update_color_schemes(self):
        style = "background-color:" + self.settings_dict['background-color'] + "; color:" + \
                self.settings_dict['color'] + ";"

        style_form = "background-color:" + self.settings_dict['form-background'] + "; color:" + self.settings_dict[
            'color-table'] + "; font: 12px; gridline-color:" + self.settings_dict['solid-color'] + ";"
        self.tableWidget_qso.setStyleSheet(style_form + self._select_item_style)
        all_rows = self.tableWidget_qso.rowCount()
        all_cols = self.tableWidget_qso.columnCount()
        color = QColor(self.settings_dict["color-table"])
        for row in range(all_rows):
            for col in range(all_cols):
                item = self.tableWidget_qso.item(row, col)
                if item is not None:
                    item.setForeground(color)
        self.setStyleSheet(style)

    def addRecord(self, recordObject):
        """
        info for method:
        ADIF string - <BAND:3>20M <CALL:6>DL1BCL <FREQ:9>14.000000
        # <MODE:3>SSB <OPERATOR:6>UR4LGA <PFX:3>DL1 <QSLMSG:19>TNX For QSO TU 73!.
        # <QSO_DATE:8:D>20131011 <TIME_ON:6>184700 <RST_RCVD:2>57 <RST_SENT:2>57 <TIME_OFF:6>184700
        # <eQSL_QSL_RCVD:1>Y <APP_LOGGER32_QSO_NUMBER:1>1  <EOR>

        :param recordObject:
        :return:
        """

        if self.settings_dict['eqsl'] == 'enable':
            try:
                self.sync_eqsl = internetworker.Eqsl_services(settingsDict=self.settings_dict, recordObject=recordObject,
                                                              std=std.std, parent_window=self)
                self.sync_eqsl.send_ok.connect(self.eqsl_ok)
                self.sync_eqsl.error_signal.connect(self.eqsl_error)
            except Exception:
                logger.debug("Don't sent eQSL")

        adi_fields = (
            ('BAND', recordObject.get('BAND', '')),
            ('CALL', recordObject.get('CALL', '')),
            ('FREQ', Adi_file._format_adif_frequency(recordObject.get('FREQ', ''))),
            ('MODE', recordObject.get('MODE', '')),
            ('OPERATOR', recordObject.get('OPERATOR', '')),
            ('QSO_DATE', recordObject.get('QSO_DATE', '')),
            ('TIME_ON', recordObject.get('TIME_ON', '')),
            ('RST_RCVD', recordObject.get('RST_RCVD', '')),
            ('RST_SENT', recordObject.get('RST_SENT', '')),
            ('NAME', recordObject.get('NAME', '')),
            ('QTH', recordObject.get('QTH', '')),
            ('COMMENTS', recordObject.get('COMMENT', '')),
            ('TIME_OFF', recordObject.get('TIME_OFF', '')),
            ('EQSL_QSL_SENT', recordObject.get('EQSL_QSL_SENT', '')),
            ('CLUBLOG_QSO_UPLOAD_STATUS', recordObject.get('CLUBLOG_QSO_UPLOAD_STATUS', '')),
            ('STATION_CALLSIGN', recordObject.get('STATION_CALLSIGN', '')),
        )
        stringToAdiFile = ''.join(_format_adi_field(field, value) for field, value in adi_fields) + '<EOR>\n'

        # Insert into the database first so the table row gets a real id.
        inserted_id = db.record_qso_to_base(recordObject)
        try:
            qth_map_window = getattr(logForm, "qth_map", None) if "logForm" in globals() else None
            if qth_map_window is not None and hasattr(qth_map_window, "map"):
                qth_map_window.map.mark_cluster_spot_worked(recordObject.get("CALL"))
        except Exception:
            pass
        if self.settings_dict['eqsl'] == 'enable' and getattr(self, 'sync_eqsl', None) is not None:
            self.sync_eqsl.target_record_id = str(inserted_id)
        row_record = dict(recordObject)
        row_record['id'] = inserted_id

        self.tableWidget_qso.insertRow(0)
        self._populate_row(0, row_record)
        if self._sort_column is not None:
            self.tableWidget_qso.sortItems(self._sort_column, self._sort_order)
        if self.tableWidget_qso.rowCount() <= 2000:
            self.tableWidget_qso.resizeRowsToContents()

        if self.settings_dict['clublog'] == 'enable':
            self.clublog_thread = QThread()
            self.clublog = internetworker.Clublog(self.settings_dict, adi_string=stringToAdiFile)
            self.clublog.target_record_id = str(inserted_id)
            self.clublog.moveToThread(self.clublog_thread)
            self.clublog.sent_qso_ok.connect(self.clublog_sent_ok)
            self.clublog.sent_qso_no.connect(self.clublog_sent_no)
            self.clublog.network_error.connect(self.clublog_sent_error)
            self.clublog.operation_finished.connect(self.clublog_thread.quit)
            self.clublog_thread.finished.connect(self.clublog.deleteLater)
            self.clublog_thread.finished.connect(self.clublog_thread.deleteLater)
            self.clublog_thread.started.connect(self.clublog.add_record)
            self.clublog_thread.start()
        if self.settings_dict['qrz-com-logbook-enable'] == "enable":
            self.qrz_com_logbook.send_qso_to_logbook(stringToAdiFile)

    @QtCore.pyqtSlot(object)
    def clublog_sent_ok(self, response):
        row = self._response_row()
        if row is None:
            return
        self.tableWidget_qso.setItem(row, self._column_index['CLUBLOG_QSO_UPLOAD_STATUS'], self._make_qso_item('CLUBLOG_QSO_UPLOAD_STATUS', 'Y'))
        self.store_change_record(row_arg=row)

    @QtCore.pyqtSlot(object)
    def clublog_sent_no(self, response):
        std.std.message(self,
                        "Club log: " + response.content.decode(self.settings_dict['encodeStandart']) + "\n",
                        "ERROR")
        row = self._response_row()
        if row is None:
            return
        self.tableWidget_qso.setItem(row, self._column_index['CLUBLOG_QSO_UPLOAD_STATUS'], self._make_qso_item('CLUBLOG_QSO_UPLOAD_STATUS', 'N'))

    @QtCore.pyqtSlot()
    def clublog_sent_error(self):
        std.std.message(self,
                        "<strong>Can't send to Club Log</strong><br>Check internet connection<br><br><i><p style='font-size: 12px;'>You can disable auto send to Club log <br> (Settings -> Services -> Auto sent to Club log after QSO )</p></i>",
                        "<p style='color: red'>ERROR Clublog</p>")
        row = self._response_row()
        if row is None:
            return
        self.tableWidget_qso.setItem(row, self._column_index['CLUBLOG_QSO_UPLOAD_STATUS'], self._make_qso_item('CLUBLOG_QSO_UPLOAD_STATUS', 'N'))

    @QtCore.pyqtSlot(name='eqsl_ok')
    def eqsl_ok(self):
        row = self._response_row()
        if row is None:
            return
        self.tableWidget_qso.setItem(row, self._column_index['EQSL_QSL_SENT'], self._make_qso_item('EQSL_QSL_SENT', 'Y'))
        allCols = len(self.allCollumn)
        for col in range(allCols):
            item = self.tableWidget_qso.item(row, col)
            if item is not None:
                item.setBackground(QColor(self.settings_dict['eqsl-sent-color']))

        self.store_change_record(row_arg=row)

    @QtCore.pyqtSlot()
    def eqsl_error(self):
        pass

    def search_in_table(self, call):
        """Return all table rows whose CALL matches ``call``."""
        indexes = self._column_index
        call = str(call or "").strip()
        if not call:
            return []
        list_dict = []
        table = self.tableWidget_qso
        for row in range(table.rowCount()):
            name_item = table.item(row, indexes['CALL'])
            if name_item is None or name_item.text() != call:
                continue
            values = {}
            for field, key in SEARCH_TABLE_FIELDS:
                item = table.item(row, indexes[field])
                values[key] = item.text() if item is not None else ""
            list_dict.append(values)
        return list_dict


class LogSearch(QWidget):
    def __init__(self, settings_dict=None):
        super().__init__()
        self.settings_dict = settings_dict if settings_dict is not None else globals().get("self.settings_dict", {})
        self.foundList = []
        self.initUI()

    def initUI(self):

        self.setGeometry(int(self.settings_dict['log-search-window-left']), int(self.settings_dict['log-search-window-top']),
                         int(self.settings_dict['log-search-window-width']), int(self.settings_dict['log-search-window-height']))
        self.setWindowTitle('Repeats')
        self.setWindowIcon(QIcon(f'{Path(__file__).parent}/logo.png'))
        if self.settings_dict['border_wnd'] == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(float(self.settings_dict['logSearch-opacity']))
        style = "background-color:" + self.settings_dict['background-color'] + "; color:" + self.settings_dict[
            'color'] + "; font: 12px;"
        self.setStyleSheet(style)
        self.tableWidget = QTableWidget()
        style_table = "background-color:" + self.settings_dict['form-background'] + "; color:" + self.settings_dict[
            'color-table'] + "; font: 12px;  gridline-color: " + self.settings_dict['solid-color'] + ";"
        self.tableWidget.setStyleSheet(style_table)
        fnt = self.tableWidget.font()
        fnt.setPointSize(9)
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.setFont(fnt)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tableWidget)
        self.setLayout(self.layout)
        # self.show()

    def clear_table(self):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.resize_wnd = event.pos()
            self.x = self.width()
            self.y = self.height()
            self.flag_button = "right"
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()
            self.flag_button = "left"


    def mouseMoveEvent(self, event):
        if self.flag_button == "left":
            x = int(event.globalPosition().x())
            y = int(event.globalPosition().y())
            x_w = self.offset.x()
            y_w = self.offset.y()
            self.move(x - x_w, y - y_w)
        if self.flag_button == "right":
            x_r = self.resize_wnd.x() - event.pos().x()
            y_r = self.resize_wnd.y() - event.pos().y()
            self.resize(self.x - x_r, self.y - y_r)

    def changeEvent(self, event):

        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            if self.isMinimized():
                self.settings_dict['log-search-window'] = 'False'
            elif self.isVisible():
                self.settings_dict['log-search-window'] = 'True'
            QWidget.changeEvent(self, event)

    def overlap_qso_info(self, foundList):
        table = self.tableWidget
        if foundList:
            # Keep the data columns aligned with the headers below.
            columns = ("QSO_DATE", "BAND", "FREQ", "CALL", "MODE", "RST_RCVD",
                       "RST_SENT", "TIME_ON", "NAME", "QTH")
            headers = ["   Date   ", "Band", "   Freq   ", "Call", "Mode", "RST r",
                       "RST s", " Time ", "      Name      ", "      QTH      "]
            color = QColor(self.settings_dict["color-table"])
            table.setSortingEnabled(False)
            table.clearContents()
            table.setRowCount(len(foundList))
            table.setColumnCount(len(columns))
            table.setHorizontalHeaderLabels(headers)
            for row, record in enumerate(foundList):
                for column, field in enumerate(columns):
                    value = record.get(field, "")
                    if field == "QSO_DATE":
                        value = format_table_date(value)
                    elif field in ("TIME_ON", "TIME_OFF"):
                        value = format_table_time(value)
                    elif field == "FREQ":
                        value = format_frequency_hz(value)
                    elif value is None or value == "None":
                        value = ""
                    item = QTableWidgetItem(str(value))
                    item.setForeground(color)
                    table.setItem(row, column, item)
            table.setSortingEnabled(True)
            table.resizeRowsToContents()
            table.resizeColumnsToContents()
            self.foundList = foundList
        else:
            table.clearContents()
            table.setRowCount(0)

    def refresh_interface(self):

        self.setGeometry(int(self.settings_dict['log-search-window-left']), int(self.settings_dict['log-search-window-top']),
                         int(self.settings_dict['log-search-window-width']), int(self.settings_dict['log-search-window-height']))

        self.update_color_schemes()

    def update_color_schemes(self):
        style = "background-color:" + self.settings_dict['background-color'] + "; color:" + \
                self.settings_dict['color'] + ";"

        style_form = "background-color:" + self.settings_dict['form-background'] + "; color:" + self.settings_dict[
            'color-table'] + "; font: 12px"
        self.tableWidget.setStyleSheet(style_form)
        color = QColor(self.settings_dict['color-table'])
        rows = self.tableWidget.rowCount()
        cols = self.tableWidget.columnCount()
        for row in range(rows):
            for col in range(cols):
                item = self.tableWidget.item(row, col)
                if item is not None:
                    item.setForeground(color)

        self.setStyleSheet(style)


class check_update(QThread):
    update_available = pyqtSignal(object)
    no_update_available = pyqtSignal()
    request_failed = pyqtSignal()

    def __init__(self, APP_VERSION, settingsDict, parrentWindow):
        super().__init__(parrentWindow)
        self.version = APP_VERSION
        self.settingsDict = settingsDict
        self.parrent = parrentWindow

    def run(self):
        server_url = str(self.settingsDict.get('server-upd', '')).strip()
        parsed_server_url = urlsplit(server_url)
        if parsed_server_url.scheme not in {'http', 'https'} or not parsed_server_url.netloc:
            self.request_failed.emit()
            return

        callsign = str(self.settingsDict.get('my-call', '')).strip()
        if not callsign:
            self.request_failed.emit()
            return

        endpoint = (
            "api/v1/updater/"
            + quote(str(self.version), safe="")
            + "/"
            + quote(callsign, safe="")
        )
        url_action = urljoin(server_url.rstrip("/") + "/", endpoint)
        try:
            response = requests.get(url_action, timeout=30)
            response.raise_for_status()
            update_obj = response.json()
        except (requests.RequestException, ValueError, TypeError):
            self.request_failed.emit()
            return

        if not isinstance(update_obj, dict):
            self.request_failed.emit()
        elif not update_obj.get("status"):
            self.no_update_available.emit()
        elif (isinstance(update_obj.get("version"), str)
              and update_obj["version"].strip()):
            self.update_available.emit(update_obj)
        else:
            self.request_failed.emit()

    def update_processing(self, update_obj):
        update_result = QMessageBox.question(self.parrent, "LinuxLog | Updater",
                                             f"Found new version {update_obj['version']} install it?",
                                             buttons=QMessageBox.Yes | QMessageBox.No,
                                             defaultButton=QMessageBox.Yes
                                             )
        if update_result == QMessageBox.Yes:
            logger.debug("Start update process")
        if update_result == QMessageBox.No:
            logger.debug("Not start update process")
        self.enable_upd_button()
        logger.debug(f"Class check_upate.update_processing.\nInput: {update_obj}")

    def no_new_version(self):
        std.std.message(self.parrent, "You have latest version", "UPDATER")
        self.enable_upd_button()

    def enable_upd_button(self):
        self.parrent.check_update.setText("> Check update <")
        self.parrent.check_update.setEnabled(True)

    def update_check_failed(self):
        std.std.message(self.parrent, "Can't connect to the update server", "UPDATER")
        self.enable_upd_button()

class About_window(QWidget):
    def __init__(self, capture, text):
        super().__init__()
        self.capture_string = capture
        self.text_string = text
        self.initUI()

    def initUI(self):
        desktop = QApplication.primaryScreen().availableGeometry()
        # self.setGeometry(100,100,210,100)
        width_coordinate = (desktop.width() / 2) - 100
        height_coordinate = (desktop.height() / 2) - 100
        # self.setWindowModified(False)
        self.setFixedHeight(270)
        self.setFixedWidth(320)

        self.setGeometry(int(width_coordinate), int(height_coordinate), 200, 300)
        self.setWindowIcon(QIcon(f'{Path(__file__).parent }/logo.png'))
        self.setWindowTitle('About | LinuxLog')
        style = "QWidget{background-color:" + settingsDict['background-color'] + "; color:" + settingsDict['color'] + ";}"
        self.setStyleSheet(style)
        self.capture = QLabel(self.capture_string)
        self.capture.setStyleSheet("font-size: 18px")
        self.capture.setFixedHeight(30)
        self.text = QLabel(self.text_string)
        self.text.setOpenExternalLinks(True)
        # self.text.setFixedHeight(200)
        self.text.setStyleSheet("font-size: 12px")
        self.about_layer = QVBoxLayout()
        self.image = QPixmap(f"{Path(__file__).parent}/logo.png")
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setPixmap(self.image)

        # Update button
        self.check_update = QPushButton()
        self.check_update.setFixedWidth(130)
        self.check_update.setFixedHeight(60)
        self.check_update.setText("> Check update <")
        self.check_update.setStyleSheet("size: 10px;")
        self.check_update.clicked.connect(self.updater)

        # Setup layers
        self.about_layer.addWidget(self.capture)
        self.about_layer.addSpacing(5)
        self.about_layer.addWidget(self.check_update)
        self.about_layer.addWidget(self.text)
        self.horizontal_lay = QHBoxLayout()
        self.horizontal_lay.addWidget(self.image_label)
        self.horizontal_lay.addLayout(self.about_layer)

        self.setLayout(self.horizontal_lay)

    def updater(self):
        self.check_update.setEnabled(False)
        self.check_update.setText("Found update")
        self.check = check_update(APP_VERSION, settingsDict=settingsDict, parrentWindow=self)
        self.check.update_available.connect(self.check.update_processing)
        self.check.no_update_available.connect(self.check.no_new_version)
        self.check.request_failed.connect(self.check.update_check_failed)
        self.check.start()


class RealTime(QThread):
    real_time_signal = pyqtSignal(object)

    def __init__(self, logformwindow, parent=None):
        super().__init__(logformwindow)
        self.logformwindow = logformwindow
        self.run_flag = True

    def stop_(self):
        self.run_flag = False

    def run(self):
        while self.run_flag:
            self.real_time_signal.emit((strftime("%H:%M:%S", localtime()), strftime("%H:%M:%S", gmtime())))
            time.sleep(0.1)

class ClikableLabel(QLabel):
    click_signal = QtCore.pyqtSignal()
    change_value_signal = QtCore.pyqtSignal()

    def __init__(self, parrent=None):
        QLabel.__init__(self, parrent)

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.click_signal.emit()


class FreqWindow(QWidget):
    figure = QtCore.pyqtSignal(str)

    def __init__(self, settings_dict, parent_window):
        super().__init__()
        self.settings_dict = settings_dict
        self.memory_list = []
        self.parent_window = parent_window
        self.active_memory_element = "0"
        self.label_style = "background:" + self.settings_dict['form-background'] + \
                           "; color:" + self.settings_dict['color-table'] + "; font: 25px;"
        self.style_mem_label = f"background: {self.settings_dict['form-background']}; color: {self.settings_dict['color-table']}; font: 12px;"
        self.style = f"background: {self.settings_dict['background-color']}; color: {self.settings_dict['color']}; font: 12px;"
        self.style_window = f"background: {self.settings_dict['background-color']}; color: {self.settings_dict['color']};"
        self.freq_status = 0
        self.initUI()

        if self.isEnabled():
            self.init_data()

    def keyPressEvent(self, e):

        if e.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self.enter_freq()
        if e.key() == QtCore.Qt.Key_F12:
            self.close()

    def initUI(self):
        self.setGeometry(int(self.settings_dict['log-form-window-left']) + logForm.width(),
                         int(self.settings_dict['log-form-window-top']),
                         200, int(self.settings_dict['log-form-window-height']))
        self.setFixedHeight(320)
        self.setWindowOpacity(float(self.settings_dict['freq-input-window-opacity']))
        self.setWindowTitle('Frequency')
        self.setStyleSheet(self.style_window)
        # Create elements

        # create digit buttons 0-9
        for digit in range(10):
            button = QPushButton(str(digit))
            button.setStyleSheet(self.style)
            button.setFixedSize(40, 40)
            button.clicked.connect(self.num_clicked)
            button.setShortcut(str(digit))
            setattr(self, f"button_{digit}", button)
        # create button Point
        self.button_p = QPushButton("<-")
        self.button_p.setStyleSheet(self.style)
        self.button_p.setFixedSize(40, 40)
        self.button_p.clicked.connect(self.delete_symbol_freq)
        self.button_p.setShortcut('Backspace')
        # create button CLR
        self.button_clear = QPushButton("CLR")
        self.button_clear.setStyleSheet(self.style)
        self.button_clear.setFixedSize(40, 40)
        self.button_clear.clicked.connect(self.clear_freq_label)
        self.button_clear.setShortcut('Esc')
        # create button Ent
        self.button_ent = QPushButton("Enter")
        self.button_ent.setStyleSheet(self.style)
        self.button_ent.setFixedSize(60, 40)
        self.button_ent.clicked.connect(self.enter_freq)
        # self.button_ent.setShortcut('Enter')
        # self.button_ent.setShortcut('Return')
        # create button Save in memory
        self.button_sm = QPushButton("+memory")
        self.button_sm.setStyleSheet(self.style)
        self.button_sm.setFixedSize(60, 25)
        self.button_sm.clicked.connect(self.save_freq_to_memory)
        # create button up in memory
        self.button_up = QPushButton("▲")
        self.button_up.setStyleSheet(self.style)
        self.button_up.setFixedSize(60, 20)
        self.button_up.clicked.connect(self.change_memory_element)
        # create button down in memory
        self.button_dn = QPushButton("▼")
        self.button_dn.setStyleSheet(self.style)
        self.button_dn.setFixedSize(60, 20)
        self.button_dn.clicked.connect(self.change_memory_element)
        # create recall from memory
        self.button_all_rm = QPushButton("memory>")
        self.button_all_rm.setStyleSheet(self.style)
        self.button_all_rm.setFixedSize(60, 25)
        self.button_all_rm.clicked.connect(self.recal_from_memory)
        # delete from memory
        self.button_dm = QPushButton("- memory")
        self.button_dm.setStyleSheet(self.style)
        self.button_dm.setFixedSize(60, 25)
        self.button_dm.clicked.connect(self.delete_from_memory)
        # create button up in memory
        self.button_all_m = QPushButton("Show \n memory")
        self.button_all_m.setStyleSheet(self.style)
        self.button_all_m.setFixedSize(60, 40)
        # create label with memory
        self.memory_label = QLabel()
        self.memory_label.setStyleSheet(self.style)
        self.memory_label.setFixedHeight(10)
        # Create freq Label
        self.freq_label = QLabel()
        freq = logForm.get_freq()
        if freq.isnumeric():
            freq_to_label = self.freq_to_sting(freq)
            if freq_to_label:
                self.freq_label.setText(freq_to_label + " Hz")
        self.freq_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.freq_label.setStyleSheet(self.label_style)
        self.freq_label.setFixedHeight(50)
        self.freq_label.setFixedWidth(200)
        # create memory label Show
        self.memory_label_show = QLabel()
        self.memory_label_show.setStyleSheet(self.style_mem_label)
        self.memory_label_show.setFixedWidth(200)
        self.memory_label_show.setFixedHeight(20)
        # create Close chekbox element
        self.close_checkbox = QCheckBox("Close after enter freq")
        self.close_checkbox.setStyleSheet(self.style)
        if self.settings_dict['freq-wnd'] == "enable":
            self.close_checkbox.setChecked(True)
        #####################
        # Setup to lay
        # 1-3
        self.buttons1_3_lay = QHBoxLayout()
        self.buttons1_3_lay.addWidget(self.button_1)
        self.buttons1_3_lay.addWidget(self.button_2)
        self.buttons1_3_lay.addWidget(self.button_3)
        # 4-6
        self.buttons4_6_lay = QHBoxLayout()
        self.buttons4_6_lay.addWidget(self.button_4)
        self.buttons4_6_lay.addWidget(self.button_5)
        self.buttons4_6_lay.addWidget(self.button_6)
        # 7-9
        self.buttons7_9_lay = QHBoxLayout()
        self.buttons7_9_lay.addWidget(self.button_7)
        self.buttons7_9_lay.addWidget(self.button_8)
        self.buttons7_9_lay.addWidget(self.button_9)
        # clr - 0 - point
        self.buttons0_lay = QHBoxLayout()
        self.buttons0_lay.addWidget(self.button_clear)
        self.buttons0_lay.addWidget(self.button_0)
        self.buttons0_lay.addWidget(self.button_p)
        # memory lay & enter button
        self.buttons_memory_lay = QVBoxLayout()
        self.buttons_memory_lay.addSpacing(10)
        self.buttons_memory_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.buttons_memory_lay.addWidget(self.button_sm)
        self.buttons_memory_lay.addWidget(self.button_up)
        self.memory_bank_num = QHBoxLayout()
        self.memory_bank_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.memory_bank_num.addWidget(self.memory_label)
        self.buttons_memory_lay.addLayout(self.memory_bank_num)
        self.buttons_memory_lay.addWidget(self.button_dn)
        self.buttons_memory_lay.addWidget(self.button_dm)
        self.buttons_memory_lay.addWidget(self.button_all_rm)
        # self.buttons_memory_lay.addWidget(self.button_all_m)
        self.buttons_memory_lay.addWidget(self.button_ent)
        self.buttons_memory_lay.addSpacing(15)
        # create NUM layer
        self.num_buttons_lay = QVBoxLayout()
        self.num_buttons_lay.addLayout(self.buttons1_3_lay)
        self.num_buttons_lay.addLayout(self.buttons4_6_lay)
        self.num_buttons_lay.addLayout(self.buttons7_9_lay)
        self.num_buttons_lay.addLayout(self.buttons0_lay)
        self.num_buttons_lay.addWidget(self.close_checkbox)
        # create all button layer
        self.button_layer = QHBoxLayout()
        # self.button_layer.setGeometry(QRect(0, 0, 100, 100))
        self.button_layer.addLayout(self.num_buttons_lay)
        self.button_layer.addLayout(self.buttons_memory_lay)
        #
        self.general_lay = QVBoxLayout()
        self.general_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        # self.general_lay.
        self.general_lay.addWidget(self.memory_label_show)
        self.general_lay.addWidget(self.freq_label)
        self.general_lay.addLayout(self.button_layer)
        # self.general_lay.
        self.general_lay.addStretch()
        # setup general lay to form
        self.setLayout(self.general_lay)
        self.show()

    def init_data(self):
        self.memory_list = json.loads(self.settings_dict['memory-freq'])
        len_memory_list = len(self.memory_list)
        if len_memory_list > 0:
            self.memory_label.setText(str(len_memory_list))

            self.memory_label_show.setText(
                "Mem: " + str(len_memory_list) + " Frq: " + str(self.memory_list[len_memory_list - 1]))
        else:
            self.memory_label.setText('')
            self.memory_label_show.setText('')
        # self.init_data()

    def clear_freq_label(self):
        self.freq_label.clear()
        self.freq_status = 0

    def num_clicked(self):
        button = self.sender()
        digit_freq = self.freq_label.text().replace('.', '').replace(' Hz', '')
        if self.freq_status == 0:
            digit_freq = ''
            self.freq_status = 1
        future_freq = digit_freq + button.text()
        if int(future_freq or 0) < 146000000:
            self.freq_label.setText(self.freq_to_sting(future_freq) + " Hz")
        else:
            self.freq_label.setText("146.000.000 Hz")

    def freq_to_sting(self, freq):
        return format_frequency_hz(freq)

    def enter_freq(self):
        frequency = self.freq_label.text().replace(" Hz", "").replace('.', '').strip()
        if not frequency.isdigit() or len(frequency) <= 3 or int(frequency) <= 0:
            if self.close_checkbox.isChecked():
                self.close()
            return
        std_value = std.std()
        logForm.set_freq(frequency)
        if self.settings_dict['rigctl-enabled'] == "enable":
            self.parent_window.rigctl_set_freq_to_trx(frequency)
        padded_frequency = frequency.zfill(8)
        if self.settings_dict['tci'] == 'enable':
            band = std_value.get_std_band(padded_frequency)
            mode = std_value.mode_band_plan(band, padded_frequency)
            if isinstance(mode, (tuple, list)):
                mode = mode[0]
            try:
                tci_sndr.set_freq(padded_frequency)
                tci_sndr.set_mode("0", mode)
            except Exception:
                logger.debug("enter_freq:_> Can't setup tci_freq")
        if self.settings_dict['cat'] == 'enable':
            self.parent_window.set_freq_for_cat(padded_frequency)
        if self.close_checkbox.isChecked():
            self.close()

    def delete_symbol_freq(self):
        self.freq_status = 1
        freq_str = self.freq_label.text().replace(" Hz", "")
        freq_str_del = freq_str[:-1]
        self.freq_label.setText(freq_str_del + " Hz")

    def save_freq_to_memory(self):
        frequency = self.freq_label.text().strip()
        if not frequency:
            return
        self.memory_list.append(frequency)
        self.active_memory_element = str(len(self.memory_list))
        self.memory_label.setText(self.active_memory_element)
        self.memory_label_show.setText("Mem: " + self.active_memory_element +
                                       " Frq: " + str(self.memory_list[-1]))

    def set_freq(self, freq):
        freq_to_label = self.freq_to_sting(freq)
        if freq_to_label:
            self.freq_label.setText(freq_to_label + " Hz")

    def change_memory_element(self):
        button = self.sender()
        if not self.memory_list or self.memory_label.text() == '':
            return
        index = int(self.memory_label.text())
        if button.text() == "▲":
            index = len(self.memory_list) if index - 1 == 0 else index - 1
        elif button.text() == "▼":
            index = 1 if index + 1 > len(self.memory_list) else index + 1
        self.index = index
        self.memory_label.setText(str(index))
        self.memory_label_show.setText("Mem: " + str(index) + " Frq: " + self.memory_list[index - 1])

    def delete_from_memory(self):
        if self.memory_label.text() != '' and self.memory_list:
            index = int(self.memory_label.text()) - 1
            if not 0 <= index < len(self.memory_list):
                return
            del self.memory_list[index]
            if not self.memory_list:
                self.memory_label.setText('')
                self.memory_label_show.setText('No freq in memory')
            elif index == 0:
                self.memory_label.setText('1')
            else:
                self.memory_label.setText(str(index))

    def recal_from_memory(self):
        if self.memory_label.text() != '' and self.memory_list:
            index = int(self.memory_label.text()) - 1
            if 0 <= index < len(self.memory_list):
                self.freq_label.setText(self.memory_list[index])
                self.enter_freq()

    def refresh_interface(self):
        self.label_style = "background:" + self.settings_dict['form-background'] + \
                           "; color:" + self.settings_dict['color-table'] + "; font: 25px"
        self.style = "background:" + self.settings_dict['background-color'] + "; color:" \
                     + self.settings_dict['color'] + "; font: 12px;"
        self.style_window = "background:" + self.settings_dict['background-color'] + "; color:" \
                            + self.settings_dict['color'] + ";"
        self.style_mem_label = "background:" + self.settings_dict['form-background'] + \
                               "; color:" + self.settings_dict['color-table'] + "; font: 12px"

        self.updatesEnabled()

    def closeEvent(self, event):
        self.settings_dict['memory-freq'] = json.dumps(self.memory_list)
        self.settings_dict['band'] = logForm.get_band()
        if self.close_checkbox.isChecked():
            self.settings_dict['freq-wnd'] = 'enable'
        else:
            self.settings_dict['freq-wnd'] = 'disable'

        self.settingsDict = self.settings_dict
        Settings_file.update_file_to_disk(self)
        event.accept()


class LogForm(QMainWindow):
    change_mode_signal = QtCore.pyqtSignal(str)

    def __init__(self, settings_dict, log_search):
        super().__init__()
        self.settings_dict = settings_dict
        self.logSearch = log_search
        self._filter = Filter(internetSearch, self.settings_dict)
        self.diploms_init()
        self.spot_index_by_band = {}
        # self.updater = update_after_run(version=APP_VERSION, settings_dict=self.settings_dict)
        self.country_dict = self.get_country_dict()
        self._build_country_prefix_index()
        self.mode = self.settings_dict['mode']
        self.db = db
        self.db.search_in_db_like_signal.connect(self.olerlap_found_qso)
        self.diplomsCheck()
        self.qrz_com_ready = False
        self.rigctl_main_loop = None
        self.sender = None
        self.current_spot = None
        self.prev_spots = None
        self.trx = None
        self.qrz_com = None
        self._pending_lookup = ""
        self._lookup_timer = QTimer(self)
        self._lookup_timer.setSingleShot(True)
        self._lookup_timer.setInterval(300)
        self._lookup_timer.timeout.connect(self._run_call_lookup)

        self.initUI()
        self._configure_qrz_com()
        self.rigctl_init_base_data()

    def _configure_qrz_com(self):
        enabled = (
            self.settings_dict.get("qrz-com-enable") == "enable"
            and bool(self.settings_dict.get("qrz-com-username"))
            and bool(self.settings_dict.get("qrz-com-password"))
        )
        username = self.settings_dict.get("qrz-com-username", "")
        password = self.settings_dict.get("qrz-com-password", "")
        current_client = self.qrz_com

        if current_client is not None:
            if (
                enabled
                and current_client.qrz_com_thread.isRunning()
                and (current_client.username, current_client.password) == (username, password)
            ):
                return True
            if not current_client.stop_thread():
                return False
            current_client.deleteLater()
            self.qrz_com = None
            self.qrz_com_ready = False

        if not enabled:
            self.qrz_com_ready = False
            return True

        self.qrz_com = QrzComApi(username, password, parent=self)
        self.qrz_com.data_info.connect(self.fill_form)
        self.qrz_com.qrz_com_connect.connect(self.qrz_com_status)
        self.qrz_com.qrz_com_error.connect(self.qrz_com_error)
        return True


    def set_current_spot(self, spot_dict):
        self.current_spot = spot_dict
    def rigctl_init_base_data(self):
        if self.settings_dict['rigctl-enabled'] == "enable":
            self.set_rigctl_stat(color="#aaaaaa")
            self.trx = Rigctl_thread(self.settings_dict['rigctl-uri'], self.settings_dict['rigctl-port-rx1'])
            self.trx.rigctl_ready_signal.connect(self.rigctl_start_main_loop)
            self.trx.start()

    def rigctl_stop(self):
        if self.rigctl_main_loop is not None:
            self.rigctl_main_loop.set_restart_flag(False)
            self.rigctl_main_loop.stop_main_loop()
            self.set_rigctl_stat(color="#aaaaaa")
        if self.trx is not None:
            self.trx.socket_shutdown()
            self.trx = None



    @QtCore.pyqtSlot(object)
    def rigctl_start_main_loop(self, socket):
        logger.debug(f"rigctl _start_main_loop")
        self.rigctl_main_loop = RigctlMainLoop(
            socket=socket,
            sleep_time=float(self.settings_dict['rigctl-refresh-time']),
            encoding=self.settings_dict['encodeStandart']
        )
        self.rigctl_main_loop.rigctl_stop_loop_signal.connect(self.rigctl_restart_main_loop)
        self.rigctl_main_loop.timeout_signal.connect(self.rigctl_stat_off)
        self.rigctl_main_loop.frequency_signal.connect(self.rigctl_set_freq)
        self.rigctl_main_loop.vfo_signal.connect(self.rigctl_set_vfo)
        self.rigctl_main_loop.mode_signal.connect(self.rigctl_set_mode)
        self.rigctl_main_loop.ptt_signal.connect(self.rigctl_set_ptt)
        self.rigctl_main_loop.start()
        self.set_rigctl_stat()
        self.sender = Rigctl_sender(socket)

    @QtCore.pyqtSlot(object)
    def rigctl_restart_main_loop(self, input_thread: RigctlMainLoop):
        self.set_rigctl_stat(color="#aaaaaa")
        if self.rigctl_main_loop.isRunning():
            self.rigctl_main_loop.stop_()
            self.rigctl_main_loop.wait()
        logger.debug(f"stoped: {input_thread.isRunning()}")
        self.trx.socket_shutdown()
        self.rigctl_init_base_data()

    @QtCore.pyqtSlot()
    def rigctl_stat_off(self):
        self.set_rigctl_stat(color="#aaaaaa")
        logger.debug(f"Restart main loop: {self.rigctl_main_loop.isRunning()}")

    def rigctl_set_freq_to_trx(self, freq):
        if self.sender is not None:
            band = std.std().get_std_band(freq)
            mode = std.std().mode_band_plan(band, freq)
            if isinstance(mode, (tuple, list)):
                mode = mode[0]
            self.sender.send_command(f"M {mode}")
            self.sender.send_command(f"F {freq}")
        # self.rigctl_main_loop.command_transaction(f"M {mode}")
        # self.rigctl_main_loop.command_transaction(f"F {freq}")

    @QtCore.pyqtSlot(object)
    def rigctl_set_freq(self, freq_str):
        self.set_freq(freq_str)
        standart = std.std()
        band = standart.get_std_band(freq_str)
        self.set_band(band)

    @QtCore.pyqtSlot(object)
    def rigctl_set_vfo(self, vfo_str):
        self.set_vfo(vfo_str)

    @QtCore.pyqtSlot(object)
    def rigctl_set_mode(self, mode):
        self.set_mode_rigctl(mode)

    @QtCore.pyqtSlot(object)
    def rigctl_set_ptt(self, ptt):
        pass

    def get_qrz_com_ready(self):
        return self.qrz_com_ready

    def get_info_from_qrz(self, text_call):
        if self.qrz_com_ready and self.qrz_com is not None:
            self.qrz_com.get_callsign_info(text_call)

    @PyQt6.QtCore.pyqtSlot(bool)
    def qrz_com_status(self, connect):
        if connect:
            self.set_qrz_com_stat()
            self.qrz_com_ready = True
        else:
            self.qrz_com_ready = False
            self.set_qrz_com_wrong("qrz.com")

    @PyQt6.QtCore.pyqtSlot(object)
    def qrz_com_error(self, error_message):
        std.std().message(error_message, "QRZ.COM ERROR")

    @PyQt6.QtCore.pyqtSlot(object)
    def fill_form(self, data):
        if data is not None:
            result_call = str(data.get("call") or "").strip().upper()
            current_call = self.inputCall.text().strip().upper()
            if result_call and result_call != current_call:
                # Ignore a late QRZ.com answer for a callsign that is no
                # longer in the input field (e.g. the user deleted it or
                # selected another spot).  Portable suffixes such as /P
                # still count as the same station.
                result_base = result_call.split("/")[0]
                current_base = current_call.split("/")[0]
                if not current_base or result_base != current_base:
                    return
            self.set_qrz_com_stat()
            if data.get("f_name") is not None:
                self.inputName.setText(data["f_name"])
            elif data.get("s_name"):
                self.inputName.setText(data["s_name"])
            else:
                self.inputName.clear()
            if data.get("qth") is not None:
                self.inputQth.setText(data["qth"])
            else:
                self.inputQth.clear()
            call = self.inputCall.text().strip().upper()
            grid = str(data.get("grid") or "").strip()
            if not grid and data.get("lat") and data.get("lon"):
                try:
                    grid = latlon_to_locator(
                        float(data["lat"]), float(data["lon"]), precision=6
                    )
                except (TypeError, ValueError):
                    grid = ""
            if call and grid:
                publish("qth.map.update", {"call": call, "locator": grid, "source": "qrz.com"})
        else:
            self.inputQth.clear()
            self.inputName.clear()

    @QtCore.pyqtSlot(object)
    def olerlap_found_qso(self, obj: list):
        self.logSearch.overlap_qso_info(obj)

    def get_coordinate_windows(self):
        '''
        This method packing coordinates and visibale state in
        dictionary
         {key (name coordiantes in config-file): value

        :return: dict: {name coordiantes in config-file: value}
        '''
        self.parameter = {}
        internetSearch_geometry = internetSearch.geometry()
        logger.debug(internetSearch.isVisible())
        logWindow_geometry = logWindow.geometry()
        logSearch_geometry = logSearch.geometry()
        logForm_geometry = logForm.geometry()
        telnetCluster_geometry = telnetCluster.geometry()
        qth_map_window = getattr(self, "qth_map", None)
        if qth_map_window is not None:
            qth_map_geometry = qth_map_window.geometry()
        self.parameter.update({'search-internet-left': str(internetSearch_geometry.left()),
                               'search-internet-top': str(internetSearch_geometry.top()),
                               'search-internet-width': str(internetSearch_geometry.width()),
                               'search-internet-height': str(internetSearch_geometry.height()),
                               'log-window-left': str(logWindow_geometry.left()),
                               'log-window-top': str(logWindow_geometry.top()),
                               'log-window-width': str(logWindow_geometry.width()),
                               'log-window-height': str(logWindow_geometry.height()),
                               'log-search-window-left': str(logSearch_geometry.left()),
                               'log-search-window-top': str(logSearch_geometry.top()),
                               'log-search-window-width': str(logSearch_geometry.width()),
                               'log-search-window-height': str(logSearch_geometry.height()),
                               'log-form-window-left': str(logForm_geometry.left()),
                               'log-form-window-top': str(logForm_geometry.top()),
                               'log-form-window-width': str(logForm_geometry.width()),
                               'log-form-window-height': str(logForm_geometry.height()),
                               'telnet-cluster-window-left': str(telnetCluster_geometry.left()),
                               'telnet-cluster-window-top': str(telnetCluster_geometry.top()),
                               'telnet-cluster-window-width': str(telnetCluster_geometry.width()),
                               'telnet-cluster-window-height': str(telnetCluster_geometry.height()),
                               'log-search-window': str(logSearch.isVisible()),
                               'telnet-cluster-window': str(telnetCluster.isVisible()),
                               'search-internet-window': str(internetSearch.isVisible()),
                               'qth-map-window': str(qth_map_window.isVisible()) if qth_map_window is not None else 'False',
                               })
        if qth_map_window is not None:
            self.parameter.update({
                'qth-map-window-left': str(qth_map_geometry.left()),
                'qth-map-window-top': str(qth_map_geometry.top()),
                'qth-map-window-width': str(qth_map_geometry.width()),
                'qth-map-window-height': str(qth_map_geometry.height()),
            })
        return self.parameter

    def save_coordinate_to_new_profile(self):

        self.name = std.wnd_what("Save Profile as...")
        self.name.ok.connect(self.save_profile_name)

    def save_coordinate_to_profile(self):
        self.coordinates_w = self.get_coordinate_windows()
        logger.debug(self.coordinates_w)
        profile_list = json.loads(self.settings_dict['coordinate-profile'])

        for elem in profile_list:
            if elem['name'] == self.settings_dict['active-profile']:
                elem.update(self.coordinates_w)
        json_string = json.dumps(profile_list)
        self.settings_dict['coordinate-profile'] = json_string
        self.param = {'coordinate-profile': json_string,
                      'active-profile': self.settings_dict['active-profile']}
        self.remember_in_cfg(self.param)

    @QtCore.pyqtSlot(str)
    def save_profile_name(self, name):
        json_list = json.loads(self.settings_dict['coordinate-profile'])
        self.coordinates = self.get_coordinate_windows()
        self.coordinates.update({"name": name})
        json_list.append(self.coordinates)
        json_string = json.dumps(json_list)
        # logger.debug("json_string:_>", json_string)
        self.settings_dict['coordinate-profile'] = json_string
        self.param = {'coordinate-profile': json_string,
                      'active-profile': name}
        self.remember_in_cfg(self.param)
        self.settings_dict['active-profile'] = name
        self.update_cordinates()
        self.profile_update_menu()

    def trx_enable(self, parameter):
        if parameter == 'rx':
            try:
                self.cw_machine.reset()

            except Exception:
                pass
            logger.debug("RX")

        if parameter == 'tx':
            try:
                self.cw_machine.set_tx_stat()
            except Exception:
                pass

            logger.debug("TX")

    def update_cordinates(self):
        json_list = json.loads(self.settings_dict['coordinate-profile'])
        for elem in json_list:
            if elem['name'] == self.settings_dict['active-profile']:
                for key in elem:
                    if key != "name":
                        self.settings_dict[key] = elem[key]
        logSearch.refresh_interface()
        logWindow.refresh_interface()
        telnetCluster.refresh_interface()
        internetSearch.refresh_interface()
        logForm.refresh_interface()
        qth_map_window = getattr(logForm, "qth_map", None)
        if qth_map_window is not None:
            try:
                qth_map_window.setGeometry(
                    int(self.settings_dict.get("qth-map-window-left", qth_map_window.x())),
                    int(self.settings_dict.get("qth-map-window-top", qth_map_window.y())),
                    int(self.settings_dict.get("qth-map-window-width", qth_map_window.width())),
                    int(self.settings_dict.get("qth-map-window-height", qth_map_window.height())),
                )
            except (TypeError, ValueError):
                pass
            if self.settings_dict.get("qth-map-window") == "True":
                qth_map_window.show()
            else:
                qth_map_window.hide()

    def change_profile(self, text):
        logger.debug(text)

    def tx_tci(self, flag):
        logger.debug("FLag", flag)
        if flag == "restart":
            logger.debug("FLag", flag)
            tci_sndr.update_tx_tci()

    @QtCore.pyqtSlot()
    def restart_tci_sender(self):
        self.tx_tci("restart")

    @QtCore.pyqtSlot(str, str, str)
    def handle_tci_spot(self, call, frequency, mode):
        self.set_call(call)
        self.set_freq(frequency)
        if mode.lower() != "error":
            self.set_mode_tci(mode)
            tci_sndr.set_mode("0", mode.upper())

    def sendMesageToTCI(self, message):
        ...
        #tci_recv.tci_reciever.tci_send_command("RX_SENSORS_ENABLE:true,500;")
        #tci_sndr.send_command(message)

    def dBm_to_S(self, dBm):
        try:
            value = float(dBm)
        except (TypeError, ValueError):
            return ""
        for bound, label in S_METER_STEPS:
            if value < bound:
                return label
        return "9+60"

    def set_rs_s(self, dBm):
        self.inputRstS.setText(f"5{self.dBm_to_S(dBm) if self.comboMode.currentText() != 'DIGI' else dBm}")

    def set_data_qso(self, found_list):
        # logger.debug("Found_list:", found_list)
        if len(found_list) > 0:
            for record in found_list:
                if record['NAME'] != '':
                    self.inputName.setText(record['NAME'])
                if record['QTH'] != '':
                    self.inputQth.setText(record['QTH'])
                if record['COMMENT'] != '':
                    self.comments.setText(record['COMMENT'])
        else:
            self.inputName.setText('')
            self.inputQth.setText('')
            # print ("Found_list:", found_list)

    def get_country_dict(self):

        with open(Path(__file__).parent / self.settings_dict['country-file'], 'r') as f:
            country_json = json.load(f)

        return country_json

    def _build_country_prefix_index(self):
        """Build a prefix -> country tuple index once instead of scanning every call."""
        index = {}
        max_length = 0
        for country, metadata in self.country_dict.items():
            if not isinstance(metadata, dict):
                continue
            prefixes = metadata.get("prefix", ())
            if not isinstance(prefixes, (list, tuple)):
                continue
            data = (country, metadata.get("itu", ""), metadata.get("cq-zone", ""))
            for raw_prefix in prefixes:
                prefix = str(raw_prefix).strip().upper()
                if not prefix:
                    continue
                index.setdefault(prefix, data)
                if len(prefix) > max_length:
                    max_length = len(prefix)
        self._country_prefix_index = index
        self._country_prefix_max_length = max_length

    def start_cat(self):
        self.cat_system = cat.Cat_start(self.settings_dict, self)
        # self.cat_system.start_reciever_cat()

    def stop_cat(self):
        logger.debug("stoped CAT")
        self.set_cat_label(0)
        # try:
        self.cat_system.stop_cat()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key.Key_F5:
            self.full_clear_form()
        if e.key() == QtCore.Qt.Key.Key_F12:
            self.freq_window()
        if e.key() == Qt.Key.Key_F2:
            self.get_prev_spot_on_band()
        if e.key() == QtCore.Qt.Key.Key_F3:
            self.get_next_spot_on_band()
        if e.key() == Qt.Key.Key_F4:
            self.get_prev_general_spot()
        if e.key() == Qt.Key.Key_F6:
            self.get_last_general_spot()
        if e.key() in (QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return):
            self.logFormInput()

    def get_last_general_spot(self):
        logger.debug("get last general spot")
        all_spots = telnetCluster.get_all_spots()
        #logger.debug(all_spots)
        if all_spots and self.current_spot != all_spots[-1]:
            self.prev_spots = self.current_spot
            self.current_spot = all_spots[-1]
            self.fill_qso_form_from_cluster(self.current_spot)
        else:
            logger.debug("No spots")

    def get_prev_general_spot(self):
        logger.debug("get prev spot")
        if self.prev_spots is not None:
            spot = self.prev_spots
            self.prev_spots = self.current_spot
            self.current_spot = spot
            self.fill_qso_form_from_cluster(self.current_spot)
        else:
            logger.debug(f"No prev spots")

    def get_last_spot_on_band(self):
        logger.debug("get last spot on band")
        spots_on_band = self.get_spots_for_current_band()
        if spots_on_band:
            self.prev_spots = self.current_spot
            self.current_spot = spots_on_band[-1]
            self.fill_qso_form_from_cluster(self.current_spot)
        else:
            logger.debug("No spots")

    def _unlogged_spots_on_current_band(self):
        """Spots for the current band whose callsign is not in the log yet."""
        band = self.get_current_band()
        spots = [
            spot for spot in telnetCluster.get_all_spots()
            if spot is not None and spot.get('band') == band
        ]
        if not spots:
            return []
        logged_calls = db.calls_in_base([spot.get('call') for spot in spots])
        return [spot for spot in spots if str(spot.get('call', '')).strip().upper() not in logged_calls]

    def get_next_spot_on_band(self):
        band = self.get_current_band()
        spots_on_band = self._unlogged_spots_on_current_band()
        if not spots_on_band:
            logger.debug("For this band no spot")
            return
        index = self.spot_index_by_band.get(band, -1) + 1
        if index <= len(spots_on_band) - 1:
            self.spot_index_by_band[band] = index
            self.prev_spots = self.current_spot
            self.current_spot = spots_on_band[index]
            self.fill_qso_form_from_cluster(self.current_spot)
        else:
            logger.debug("Last spot by next")

    def get_prev_spot_on_band(self):
        band = self.get_current_band()
        spots_on_band = self._unlogged_spots_on_current_band()
        if not spots_on_band:
            logger.debug("For this band no spot")
            return
        index = self.spot_index_by_band.get(band, 0) - 1
        if 0 <= index <= len(spots_on_band) - 1:
            self.spot_index_by_band[band] = index
            self.prev_spots = self.current_spot
            self.current_spot = spots_on_band[index]
            self.fill_qso_form_from_cluster(self.current_spot)
        else:
            logger.debug("Last spot by prev")

    def get_spots_for_current_band(self):
        return self._unlogged_spots_on_current_band()

    def fill_from_map_spot(self, call, freq=""):
        call = str(call or "").strip().upper()
        freq = str(freq or "").strip()
        if not call:
            return
        self.inputCall.setText(call)
        if freq:
            self.set_freq(freq)
        self.get_info_from_qrz(call)
        self.img_search = internetworker.internetWorker(window=internetSearch, settings=self.settings_dict)
        self.img_search.set_callsign_for_search(callsign=call)
        self.img_search.start()
        if self.settings_dict.get("rigctl-enabled") == "enable":
            try:
                self.rigctl_set_freq_to_trx(freq)
            except Exception:
                pass
        if self.settings_dict.get("tci") == "enable" and freq:
            try:
                tci_sndr.set_freq(freq)
            except Exception:
                logger.debug("Set_freq_map_spot: Can't set frequency")

    def fill_qso_form_from_cluster(self, qso_data):
        if qso_data is not None:
            call = qso_data.get('call', '')
            freq = qso_data.get('freq', '')
            mode = qso_data.get('mode', 'ERROR')
            if isinstance(mode, (tuple, list)):
                mode = mode[0]
            self.inputCall.setText(call)
            self.set_freq(freq)
            self.get_info_from_qrz(call)
            if self.settings_dict["rigctl-enabled"] == "enable":
                self.rigctl_set_freq_to_trx(freq)
            if self.settings_dict['tci'] == 'enable':
                try:
                    tci_sndr.set_freq(freq)
                    if mode != 'ERROR':
                        tci_sndr.set_mode('0', mode)
                except Exception:
                    logger.debug("Set_freq_cluster: Can't connection to server:", self.settings_dict['tci-server'], ":",
                          self.settings_dict['tci-port'], "freq:_>", freq)

            if self.settings_dict['cat'] == 'enable':
                try:
                    logForm.cat_system.sender_cat(freq=freq, mode=mode)
                except Exception:
                    logger.debug("Can't read/write to CAT port")

    def get_current_band(self):
        return self.comboBand.currentText().strip()
    def menu(self):

        logSettingsAction = QAction('&Settings', self)
        # logSettingsAction.setStatusTip('Name, Call and other of station')
        logSettingsAction.triggered.connect(self.logSettings)
        #
        window_cluster_action = QAction('Cluster window', self)
        # windowAction.setStatusTip('Name, Call and other of station')
        window_cluster_action.triggered.connect(self.stat_cluster)
        #
        window_inet_search_action = QAction('Image window', self)
        window_inet_search_action.triggered.connect(self.stat_internet_search)
        #
        window_qth_map_action = QAction('QTH map', self)
        window_qth_map_action.triggered.connect(self.stat_qth_map)
        #
        window_repeat_qso_action = QAction('Repeats window', self)
        window_repeat_qso_action.triggered.connect(self.stat_repeat_qso)
        #
        window_cw_module = QAction("CW Machine", self)
        window_cw_module.triggered.connect(self.cw_machine_gui)
        #
        window_eqsl_inbox = QAction("Check inbox eQSL", self)
        window_eqsl_inbox.triggered.connect(self.open_eqsl_inbox)
        #
        window_form_diplom = QAction('New award', self)
        window_form_diplom.triggered.connect(self.new_diplom)

        self.profile_name = QAction("Save profile as", self)
        self.profile_name.triggered.connect(self.save_coordinate_to_new_profile)
        self.profile_save = QAction("Save profile", self)
        self.profile_save.triggered.connect(self.save_coordinate_to_profile)
        self.profile_delete = QAction("Delete profile", self)
        self.profile_delete.triggered.connect(self.delete_profile)
        self.profiles = QMenu("Profiles")
        self.profiles.setStyleSheet(
            "QWidget{font: 10px; background-color: " + self.settings_dict['background-color'] + "; color: " + self.settings_dict[
                'color'] + ";}")

        self.profiles.addAction(self.profile_name)
        self.profiles.addAction(self.profile_save)
        self.profiles.addAction(self.profile_delete)
        self.profiles.addSeparator()
        # self.profiles.addAction()
        exit_menu = QAction("Exit", self)
        exit_menu.triggered.connect(self.close)
        self.menuBarw = self.menuBar()

        self.menuBarw.setStyleSheet("QWidget{font: 12px;}")
        #  settings_menu = menuBar.addMenu('Settings')
        settingsMenu = self.menuBarw.addMenu("Menu")
        settingsMenu.addAction(logSettingsAction)
        settingsMenu.addAction(exit_menu)

        WindowMenu = self.menuBarw.addMenu('&Window')
        # WindowMenu.triggered.connect(self.logSettings)
        WindowMenu.addAction(window_cluster_action)
        WindowMenu.addAction(window_inet_search_action)
        WindowMenu.addAction(window_qth_map_action)
        WindowMenu.addAction(window_repeat_qso_action)
        WindowMenu.addAction(window_cw_module)
        WindowMenu.addAction(window_eqsl_inbox)
        ViewMenu = self.menuBarw.addMenu('&View')
        ViewMenu.setStyleSheet("QWidget{font: 12px;}")

        ViewMenu.addMenu(self.profiles)
        self.profile_update_menu()
        aboutAction = QAction('&About', self)

        aboutAction.triggered.connect(self.about_window)

        settingsMenu.addAction(aboutAction)

        if self.diploms != []:
            for i in range(len(self.diploms)):
                diplom_data = self.diploms[i].get_data()
                logger.debug("self.diplomsName:_>", diplom_data)
                if diplom_data != []:
                    self.menu_add(diplom_data[0]['name'])
        minimizeMenu = QAction("_", self)
        minimizeMenu.triggered.connect(self.showMinimized)
        closeMenu = QAction("✘", self)
        closeMenu.triggered.connect(self.close)
        tabMenu = QAction("𝑳𝓲𝓷𝓾𝔁𝑳𝓸𝓰", self)
        tabMenu.setDisabled(True)

        self.menuBarw.addAction(tabMenu)
        self.menuBarw.addAction(minimizeMenu)
        self.menuBarw.addAction(closeMenu)

    def open_eqsl_inbox(self):
        self.eqsl_inbox_window = eqsl_inbox.EqslWindow(settings_dict=self.settings_dict, db=db, log_window=logWindow)

    def profile_update_menu(self):
        try:
            profiles = json.loads(self.settings_dict["coordinate-profile"])
        except (json.JSONDecodeError, TypeError):
            profiles = []
        self.profiles.clear()
        self.profiles.addAction(self.profile_name)
        self.profiles.addAction(self.profile_save)
        self.profiles.addAction(self.profile_delete)
        self.profiles.addSeparator()
        for profile in profiles:
            name = profile.get("name")
            if not name:
                continue
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(name == self.settings_dict.get("active-profile"))
            action.triggered.connect(partial(self.set_active_profile, name))
            self.profiles.addAction(action)

    def set_active_profile(self, name):
        # logger.debug(name)
        self.settings_dict['active-profile'] = name
        # self.update_settings(self.settings_dict)
        # logger.debug("self.settings_dict['active-profile']: ", self.settings_dict['active-profile'])
        Settings_file.update_file_to_disk(self)
        self.update_cordinates()
        self.profile_update_menu()

    def delete_profile(self):
        try:
            profiles = json.loads(self.settings_dict["coordinate-profile"])
        except (json.JSONDecodeError, TypeError):
            profiles = []
        names = [p.get("name") for p in profiles if p.get("name")]
        if not names:
            return
        name, ok = QInputDialog.getItem(self, "Delete profile", "Profile:", names, 0, False)
        if not ok or not name:
            return
        profiles = [p for p in profiles if p.get("name") != name]
        json_string = json.dumps(profiles)
        self.settings_dict["coordinate-profile"] = json_string
        self.param = {"coordinate-profile": json_string, "active-profile": self.settings_dict.get("active-profile")}
        self.remember_in_cfg(self.param)
        if self.settings_dict.get("active-profile") == name:
            if profiles:
                self.settings_dict["active-profile"] = profiles[0].get("name")
            else:
                self.settings_dict["active-profile"] = ""
        Settings_file.update_file_to_disk(self)
        self.profile_update_menu()

    def menu_add(self, name_menu):
        # diplom
        # self.diplomMenu = self.awardsMenu.addMenu('&Awards')
        logger.debug('name_menu', name_menu)
#        self.item_menu = self.awardsMenu.addMenu(name_menu)
        edit_diploma = QAction('Edit ' + name_menu, self)
        edit_diploma.triggered.connect(lambda checked, name_menu=name_menu: self.edit_diplom(name_menu))
        show_stat = QAction('Show statistic', self)
        show_stat.triggered.connect(lambda checked, name_menu=name_menu: self.show_statistic_diplom(name_menu))
        del_diploma = QAction("Delete " + name_menu, self)
        del_diploma.triggered.connect(lambda checked, name_menu=name_menu: self.del_diplom(name_menu))

    def menu_rename_diplom(self):
        self.menuBarw.clear()
        # self.otherMenu.clear()

    def edit_diplom(self, name):
        all_data = ext.diplom.get_rules(f"{name}.rules")
        self.edit_window = ext.Diplom_form(settingsDict=self.settings_dict, log_form=self,
                                           adi_file=Adi_file(APP_VERSION, self.settings_dict), diplomname=name,
                                           list_data=all_data)
        self.edit_window.show()

        # logger.debug("edit_diplom:_>", name, "all_data:", all_data)

    def show_statistic_diplom(self, name):
        self.stat_diplom = ext.static_diplom(diplom_name=name, settingsDict=self.settings_dict)
        self.stat_diplom.show()
        # logger.debug("show_statistic_diplom:_>", name)

    def del_diplom(self, name):
        ext.diplom.del_dilpom(ext.diplom, name, self.settings_dict, self)
        # logger.debug("del_diplom:_>", name)

    def new_diplom(self):
        self.new_diploma = ext.Diplom_form(settingsDict=self.settings_dict, adi_file=Adi_file(APP_VERSION, self.settings_dict),
                                           log_form=logForm)

        self.new_diploma.show()

    def about_window(self):
        # logger.debug("About_window")
        pass
        about_window.show()

    def searchWindow(self):
        logSearch.hide()

    def cw_machine_gui(self):
        self.cw_machine = CW(parent_window=self, settings_dict=self.settings_dict)
        self.cw_machine.show()

    def get_call(self):
        return self.inputCall.text().strip()

    def get_rst_s(self):
        return self.inputRstS.text().strip()

    def get_rst_r(self):
        return self.inputRstR.text().strip()

    def get_name(self):
        return self.inputName.text().strip()

    def get_qth(self):
        return self.inputQth.text().strip()

    def get_mode(self):
        mode = self.mode
        return mode

    def initUI(self):
        font = QFont(self.settings_dict['font-app'], 10, QFont.Weight.Normal)

        QApplication.setFont(font)
        QApplication.setApplicationName('LinuxLog ' + APP_VERSION + ' | ' + self.settings_dict['my-call'])
        styleform = f"background-color: {self.settings_dict['form-background']}; color: {self.settings_dict['color-table']}; padding: 0em;"
        self.setGeometry(int(self.settings_dict['log-form-window-left']), int(self.settings_dict['log-form-window-top']),
                         int(self.settings_dict['log-form-window-width']), int(self.settings_dict['log-form-window-height']))
        self.setWindowTitle(f'{self.settings_dict["my-call"]} | LinuxLog {APP_VERSION}')
        self.setWindowIcon(QIcon('logo.png'))
        if self.settings_dict['border_wnd'] == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        style = f"background-color:{self.settings_dict['background-color']}; color: {self.settings_dict['color']};"
        self.setStyleSheet(style)
        self.menu()

        # self.test()
        self.labelCall = QLabel("Call")
        self.labelCall.setFont(QtGui.QFont(self.settings_dict['font-app'], 9))

        # labelCall.move(40,40)
        self.inputCall = QLineEdit()
        self.inputCall.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.inputCall.setStyleSheet(styleform)
        self.inputCall.setFixedWidth(108)
        self.inputCall.setFixedHeight(30)
        self.inputCall.textChanged[str].connect(
            self.onChanged)

        # adjust for your QLineEdit
        self.inputCall.installEventFilter(self._filter)
        self.inputCall.returnPressed.connect(
            self.logFormInput)
        # self.inputCall.tabPressed.connect(self.internetWorker.get_internet_info)
        # inputCall.move(40,40)

        self.labelRstR = QLabel('RSTr')

        self.labelRstR.setFont(QtGui.QFont(self.settings_dict['font-app'], 7))

        self.inputRstR = QLineEdit()

        self.inputRstR.setFixedWidth(35)
        self.inputRstR.setFixedHeight(35)
        self.inputRstR.setStyleSheet(styleform)

        if self.settings_dict['mode-swl'] == 'enable':
            self.inputRstR.setText('SWL')
            # fnt = self.inputRstR.font()
            # fnt.setPointSize(7)
            # self.inputRstR.setFont(fnt)
            self.inputRstR.setText('SWL')
            self.inputRstR.setEnabled(False)

        else:
            self.inputRstR.setText('59')
            self.inputRstR.setEnabled(True)

        self.inputRstR.returnPressed.connect(self.logFormInput)

        self.inputRstR.installEventFilter(self._filter)

        self.labelRstS = QLabel('RSTs')
        self.labelRstS.setFont(QtGui.QFont(self.settings_dict['font-app'], 7))
        self.inputRstS = QLineEdit("59")
        self.inputRstS.setFixedWidth(35)
        self.inputRstS.setFixedHeight(35)
        self.inputRstS.setStyleSheet(styleform)
        self.inputRstS.returnPressed.connect(self.logFormInput)

        self.labelName = QLabel('Name')
        self.labelName.setFont(QtGui.QFont(self.settings_dict['font-app'], 9))
        self.inputName = QLineEdit()
        self.inputName.setFixedWidth(137)
        self.inputName.setFixedHeight(30)
        self.inputName.setStyleSheet(styleform)
        self.inputName.returnPressed.connect(self.logFormInput)

        self.labelQth = QLabel("QTH  ")
        self.labelQth.setFixedWidth(36)
        self.labelQth.setFont(QtGui.QFont(self.settings_dict['font-app'], 9))

        self.inputQth = QLineEdit()
        self.inputQth.setFixedWidth(137)
        self.inputQth.setFixedHeight(30)
        self.inputQth.setStyleSheet(styleform)
        self.inputQth.returnPressed.connect(self.logFormInput)

        self.comboMode = QComboBox()
        self.comboMode.setFixedWidth(80)
        self.comboMode.setFixedHeight(30)
        self.comboMode.addItems(["SSB", "ESSB", "CW", "AM", "FM", "DSB", "DIGI"])
        indexMode = self.comboMode.findText(self.settings_dict['mode'])
        self.comboMode.setCurrentIndex(indexMode)
        self._mode_manually_selected = False
        self._setting_mode_programmatically = False
        self.comboMode.currentTextChanged.connect(self.changed_mode)
        #self.comboMode.
        #self.comboMode.activated[str].connect(self.rememberMode)

        self.comboBand = QComboBox()
        self.comboBand.setFixedWidth(80)
        self.comboBand.setFixedHeight(30)
        self.comboBand.addItems(["160", "80", "40", "30", "20", "17", "15", "12", "10", "6", "2", "100", "200", "GEN"])
        indexBand = self.comboBand.findText(self.settings_dict['band'])
        self.comboBand.setCurrentIndex(indexBand)
        # self.comboBand.activated[str].connect(self.rememberBand)
        self.comboBand.currentTextChanged.connect(self.changed_band)
        self.rememberBand
        # TCI label
        self.labelStatusCat = QLabel()
        self.labelStatusCat.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.labelStatusCat.setFont(QtGui.QFont('SansSerif', 7))

        # cat label
        self.labelStatusCat_cat = QLabel()
        self.labelStatusCat_cat.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.labelStatusCat_cat.setFont(QtGui.QFont('SansSerif', 7))

        # telnet label
        self.labelStatusTelnet = QLabel()
        self.labelStatusTelnet.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.labelStatusTelnet.setFont(QtGui.QFont('SansSerif', 7))

        # qrz.com label
        self.labelStatusQrzCom = QLabel()
        self.labelStatusQrzCom.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.labelStatusQrzCom.setFont(QtGui.QFont('SansSerif', 7))

        # Rigctl label
        self.labelStatusRigctl = QLabel()
        self.labelStatusRigctl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.labelStatusRigctl.setFont(QtGui.QFont('SansSerif', 7))

        # Time label
        self.labelTime = QLabel()
        self.labelTime.setFont(QtGui.QFont('SansSerif', 7))

        # Label VFO
        self.labelVfo = QLabel()
        self.labelVfo.setFont(QtGui.QFont('SansSerif', 7))

        # Label frequency
        self.labelFreq = ClikableLabel()
        self.labelFreq.setFont(QtGui.QFont('SansSerif', 7))
        self.labelFreq.setText("Freq control (F12)")
        self.labelFreq.click_signal.connect(self.freq_window)
        self.labelFreq.change_value_signal.connect(self.change_freq_event)

        # Callsign label
        self.labelMyCall = QLabel(self.settings_dict['my-call'])
        self.labelMyCall.setFont(QtGui.QFont('SansSerif', 10))

        # Comments field
        self.comments = QLineEdit()
        self.comments.setStyleSheet(styleform)
        self.comments.setPlaceholderText("Comment")
        self.comments.setFixedHeight(35)
        self.country_label = QLabel()
        self.country_label.setFixedWidth(100)
        self.country_label.setStyleSheet(style + " font-size: 12px;")
        hBoxHeader = QHBoxLayout()
        hBoxHeader.addWidget(self.labelTime)
        hBoxRst = QHBoxLayout()
        vBoxLeft = QVBoxLayout()
        vBoxRight = QVBoxLayout()
        vBoxMain = QVBoxLayout()
        # Build header line
        hBoxHeader.addStretch(20)
        hBoxHeader.addWidget(self.labelVfo)
        hBoxHeader.addWidget(self.labelFreq)
        hBoxHeader.addWidget(self.labelMyCall)

        # Build Left block
        hCall = QHBoxLayout()
        hCall.addWidget(self.labelCall)
        hCall.addWidget(self.inputCall)
        hCall.addWidget(self.country_label)
        hCall.addStretch(1)
        vBoxLeft.addLayout(hCall)

        # set label RSTr
        hBoxRst.addWidget(self.labelRstR)
        hBoxRst.addWidget(self.inputRstR)
        # set input RSTr
        hBoxRst.addWidget(self.labelRstS)
        hBoxRst.addWidget(self.inputRstS)

        # Set contorl number
        hBoxRst.addWidget(self.labelRstS)
        hBoxRst.addWidget(self.inputRstS)

        hBoxRst.addStretch(1)

        vBoxLeft.addLayout(hBoxRst)
        hName = QHBoxLayout()

        hName.addWidget(self.labelName)
        hName.addWidget(self.inputName)
        hName.addStretch(1)
        vBoxLeft.addLayout(hName)

        hQth = QHBoxLayout()
        hQth.addWidget(self.labelQth)
        hQth.addWidget(self.inputQth)
        hQth.addStretch(1)
        vBoxLeft.addLayout(hQth)

        # vBoxLeft.addWidget( labelName) #set label Name
        # vBoxLeft.addWidget( inputName) #set input Name
        # vBoxLeft.addWidget( labelQth)  #set label QTH
        # vBoxLeft.addWidget( inputQth)  #set input RSTr

        vBoxRight.addWidget(self.comboBand)
        vBoxRight.addWidget(self.comboMode)
        # vBoxRight.addWidget(self.country_label)
        vBoxRight.addStretch(1)
        # vBoxRight.addWidget(self.labelStatusCat)
        # vBoxRight.addWidget(self.labelStatusTelnet)

        leftRight = QHBoxLayout()

        leftRight.addLayout(vBoxLeft)
        leftRight.addLayout(vBoxRight)

        vBoxMain.addLayout(hBoxHeader)
        vBoxMain.addLayout(leftRight)

        hBoxStatus = QHBoxLayout()
        hBoxStatus.setAlignment(Qt.AlignmentFlag.AlignRight)
        hBoxStatus.addWidget(self.labelStatusTelnet)
        hBoxStatus.addWidget(self.labelStatusQrzCom)
        hBoxStatus.addWidget(self.labelStatusCat)
        hBoxStatus.addWidget(self.labelStatusRigctl)
        hBoxStatus.addWidget(self.labelStatusCat_cat)
        vBoxMain.addSpacing(10)
        vBoxMain.addWidget(self.comments)
        vBoxMain.addLayout(hBoxStatus)

        style = "QTextEdit{background:" + self.settings_dict['form-background'] + "; border: 1px solid " + self.settings_dict[
            'solid-color'] + ";}"
        self.comments.setStyleSheet(styleform)

        central_widget = QWidget()
        central_widget.setLayout(vBoxMain)
        self.setCentralWidget(central_widget)

        # self.show()

        # run time in Thread
        self.run_time = RealTime(logformwindow=self)  # run time in Thread
        self.run_time.real_time_signal.connect(self.set_time)
        self.run_time.start()
        self.init_data()

    @QtCore.pyqtSlot(object)
    def set_time(self, time_cortage):
        self.labelTime.setText(f"Loc: {time_cortage[0]} | GMT: {time_cortage[1]}")

    def init_data(self):
        for index_band in range(self.comboBand.count()):
            self.spot_index_by_band.update({self.comboBand.itemText(index_band): -1})
        self.sendMesageToTCI("RX_SENSORS_ENABLE:true;")
        #self.sendMesageToTCI("RX_SENSORS_ENABLE:true;")
        # for band in sf"elf.comboBand.count():
        # self.index_spot[]

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.RightButton:
            self.resize_wnd = event.pos()
            self.x = self.width()
            self.y = self.height()
            self.flag_button = "right"
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()
            self.flag_button = "left"

    def mouseMoveEvent(self, event):
        if self.flag_button == "left":
            x = int(event.globalPosition().x())
            y = int(event.globalPosition().y())
            x_w = self.offset.x()
            y_w = self.offset.y()
            self.move(x - x_w, y - y_w)
        if self.flag_button == "right":
            x_r = self.resize_wnd.x() - event.pos().x()
            y_r = self.resize_wnd.y() - event.pos().y()
            self.resize(self.x - x_r, self.y - y_r)

    def full_clear_form(self):
        self.inputCall.clear()
        if self.settings_dict['mode-swl'] == 'enable':
            self.inputRstR.setText('SWL')
            self.inputRstR.setEnabled(False)
        else:
            self.inputRstR.setText('59')
        self.inputRstS.setText('59')
        self.inputName.clear()
        self.inputQth.clear()
        self.comments.clear()
        self.country_label.clear()

    def change_freq_event(self):
        freq = self.labelFreq.text()
        # logger.debug("Change_freq_event:_>", freq)

    def freq_window(self):
        # logger.debug("Click by freq label")
        self.freq_input_window = FreqWindow(settings_dict=self.settings_dict, parent_window=self)

    def changed_band(self):
        self.comboBand.clearFocus()
        self.rememberBand(self.comboBand.currentText().strip())
    def rememberBand(self, text):
        config_store.update_settings({'band': self.comboBand.currentText().strip()})

    def changed_mode(self):
        self.comboMode.clearFocus()
        if not self._setting_mode_programmatically:
            self._mode_manually_selected = True
        self.rememberMode(self.comboMode.currentText())
        self.mode = self.comboMode.currentText()
        self.change_mode_signal.emit(self.mode)
        if self.sender is not None:
            self.sender.send_command(f"M {self.mode}")

    def rememberMode(self, text):
        config_store.update_settings({'mode': self.comboMode.currentText().strip()})

    def key_lay_reverse(self, string: str):
        '''
        This method reciev string on russian and reverse lay
        in equivalent to english keyboard lay. ЙЦУКЕН => QWERTY
        :param string: input original string
        :return:
        '''
        return str(string).translate(KEYBOARD_LAYOUT_TRANSLATION)

    def onChanged(self, text):
        '''метод который отрабатывает как только произошло изменение в поле ввода'''
        if LOWERCASE_LETTER_RE.search(text):
            self.inputCall.setText(text.upper())

        if CYRILLIC_UPPER_RE.search(text):
            self.inputCall.setText(self.key_lay_reverse(self.inputCall.text()))
            text = self.inputCall.text().strip()
        if len(text) > 2:
            country = self.get_country(text)
            if country:
                self.set_country_label(country[0] + ' <h6 style="font-size: 10px;">ITU: ' + str(country[1]) + '</h6>')
            else:
                self.set_country_label('')

        if len(text) < 2:
            self.set_country_label("")
        if len(text) >= 4:
            if not CYRILLIC_UPPER_RE.search(text) and text.isupper() and text.isalnum():
                # Debounce database and network lookups while the call is typed.
                self._pending_lookup = text
                self._lookup_timer.start()
            else:
                self._lookup_timer.stop()
                self._pending_lookup = ""
        else:
            self._lookup_timer.stop()
            self._pending_lookup = ""
            self.logSearch.clear_table()

        if len(text) == 0:
            self.logSearch.clear_table()
            publish("qth.map.update", "")
        elif len(text) >= 2:
            publish("qth.map.update", self.inputCall.text().strip())

    def _run_call_lookup(self):
        call = self._pending_lookup
        if not call or self.inputCall.text().strip() != call:
            return
        publish("qth.map.update", call)
        self.db.search_like_qsos(call)
        self.get_info_from_qrz(call)

    def update_qth_map(self, call=None, locator=None, source=None):
        """Refresh the QTH map for ``call``.

        Without an explicit locator the callsign-prefix fallback is used.
        A locator received from QRZ.com arrives later and replaces it.
        """
        map_window = getattr(self, "qth_map", None)
        call = str(call if call is not None else self.inputCall.text()).strip().upper()
        if not call:
            if map_window is not None:
                map_window.clear_station()
            return
        if locator is None:
            locator, prefix = locator_from_callsign(call)
            source = f"prefix {prefix}" if prefix else "not found"
        if map_window is not None:
            map_window.set_station(call, locator, source or "")

    def refresh_qth_map_locator(self):
        map_window = getattr(self, "qth_map", None)
        if map_window is not None:
            map_window.refresh_my_locator()

    def get_country(self, call_dark):
        call = str(call_dark or "").strip().upper()
        index = getattr(self, "_country_prefix_index", None)
        if not call or not index:
            return []
        max_length = min(len(call), getattr(self, "_country_prefix_max_length", len(call)))
        for size in range(max_length, 0, -1):
            match = index.get(call[:size])
            if match is not None:
                return list(match)
        return []

    def set_country_label(self, country):
        self.country_label.setText(country)

    def logFormInput(self):

        call = str(self.inputCall.text()).strip()

        if call != '' and len(call) >= 2:
            recordObject = {}
            mode = str(self.comboMode.currentText()).strip()
            rstR = str(self.inputRstR.text()).strip()
            rstS = str(self.inputRstS.text()).strip()
            name = str(self.inputName.text()).strip()
            qth = str(self.inputQth.text()).strip()
            operator = str(self.labelMyCall.text()).strip()
            band = str(self.comboBand.currentText()).strip() + "M"
            comment = str(self.comments.text()).strip()
            comment = comment.replace("\r", " ")
            comment = comment.replace("\n", " ")
            freq = self.get_freq()
            country_data = self.get_country(call)

            if country_data != []:
                country = country_data[0]
                itu = country_data[1]
                cq_zone = country_data[2]
            else:
                country = ""
                itu = ""
                cq_zone = ""

            datenow = datetime.datetime.now()
            date = datenow.strftime("%Y%m%d")
            time = str(strftime("%H%M%S", gmtime()))

            self.recordObject = {
                'QSO_DATE': date,
                'TIME_ON': time,
                'FREQ': freq,
                'CALL': call,
                'MODE': mode,
                'RST_RCVD': rstR,
                'RST_SENT': rstS,
                'NAME': name,
                'QTH': qth,
                'OPERATOR': operator,
                'BAND': band,
                'COMMENT': comment,
                'TIME_OFF': time,
                'COUNTRY': country,
                'ITUZ': itu,
                'EQSL_QSL_SENT': 'N',
                'CLUBLOG_QSO_UPLOAD_STATUS': 'N',
                'STATION_CALLSIGN': operator}

            logWindow.addRecord(self.recordObject)
            # Check current spot
            if self.current_spot is not None and call == self.current_spot['call']:
                self.current_spot['complete'] = 1
                self.spot_index_by_band[self.get_current_band()] -= 1

            call_dict = {'call': call, 'mode': mode, 'band': band}
            if self.settings_dict['diplom'] == 'enable':
                for diploms in self.diploms:
                    if diploms.filter(call_dict):
                        diploms.add_qso(self.recordObject)

            try:
                if self.settings_dict['tci'] == "enable":
                    tci_sndr.change_color_spot(call, freq)
            except Exception:
                logger.debug("LogFormInput:_> Can't connect to TCI server (set spot)")

            logForm.inputCall.setFocus()

            if self.settings_dict['mode-swl'] == 'enable':
                self.inputCall.clear()
                self.inputName.clear()
                self.inputQth.clear()
                self.inputRstR.setText('SWL')
                self.inputRstR.setEnabled(False)
                self.inputRstS.setText('59')
            else:
                self.inputCall.clear()
                self.inputRstS.setText('59')
                self.inputRstR.setText('59')
                self.inputName.clear()
                self.inputQth.clear()
                self.comments.clear()
            try:
                logSearch.tableWidget.clearContents()
                internetSearch.update_photo()
            except Exception:
                pass

    def changeEvent(self, event):

        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            if self.isMinimized():
                logger.debug("Minimized")
                if self.settings_dict['search-internet-window'] == 'True':
                    internetSearch.showMinimized()
                if self.settings_dict['log-search-window'] == 'True':
                    logSearch.showMinimized()
                    self.settings_dict['log-search-window'] = 'True'
                if self.settings_dict['log-window'] == 'True':
                    logWindow.showMinimized()
                    self.settings_dict['log-window'] = 'True'
                if self.settings_dict['telnet-cluster-window'] == 'True':
                    telnetCluster.showMinimized()
                    self.settings_dict['telnet-cluster-window'] = 'True'
            else:

                if self.settings_dict['search-internet-window'] == 'True':
                    internetSearch.showNormal()
                    self.settings_dict['search-internet-window'] = 'True'
                if self.settings_dict['log-search-window'] == 'True':
                    logSearch.showNormal()
                    self.settings_dict['log-search-window'] = 'True'
                if self.settings_dict['log-window'] == 'True':
                    logWindow.showNormal()
                    self.settings_dict['log-window'] = 'True'
                if self.settings_dict['telnet-cluster-window'] == 'True':
                    telnetCluster.showNormal()
                    self.settings_dict['telnet-cluster-window'] = 'True'

            QWidget.changeEvent(self, event)

    def showEvent(self, event):
        if self.settings_dict['log-window'] == 'True':
            logWindow.showNormal()

        if self.settings_dict['log-search-window'] == 'True':
            logSearch.showNormal()
        if self.settings_dict['telnet-cluster-window'] == 'True':
            telnetCluster.showNormal()
        if self.settings_dict['search-internet-window'] == 'True':
            internetSearch.showNormal()

    def closeEvent(self, event):
        '''
        This function recieve signal close() from logForm window
        Save coordinate and size all windows
        Stop real-time thread
        Close app
        '''
        eqsl_window = getattr(logForm, "eqsl_inbox_window", None)
        if eqsl_window is not None and not eqsl_window.prepare_close():
            std.std.message(
                self,
                "The eQSL request is stopping. Close the application again after it finishes.",
                "eQSL",
            )
            event.ignore()
            return
        qrz_client = getattr(logForm, "qrz_com", None)
        if qrz_client is not None and not qrz_client.stop_thread():
            std.std.message(
                self,
                "QRZ.com is still finishing its network request. Close the application again in a moment.",
                "QRZ.com",
            )
            event.ignore()
            return
        self.run_time.stop_()
        self.run_time.wait()
        if self.settings_dict.get('tci') == 'enable':
            tci_recv.stop_tci()
        tci_sndr.close()
        self.parameter = self.get_coordinate_windows()
        logWindow.close()
        internetSearch.close()
        logSearch.close()

        logForm.close()
        telnetCluster.close()
        map_window = getattr(self, "qth_map", None)
        if map_window is not None:
            if not map_window.isHidden():
                map_window._preserve_visibility_on_close = True
                self.settings_dict["qth-map-window"] = "True"
            map_window.close()
        settings_file.save_all_settings(self, self.settings_dict)
        try:
            if self.cw_machine.isVisible():
                self.settings_dict["cw"] = "True"
                self.cw_machine.close()
            else:
                logger.debug("closed CW machine")
                self.settings_dict["cw"] = "False"
                settings_file.save_all_settings(self, self.settings_dict)
        except Exception:
            ...
        try:
            if self.menu.isEnabled():
                self.menu.before_close_save()
                self.menu.close()
        except Exception:
            pass
        try:
            if self.freq_input_window.isEnabled():
                self.freq_input_window.close()
        except Exception:
            pass
        try:
            if self.eqsl_inbox_window.isEnabled():
                self.eqsl_inbox_window.close()

        except Exception:
            pass

        if about_window.isEnabled():
            about_window.close()
        self.remember_in_cfg(self.parameter)
        self.settings_dict['app'].exit(0)

    def remember_in_cfg(self, parameter):
        '''
        This function recieve Dictionary parametr with key:value
        record key=value into config.cfg

        :param parameter:
        :return:
        '''
        config_store.update_settings(parameter)

    def logSettings(self):
        # menu_window.show()
        self.menu = settings.Menu(
            db,
            app_env,
            self.settings_dict,
            telnetCluster,
            logForm,
            logSearch,
            logWindow,
            internetSearch,
            tci_recv,
            tci_sndr,
            table_columns
        )
        self.menu.show()
        # logSearch.close()

    def stat_cluster(self):

        if telnetCluster.isHidden():
            # logger.debug('statTelnet')
            telnetCluster.show()
        elif telnetCluster.isEnabled():
            telnetCluster.hide()

    def stat_internet_search(self):
        if internetSearch.isHidden():
            # logger.debug('internet_search')
            internetSearch.show()
        elif internetSearch.isEnabled():
            internetSearch.hide()

    def stat_qth_map(self):
        map_window = getattr(self, "qth_map", None)
        if map_window is None:
            return
        if map_window.isHidden():
            map_window.refresh_my_locator()
            map_window.show()
            map_window.raise_()
            map_window.activateWindow()
            self.settings_dict["qth-map-window"] = "True"
        else:
            map_window.hide()
            self.settings_dict["qth-map-window"] = "False"

    def stat_repeat_qso(self):
        if logSearch.isHidden():
            # logger.debug('internet_search')
            logSearch.show()
        elif logSearch.isEnabled():
            logSearch.hide()

    def set_band(self, band):
        # logger.debug("LogForm.set_band. input band:", band)
        indexMode = self.comboBand.findText(band)
        self.comboBand.setCurrentIndex(indexMode)

    def set_freq(self, freq):
        freq_string = "".join(ch for ch in str(freq) if ch.isdigit())
        if not freq_string:
            return
        self.labelFreq.setText("Freq: " + format_frequency_hz(freq_string))
        band = std.std().get_std_band(freq_string)

        index_band = self.comboBand.findText(band)
        if index_band >= 0:
            self.comboBand.setCurrentIndex(index_band)

        if not self._mode_manually_selected:
            planned_mode = std.std().mode_band_plan(band, freq_string)
            if isinstance(planned_mode, (tuple, list)):
                planned_mode = planned_mode[0]
            planned_mode = str(planned_mode or "").upper()
            if planned_mode == "CW":
                mode_text = "CW"
            elif planned_mode in ("USB", "LSB"):
                mode_text = "SSB"
            elif planned_mode.startswith("DIG"):
                mode_text = "DIGI"
            else:
                mode_text = None
            if mode_text:
                index_mode = self.comboMode.findText(mode_text)
                if index_mode >= 0:
                    self._setting_mode_programmatically = True
                    self.comboMode.setCurrentIndex(index_mode)
                    self._setting_mode_programmatically = False
        try:
            if self.freq_input_window.isEnabled():
                if self.settings_dict['cat'] != "enable":
                    self.freq_input_window.set_freq(freq_string)
        except Exception:
            pass

    def set_vfo(self, vfo_str):
        self.labelVfo.setText(str(vfo_str).upper())
    def set_freq_for_cat(self, freq):

        try:
            self.cat_system.sender_cat(freq=freq)
        except Exception:
            logger.debug("Can't set frequency by CAT")

    def set_call(self, call):
        self.inputCall.setText(str(call))

    def _apply_radio_mode(self, mode_input):
        """Select the log-form mode matching a rig/TCI reported mode."""
        mode = str(mode_input).strip().lower()
        mode_string = RADIO_MODE_ALIASES.get(mode, "SSB")
        index_mode = self.comboMode.findText(mode_string)
        if index_mode >= 0:
            self.comboMode.setCurrentIndex(index_mode)
        self.mode = mode
        try:
            self.cw_machine.set_mode()
        except Exception:
            pass

    def set_mode_rigctl(self, mode_input):
        self._apply_radio_mode(mode_input)

    def set_mode_tci(self, mode_input):
        self._apply_radio_mode(mode_input)

    def set_tci_stat(self, values, color="#57BD79"):
        self.labelStatusCat.setStyleSheet("color: " + color + "; font-weight: bold;")
        self.labelStatusCat.setText(values)


    def set_tci_label_found(self, values=''):
        self.labelStatusCat.setStyleSheet("color: #FF6C49; font-weight: bold;")
        self.labelStatusCat.setText("TCI Found " + values)
        QTimer.singleShot(550, lambda: self.labelStatusCat.setText(""))

    def set_rigctl_stat(self, values: str="· Rigctl", color="#57BD79"):
        self.labelStatusRigctl.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.labelStatusRigctl.setText("· Rigctl")

    # telnet label sets
    def set_telnet_stat(self, text=None, color="#58BD79"):
        self.labelStatusTelnet.setStyleSheet(f"color: {color}; font-weight: bold;")
        if text is None:
            self.labelStatusTelnet.setText("· Telnet")
        else:
            self.labelStatusTelnet.setText(text)
        QTimer.singleShot(150, self._reset_telnet_label)

    def _reset_telnet_label(self):
        self.labelStatusTelnet.setStyleSheet("color: #aaaaaa; font-weight: bold;")
        self.labelStatusTelnet.setText("· Telnet")

    def set_telnet_wrong(self, text=None):
        self.labelStatusTelnet.setStyleSheet("color: #8a2222; font-weight: bold;")
        self.labelStatusTelnet.setText(text)

    def set_qrz_com_stat(self, text=None):
        self.labelStatusQrzCom.setStyleSheet("color: #58BD79; font-weight: bold;")
        if text is None:
            self.labelStatusQrzCom.setText("· qrz.com")
        else:
            self.labelStatusQrzCom.setText(text)

    def set_qrz_com_wrong(self, text=None):
        self.labelStatusQrzCom.setStyleSheet("color: #8a2222; font-weight: bold;")
        self.labelStatusQrzCom.setText(text)

    def set_cat_label(self, flag: bool):
        if flag:
            self.labelStatusCat_cat.setStyleSheet("font-weight: bold; color: #57BD79;")
            self.labelStatusCat_cat.setText('·CAT')
        else:
            self.labelStatusCat_cat.setStyleSheet("font-weight: bold; color: #FF6C49;")
            self.labelStatusCat_cat.setText('')

    def get_band(self):
        return self.comboBand.currentText()

    def get_freq(self):
        freq_string = self.labelFreq.text().replace('Freq: ', '').replace('.', '')
        if freq_string.isdigit():
            return freq_string
        band = self.get_band()
        default_freq = BAND_FREQUENCIES_HZ.get(band)
        return str(default_freq) if default_freq else 'non'

    def refresh_interface(self):
        self.setGeometry(int(self.settings_dict['log-form-window-left']), int(self.settings_dict['log-form-window-top']),
                         int(self.settings_dict['log-form-window-width']), int(self.settings_dict['log-form-window-height']))
        self.labelMyCall.setText(self.settings_dict['my-call'])
        self.country_dict = self.get_country_dict()
        self._build_country_prefix_index()
        self.profile_update_menu()
        # Connecting to qrz.com
        self._configure_qrz_com()

        # SWL mode
        if self.settings_dict['mode-swl'] == 'enable':
            self.inputRstR.setText("SWL")
            self.inputRstR.setEnabled(False)
        else:
            self.inputRstR.setText("59")
            self.inputRstR.setEnabled(True)
        self.update_color_schemes()
        try:
            if self.freq_input_window.isEnabled():
                self.freq_input_window.refresh_interface()
        except Exception:
            pass
        # logger.debug("setingsDict['cat']:_>", self.settings_dict['cat'])
        if self.settings_dict['cat'] == "enable":
            try:
                self.start_cat()
            except Exception:
                logger.debug("Can't start CAT interface (maybe incorrect port)")
        else:
            try:
                self.stop_cat()
            except Exception:
                logger.debug("Can't stop CAT interface (maybe it not start)")

    def update_color_schemes(self):
        style = "background-color:" + self.settings_dict['background-color'] + "; color:" + \
                self.settings_dict['color'] + ";"
        self.labelCall.setStyleSheet(style)
        self.labelRstR.setStyleSheet(style)
        self.labelRstS.setStyleSheet(style)
        self.labelName.setStyleSheet(style)
        self.labelQth.setStyleSheet(style)
        self.labelTime.setStyleSheet(style)
        self.labelFreq.setStyleSheet(style)
        self.labelMyCall.setStyleSheet(style)
        self.comboMode.setStyleSheet(style)
        self.comboBand.setStyleSheet(style)
        self.labelStatusCat.setStyleSheet(style)
        style_form = "background-color:" + self.settings_dict['form-background'] + "; color:" + self.settings_dict[
            'color-table'] + "; font: 12px"
        self.inputCall.setStyleSheet(style_form)
        self.inputRstR.setStyleSheet(style_form)
        self.inputRstS.setStyleSheet(style_form)
        self.inputName.setStyleSheet(style_form)
        self.inputQth.setStyleSheet(style_form)
        self.comments.setStyleSheet(style_form)

        self.setStyleSheet(style)

    def update_settings(self, new_settings_dict):
        self.settings_dict.update(new_settings_dict)

    def diploms_init(self):
        self.diplomsList = []
        self.diploms = self.get_diploms()
        for diplom in self.diploms:
            if diplom.get_data() != []:
                self.diplomsList.append(ext.Diplom(diplom.get_data()[0]['name'], self.settings_dict))
            else:
                pass

    def diplomsCheck(self):
        for i, diplom in enumerate(self.diplomsList):
            if diplom.complete():
                std.std.message(self, diplom.name+" is completed", "Good")
            # print ("diplom.get_data()['call']", diplom.get_data()[0]['call'])
            # qsoByPatern = Db(self.settings_dict).getQsoByCallPattern(diplom.get_data()[i]['call'])
            # logger.debug("qso by patern:",qsoByPatern )
            # diplom.filter({'call'})
        # logger.debug("*" * 10)
        # temp = self.diplomsName[0]
        # logger.debug(temp.get_rules(temp.))
        # logger.debug("*" * 10)

    def get_diploms(self):
        diploms = []
        if self.settings_dict['diploms-json'] != '':
            rulesObject = json.loads(self.settings_dict['diploms-json'])
            for i in range(len(rulesObject)):
                rulesObject[i]['name_programm'] = ext.diplom(rulesObject[i]['name_programm'] + ".adi",
                                                             rulesObject[i]['name_programm'] + ".rules",
                                                             self.settings_dict)
                diploms.append(rulesObject[i]['name_programm'])
        return diploms


class CW(QWidget):
    def __init__(self, parent_window, settings_dict):
        super().__init__()
        self.parent_window = parent_window
        self.settings_dict = settings_dict
        self.mode = self.parent_window.get_mode()
        self.initUI()
        self.parent_window.change_mode_signal.connect(self.update_mod)

    def initUI(self):
        if settingsDict['cw-top'] == "":
            desktop = QApplication.primaryScreen().availableGeometry()
            # self.setGeometry(100,100,210,100)
            width_coordinate = (desktop.width() / 2) - 100
            height_coordinate = (desktop.height() / 2) - 100
            # self.setWindowModified(False)
            # self.setFixedHeight(270)
            # self.setFixedWidth(320)
            width = 400
            height = 220
        else:
            width_coordinate = self.settings_dict['cw-left']
            height_coordinate = self.settings_dict['cw-top']
            width = self.settings_dict['cw-width']
            height = self.settings_dict['cw-height']
        self.style = "background-color:" + settingsDict['background-color'] + "; color:" + settingsDict[
            'color'] + ";"
        self.style_table = "background-color:" + settingsDict['form-background'] + "; color:" + settingsDict[
            'color-table'] + "; font: 12px;  gridline-color: " + settingsDict['solid-color'] + ";"

        self.setGeometry(int(width_coordinate), int(height_coordinate), int(width), int(height))
        self.setStyleSheet(self.style)
        self.cq_button_1 = QPushButton("CQ")
        # self.cq_button_1.setStyleSheet(self.parent_window.)
        self.cq_button_1.setFixedWidth(30)
        self.cq_button_1.setFixedHeight(30)
        self.cq_button_1.clicked.connect(self.send_cw)
        self.cq_button_1.setStyleSheet(self.style)
        self.cq_line_edit_1 = QLineEdit()
        self.cq_line_edit_1.setStyleSheet(self.style_table)
        self.cq_line_edit_1.setFixedHeight(30)
        self.cq_line_edit_1.setText(settingsDict['cw-cq-string'])
        self.cq_line = QHBoxLayout()
        self.cq_line.addWidget(self.cq_button_1)
        self.cq_line.addWidget(self.cq_line_edit_1)

        self.answer_button_1 = QPushButton("1")
        # self.cq_button_1.setStyleSheet(self.parent_window.)
        self.answer_button_1.setFixedWidth(30)
        self.answer_button_1.setFixedHeight(30)
        self.answer_button_1.setStyleSheet(self.style)
        self.answer_button_1.clicked.connect(self.send_cw)
        self.answer_line_edit_1 = QLineEdit()
        self.answer_line_edit_1.setStyleSheet(self.style_table)
        self.answer_line_edit_1.setFixedHeight(30)
        self.answer_line_edit_1.setText(settingsDict['cw-answer-string'])
        self.answer_line = QHBoxLayout()
        self.answer_line.addWidget(self.answer_button_1)
        self.answer_line.addWidget(self.answer_line_edit_1)

        self.final_button_1 = QPushButton("2")
        # self.cq_button_1.setStyleSheet(self.parent_window.)
        self.final_button_1.setFixedWidth(30)
        self.final_button_1.setFixedHeight(30)
        self.final_button_1.setStyleSheet(self.style)
        self.final_button_1.clicked.connect(self.send_cw)
        self.final_line_edit_1 = QLineEdit()
        self.final_line_edit_1.setStyleSheet(self.style_table)
        self.final_line_edit_1.setFixedHeight(30)
        self.final_line_edit_1.setText(settingsDict['cw-final-string'])
        self.final_line = QHBoxLayout()
        self.final_line.addWidget(self.final_button_1)
        self.final_line.addWidget(self.final_line_edit_1)

        self.wpm_linedit = QLineEdit()
        self.wpm_linedit.setFixedHeight(20)
        self.wpm_linedit.setFixedWidth(30)
        self.wpm_linedit.setStyleSheet(self.style_table)
        self.wpm_linedit.setText(self.settings_dict['wpm'])
        self.wpm_button = QPushButton("Set")
        self.wpm_button.setFixedWidth(30)
        self.wpm_button.setFixedHeight(20)
        self.wpm_button.setStyleSheet(self.style + " font-size: 10px;")
        self.wpm_button.clicked.connect(self.change_status)
        self.wpm_label = QLabel("WPM")
        self.wpm_label.setFixedWidth(30)
        self.wpm_label.setStyleSheet(self.style + " font-size: 10px;")
        self.wpm_lay = QHBoxLayout()
        self.wpm_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.wpm_lay.addWidget(self.wpm_label)
        self.wpm_lay.addSpacing(7)
        self.wpm_lay.addWidget(self.wpm_linedit)
        self.wpm_lay.addSpacing(5)
        self.wpm_lay.addWidget(self.wpm_button)

        self.user_button_1 = QPushButton("3")
        self.user_button_1.setFixedWidth(30)
        self.user_button_1.setFixedHeight(30)
        self.user_button_1.setStyleSheet(self.style)
        self.user_button_1.clicked.connect(self.send_cw)
        self.user_line_edit_1 = QLineEdit()
        self.user_line_edit_1.setStyleSheet(self.style_table)
        self.user_line_edit_1.setFixedHeight(30)
        self.user_line_edit_1.setText(settingsDict['cw-user-string1'])
        self.user_line_1 = QHBoxLayout()
        self.user_line_1.addWidget(self.user_button_1)
        self.user_line_1.addWidget(self.user_line_edit_1)

        self.user_button_2 = QPushButton("4")
        self.user_button_2.setFixedWidth(30)
        self.user_button_2.setFixedHeight(30)
        self.user_button_2.setStyleSheet(self.style)
        self.user_button_2.clicked.connect(self.send_cw)
        self.user_line_edit_2 = QLineEdit()
        self.user_line_edit_2.setStyleSheet(self.style_table)
        self.user_line_edit_2.setFixedHeight(30)
        self.user_line_edit_2.setText(settingsDict['cw-user-string2'])
        self.user_line_2 = QHBoxLayout()
        self.user_line_2.addWidget(self.user_button_2)
        self.user_line_2.addWidget(self.user_line_edit_2)

        self.status_label = QLabel()
        self.status_label.setFixedHeight(10)
        self.status_label.setStyleSheet(self.style + " font-size: 10px;")
        self.set_status(self.wpm_linedit.text().strip())
        self.status_lay = QHBoxLayout()
        self.status_lay.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_lay.addSpacing(15)
        self.status_lay.addWidget(self.status_label)

        self.stop_button = QPushButton("STOP TX")
        self.stop_button.setStyleSheet(self.style + " font-size: 10px;")
        # self.stop_button.siz
        self.stop_button.setFixedHeight(30)

        self.stop_button.clicked.connect(self.send_cw)
        self.mode_label = QLabel()
        self.mode_label.setStyleSheet(self.style + " font-size: 10px;")

        self.stop_lay = QHBoxLayout()

        self.stop_lay.addWidget(self.mode_label)
        self.stop_lay.addSpacing(20)
        self.stop_lay.addWidget(self.stop_button)

        self.comand_lay = QHBoxLayout()
        self.comand_lay.setSpacing(0)
        self.comand_lay.addLayout(self.wpm_lay)
        self.comand_lay.addLayout(self.stop_lay)
        self.comand_lay.addLayout(self.status_lay)
        self.v_lay = QVBoxLayout()
        self.v_lay.addLayout(self.comand_lay)
        self.v_lay.addLayout(self.cq_line)
        self.v_lay.addLayout(self.answer_line)
        self.v_lay.addLayout(self.final_line)
        self.v_lay.addLayout(self.user_line_1)
        self.v_lay.addLayout(self.user_line_2)

        self.setLayout(self.v_lay)
        self.set_mode()
    @QtCore.pyqtSlot(str)
    def update_mod(self):
        logger.debug("update mod")
        self.set_mode()

    def set_mode(self):
        self.mode = self.parent_window.get_mode()
        logger.debug(self.mode)
        if self.mode == "CW":
            self.mode_label.setStyleSheet(self.style + " font-size: 10px; font-weight: bold; color: #337733;")
            self.enabled_control(True)
        else:
            self.mode_label.setStyleSheet(self.style + " font-size: 10px; color: #774444;")
            self.enabled_control(False)
        self.mode_label.setText("Mode: " + str(self.mode).upper())

    def enabled_control(self, enable_flag: bool):
        self.answer_button_1.setEnabled(enable_flag)
        self.cq_button_1.setEnabled(enable_flag)
        self.final_button_1.setEnabled(enable_flag)
        self.stop_button.setEnabled(enable_flag)
        self.user_button_1.setEnabled(enable_flag)
        self.user_button_2.setEnabled(enable_flag)

    def set_wpm_speed(self, wpm):
        self.wpm_speed = wpm

    def set_tx_stat(self):
        self.stop_button.setStyleSheet(
            self.style + " font-size: 12px; background: #883333; color: #ffffff; font-color: bold;")

    def reset(self):
        self.cq_button_1.setStyleSheet(self.style + " font-size: 12px;")
        self.answer_button_1.setStyleSheet(self.style + " font-size: 12px;")
        self.final_button_1.setStyleSheet(self.style + " font-size: 12px;")
        self.user_button_1.setStyleSheet(self.style + " font-size: 12px;")
        self.user_button_2.setStyleSheet(self.style + " font-size: 12px;")
        self.stop_button.setStyleSheet(self.style + " font-size: 12px;")

    def get_cw_macros_string(self, text):
        string_list = text.split("%")
        output_string = ""
        for elem in string_list:
            if elem == "OPERATOR":
                output_string = output_string + self.settings_dict['my-call']
            elif elem == "CALL":
                output_string = output_string + self.parent_window.get_call()
            elif elem == "NAME":
                output_string = output_string + self.parent_window.get_name()
            elif elem == "RST_S":
                output_string = output_string + self.parent_window.get_rst_s()
            elif elem == "RST_R":
                output_string = output_string + self.parent_window.get_rst_r()
            elif elem == "QTH":
                output_string = output_string + self.parent_window.get_qth()
            elif elem == "MY-NAME":
                output_string = output_string + self.settings_dict['my-name']
            elif elem == "MY-QTH":
                output_string = output_string + self.settings_dict['my-qth']

            else:
                output_string = output_string + elem
        return output_string

    def send_cw(self):

        button = self.sender()

        if self.mode == "cw":
            if button.text() == "CQ":
                button.setStyleSheet(
                    self.style + " font-size: 12px; background: #337733; color: #ffffff; font-color: bold;")
                # logger.debug("send_CQ_cw")
                string = self.cq_line_edit_1.text()
                string_tci = self.get_cw_macros_string(string)
                # logger.debug(string_tci)
                tci_sndr.send_command("cw_macros:0," + string_tci + ";")

            if button.text() == "1":
                button.setStyleSheet(
                    self.style + " font-size: 12px; background: #337733; color: #ffffff; font-color: bold;")
                # logger.debug("send_1_cw")
                string = self.answer_line_edit_1.text()
                string_tci = self.get_cw_macros_string(string)
                logger.debug(string_tci)
                tci_sndr.send_command("cw_macros:0," + string_tci + ";")
            if button.text() == "2":
                button.setStyleSheet(
                    self.style + " font-size: 12px; background: #337733; color: #ffffff; font-color: bold;")
                # logger.debug("send_2_cw")
                string = self.final_line_edit_1.text()
                string_tci = self.get_cw_macros_string(string)
                logger.debug(string_tci)
                tci_sndr.send_command("cw_macros:0," + string_tci + ";")
            if button.text() == "3":
                button.setStyleSheet(
                    self.style + " font-size: 12px; background: #337733; color: #ffffff; font-color: bold;")
                logger.debug("send_3_cw")
                string = self.user_line_edit_1.text()
                string_tci = self.get_cw_macros_string(string)
                logger.debug(string_tci)
                tci_sndr.send_command("cw_macros:0," + string_tci + ";")
            if button.text() == "4":
                button.setStyleSheet(
                    self.style + " font-size: 12px; background: #337733; color: #ffffff; font-color: bold;")
                logger.debug("send_4_cw")
                string = self.user_line_edit_2.text()
                string_tci = self.get_cw_macros_string(string)
                logger.debug(string_tci)
                tci_sndr.send_command("cw_macros:0," + string_tci + ";")
            if button.text() == "STOP TX":
                button.setStyleSheet(self.style)
                tci_sndr.send_command("cw_macros_stop;")
        else:
            pass
            # self.set_mode(self.mode)

    def before_close_save(self):
        self.settings_dict['cw-cq-string'] = self.cq_line_edit_1.text().strip()
        self.settings_dict['cw-answer-string'] = self.answer_line_edit_1.text().strip()
        self.settings_dict['cw-final-string'] = self.final_line_edit_1.text().strip()
        self.settings_dict['cw-user-string1'] = self.user_line_edit_1.text().strip()
        self.settings_dict['cw-user-string2'] = self.user_line_edit_2.text().strip()
        self.settings_dict['cw-left'] = str(self.geometry().left())
        self.settings_dict['cw-top'] = str(self.geometry().top())
        self.settings_dict['cw-width'] = str(self.geometry().width())
        self.settings_dict['cw-height'] = str(self.geometry().height())
        #self.settings_dict['cw'] = "False"
        settings_file.save_all_settings(self, self.settings_dict)

    def closeEvent(self, event):
        self.before_close_save()
        event.accept()

    def change_status(self):
        self.settings_dict['wpm'] = self.wpm_linedit.text().strip()
        tci_sndr.send_command("CW_MACROS_SPEED:" + self.settings_dict['wpm'] + ";")
        self.set_status(self.wpm_linedit.text().strip())
        settings_file.save_all_settings(self, self.settings_dict)

    def set_status(self, text):
        self.status_label.setText("WPM set: " + text)
        self.wpm_speed = text


class TelnetCluster(QWidget):
    _beep_wave = None
    _BEEP_RETRY_MS = 60_000

    def __init__(self, settings_dict=None):
        super().__init__()
        # self.mainwindow = mainwindow
        # self.log_form = log_form
        self.settings_dict = settings_dict if settings_dict is not None else globals().get("settingsDict", {})
        self.host = self.settings_dict['telnet-host']
        self.port = self.settings_dict['telnet-port']
        self.call = self.settings_dict['my-call']
        self.tableWidget = QTableWidget()
        self.allRows = 0
        self.all_spots = []
        self._beep_enabled = self.settings_dict.get("cluster-beep-enabled", "enable") == "enable"
        self._beep_available = True
        self._beep_warning_shown = False
        self._beep_filter_enabled = False
        self._beep_filter_band = ""
        self._beep_filter_mode = ""
        self._beep_filter_call = ""
        self.run_cluster = ClusterThread(settings_dict=self.settings_dict, parent=self)
        try:
            from services.qso_repository import QsoRepository
            self.db = QsoRepository(self.settings_dict)
        except Exception:
            self.db = None
        self.initUI()

    def initUI(self):
        """
        Design of cluster window
        """

        self.setGeometry(int(self.settings_dict['telnet-cluster-window-left']),
                         int(self.settings_dict['telnet-cluster-window-top']),
                         int(self.settings_dict['telnet-cluster-window-width']),
                         int(self.settings_dict['telnet-cluster-window-height']))
        # Allow narrowing the cluster window; Qt's default minimum size is
        # too large for small screens.
        self.setMinimumSize(0, 0)
        self.setWindowTitle('Telnet cluster')
        self.setWindowIcon(QIcon('logo.png'))
        if self.settings_dict['border_wnd'] == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(float(self.settings_dict['clusterWindow-opacity']))
        style = "background-color:" + self.settings_dict['background-color'] + "; color:" + self.settings_dict[
            'color'] + ";"
        self.setStyleSheet(style)
        self.labelIonosphereStat = QLabel()
        self.labelIonosphereStat.setMinimumWidth(0)
        self.labelIonosphereStat.setFixedHeight(10)
        self.labelIonosphereStat.setStyleSheet("font: 8px;")
        # self.labelIonosphereStat.setText("A=12, K=23, F=21, No storm, no storm")
        style_table = "background-color:" + self.settings_dict['form-background'] + "; color:" + self.settings_dict[
            'color-table'] + "; font: 12px;  gridline-color: " + self.settings_dict['solid-color'] + ";"
        self.tableWidget.setStyleSheet("QWidget {" + style_table + "}")
        fnt = self.tableWidget.font()
        fnt.setPointSize(9)
        self.tableWidget.setFont(fnt)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setMinimumSize(0, 0)
        self.tableWidget.setHorizontalHeaderLabels(["Time Loc", "Time GMT", "Call", "Freq", " Spot"])
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.cellClicked.connect(self.click_to_spot)
        # Beep switch and beeper filter
        button_style = "font-size: 9px;"
        self.sound_button = QPushButton("Beep: ON" if self._beep_enabled else "Beep: OFF")
        self.sound_button.setCheckable(True)
        self.sound_button.setChecked(self._beep_enabled)
        self.sound_button.setMinimumWidth(60)
        self.sound_button.setFixedHeight(18)
        self.sound_button.setStyleSheet(button_style)
        self.sound_button.setToolTip("Enable or disable cluster spot beeps")
        self.sound_button.toggled.connect(self.set_cluster_sound)
        self.sound_button.setStyleSheet(
            "font-size: 9px; background-color: " + ("#2e7d32" if self._beep_enabled else "#7f1d1d") + "; color: white;"
        )

        self.beep_filter_button = QPushButton("Beep filter: OFF")
        self.beep_filter_button.setMinimumWidth(60)
        self.beep_filter_button.setFixedHeight(18)
        self.beep_filter_button.setStyleSheet(button_style)
        self.beep_filter_button.setToolTip("Configure the optional beeper filter")
        self.beep_filter_button.clicked.connect(self.open_beep_filter)

        filter_enabled = self.settings_dict.get("cluster-filter-enabled") == "enable"
        self.filter_button = QPushButton("Filter: " + ("ON" if filter_enabled else "OFF"))
        self.filter_button.setCheckable(True)
        self.filter_button.setChecked(filter_enabled)
        self.filter_button.setMinimumWidth(60)
        self.filter_button.setFixedHeight(18)
        self.filter_button.setStyleSheet(button_style)
        self.filter_button.setToolTip("Filter cluster spots")
        self.filter_button.clicked.connect(self.open_cluster_filter)
        self.filter_button.setStyleSheet(
            "font-size: 9px; background-color: " + ("#2e7d32" if filter_enabled else "#555555") + "; color: white;"
        )

        self.server_button = QPushButton("Server")
        self.server_button.setMinimumWidth(60)
        self.server_button.setFixedHeight(18)
        self.server_button.setStyleSheet(button_style)
        self.server_button.setToolTip("Cluster server settings")
        self.server_button.clicked.connect(self.open_server_settings)
        self.server_button.setStyleSheet(
            "font-size: 9px; background-color: "
            + ("#2e7d32" if self.settings_dict.get("cluster-connection-enabled", "enable") == "enable" else "#7f1d1d")
            + "; color: white;"
        )

        self.beep_buttons_lay = QHBoxLayout()
        self.beep_buttons_lay.setSpacing(4)
        self.beep_buttons_lay.addWidget(self.server_button)
        self.beep_buttons_lay.addWidget(self.filter_button)
        self.beep_buttons_lay.addWidget(self.beep_filter_button)
        self.beep_buttons_lay.addWidget(self.sound_button)

        self.cluster_top_lay = QHBoxLayout()
        self.cluster_top_lay.addWidget(self.labelIonosphereStat)
        self.cluster_top_lay.addStretch()
        self.cluster_top_lay.addLayout(self.beep_buttons_lay)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(3)
        self.layout.addLayout(self.cluster_top_lay)
        self.layout.addWidget(self.tableWidget)

        # Text area communicate
        self.textarea = QPlainTextEdit()
        self.textarea.setStyleSheet("QWidget {" + style_table + "}")

        # Command input
        self.command_input = QLineEdit()
        self.command_input.setStyleSheet("QWidget {" + style_table + "}")
        # self.command_input.setFixedWidth(250)

        # Command button
        self.command_button = QPushButton("Send")
        self.command_button.clicked.connect(self.send_to_telnet_cluster)
        self.command_button.setFixedWidth(40)
        # self.command_button.setFixedHeight(13)

        # Command layer
        self.command_lay = QHBoxLayout()
        self.command_lay.addWidget(self.command_input)
        self.command_lay.addWidget(self.command_button)

        # Comunicate layer
        self.communicate_lay = QVBoxLayout()
        self.communicate_lay.addWidget(self.textarea)
        self.communicate_lay.addLayout(self.command_lay)

        # Cluster main widget
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.layout)

        # Cluster comunicate widget
        self.comunicate_widget = QWidget()
        self.comunicate_widget.setLayout(self.communicate_lay)

        # Tabs
        # Cluster tab
        self.cluster_tab = QTabWidget()
        self.cluster_tab.setMovable(False)
        # Setup cluster tab
        self.cluster_tab.addTab(self.main_widget, "Cluster")
        # Setup comunicate tab
        self.cluster_tab.addTab(self.comunicate_widget, "Cluster console")

        # Main layer to tab
        self.main_lay = QVBoxLayout()
        self.main_lay.addWidget(self.cluster_tab)
        self.setLayout(self.main_lay)
        if self.settings_dict.get("cluster-connection-enabled", "enable") == "enable":
            self.start_cluster()

    def set_telnet_wrong(self, text):
        logForm.set_telnet_wrong(text)

    def set_telnet_stat(self):
        logForm.set_telnet_stat()

    def send_to_telnet_cluster(self):
        if self.command_input.text() in ("", " "):
            return None
        command = self.command_input.text().strip()
        try:
            self.run_cluster.send_to_telnet(command)
        except (OSError, ConnectionError, UnicodeError):
            self.set_telnet_wrong(text="· Telnet")
            return
        self.textarea.appendPlainText(command)
        self.command_input.clear()

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.RightButton:
            self.resize_wnd = event.pos()
            self.x = self.width()
            self.y = self.height()
            self.flag_button = "right"
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()
            self.flag_button = "left"


        logger.debug(event.button())

    def mouseMoveEvent(self, event):
        if self.flag_button == "left":
            x = int(event.globalPosition().x())
            y = int(event.globalPosition().y())
            x_w = self.offset.x()
            y_w = self.offset.y()
            self.move(x - x_w, y - y_w)
        if self.flag_button == "right":
            # x = self.width()
            # y = self.height()
            x_r = self.resize_wnd.x() - event.pos().x()
            y_r = self.resize_wnd.y() - event.pos().y()
            logger.debug(event.globalPosition().y(), x_r, self.resize_wnd.x())
            self.resize(self.x - x_r, self.y - y_r)

    def parsing_telnet_string(self, telnet_string):
        if not isinstance(telnet_string, str):
            return None
        cleaned = telnet_string.replace("\x07", "").strip()
        if not cleaned.upper().startswith("DX"):
            return None

        elem_string_list = cleaned.split()
        if len(elem_string_list) < 4:
            return None
        try:
            call_position = int(self.settings_dict['telnet-call-position'])
            freq_position = int(self.settings_dict['telnet-freq-position'])
        except (KeyError, TypeError, ValueError):
            call_position, freq_position = 4, 3

        standart_lib = std.std()
        freq = ""
        if 0 <= freq_position < len(elem_string_list):
            freq = standart_lib.std_freq(elem_string_list[freq_position])
        if not freq:
            # The configured columns may not match this cluster's format.
            # Find the first token that looks like a frequency instead.
            for index, token in enumerate(elem_string_list[2:], start=2):
                candidate = standart_lib.std_freq(token)
                if candidate:
                    freq = candidate
                    freq_position = index
                    break

        if not (0 <= call_position < len(elem_string_list)):
            call_position = freq_position + 1
        if not (0 <= call_position < len(elem_string_list)):
            return None

        call = elem_string_list[call_position].strip().rstrip(":")
        if not call:
            return None

        band = standart_lib.get_std_band(freq)
        mode = standart_lib.mode_band_plan(band, freq)
        if isinstance(mode, (tuple, list)):
            mode = mode[0]
        comment = " ".join(elem_string_list[call_position + 1:])
        de = elem_string_list[2].rstrip(":") if len(elem_string_list) > 2 else ""
        return {
            "call": call,
            "freq": freq,
            "band": band,
            "mode": mode,
            "complete": 0,
            "comment": comment,
            "de": de,
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
        }

    def add_row_to_cluster(self, string_from_telnet, spot_dict=None):
        if not isinstance(string_from_telnet, str):
            return
        cleaned_string = string_from_telnet.replace("\x07", "").strip()
        if not cleaned_string.upper().startswith("DX"):
            if cleaned_string.upper().startswith("WWV"):
                self.labelIonosphereStat.setText(
                    "Propagination info: " + cleaned_string
                )
            return
        if spot_dict is None:
            spot_dict = self.parsing_telnet_string(cleaned_string)
        if (
            spot_dict is None
            or not spot_dict.get("call")
            or not spot_dict.get("freq")
            or not self.cluster_filter(spot_dict)
        ):
            return

        table = self.tableWidget
        last_row = table.rowCount()
        clean_string = cleaned_string
        call_dict = {'call': spot_dict["call"].strip(), 'mode': 'cluster', 'band': 'cluster'}
        search_in_diplom_rules_flag = False
        color = None
        for diplom in getattr(logForm, "diploms", ()):
            if diplom.filter(call_dict):
                color = diplom.get_color_bg()
                search_in_diplom_rules_flag = True

        try:
            spot_call = str(spot_dict.get("call") or "").strip().upper()
            spot_locator = locator_from_callsign(spot_call)[0] if spot_call else ""
            worked = False
            if spot_call and getattr(self, "db", None) is not None:
                try:
                    worked = bool(self.db.search_qso_in_base(spot_call))
                except Exception:
                    worked = False
            qth_map_window = getattr(logForm, "qth_map", None) if "logForm" in globals() else None
            if qth_map_window is not None and hasattr(qth_map_window, "map"):
                qth_map_window.map.add_cluster_spot(spot_call, spot_locator, worked, spot_dict.get("freq", ""))
        except Exception:
            pass

        table.insertRow(last_row)
        table.setItem(last_row, 0, QTableWidgetItem(strftime("%H:%M:%S", localtime())))
        table.setItem(last_row, 1, QTableWidgetItem(strftime("%H:%M:%S", gmtime())))
        table.setItem(last_row, 2, QTableWidgetItem(spot_dict["call"]))
        table.setItem(last_row, 3, QTableWidgetItem(format_frequency_hz(spot_dict["freq"])))
        table.setItem(last_row, 4, QTableWidgetItem(clean_string))
        table.scrollToBottom()
        for col in range(table.columnCount()):
            item = table.item(last_row, col)
            if item is None:
                continue
            if search_in_diplom_rules_flag and color is not None:
                item.setBackground(color)
            else:
                item.setForeground(QColor(self.settings_dict["color-table"]))

        # Fit columns and the new row to their content.  Resizing only the
        # row that was just inserted keeps this cheap while the table grows.
        table.resizeColumnsToContents()
        table.resizeRowToContents(last_row)

        if self.settings_dict['spot-to-pan'] == 'enable' and self.settings_dict['tci'] == 'enable':
            try:
                tci_sndr.set_spot(spot_dict["call"], spot_dict["freq"], color="19711680")
            except Exception:
                logger.debug("clusterThread: Except in Tci_sender.set_spot", traceback.format_exc())

    @QtCore.pyqtSlot(object)
    def add_spot_to_table(self, string_from_telnet: object):
        try:
            spot_dict = self.parsing_telnet_string(string_from_telnet)
        except Exception:
            logger.debug("cluster: failed to parse spot", traceback.format_exc())
            return
        if spot_dict is not None:
            self.all_spots.append(spot_dict)
        self.add_row_to_cluster(string_from_telnet, spot_dict)
        if (
            self._beep_filter_enabled
            and spot_dict is not None
            and spot_dict.get("freq")
            and self.cluster_filter(spot_dict)
            and self.beep_filter_matches(spot_dict)
        ):
            self.beeper()

    @QtCore.pyqtSlot(object)
    def communicate_out(self, telnet_string):
        if isinstance(telnet_string, bytes):
            text = telnet_string.decode(self.settings_dict["encodeStandart"], errors="ignore")
        else:
            text = str(telnet_string)
        if text.strip() and text.strip() != "DX":
            self.textarea.appendPlainText(text)

    def add_new_spot(self, string_from_telnet):
        spot_dict = self.parsing_telnet_string(string_from_telnet)
        if spot_dict is not None:
            self.all_spots.append(spot_dict)

    def get_all_spots(self):
        return self.all_spots

    def stop_cluster(self):
        self.run_cluster.stop()
        if self.run_cluster.isRunning():
            self.run_cluster.wait(4000)
        self.set_telnet_wrong(text="· Telnet")

    def closeEvent(self, event):
        self.settings_dict["cluster-beep-enabled"] = "enable" if self._beep_enabled else "disable"
        self.stop_cluster()
        if self.run_cluster.isRunning():
            self.run_cluster.wait(4000)
        event.accept()

    def start_cluster(self):
        if not getattr(self, "_cluster_signals_connected", False):
            self.run_cluster.reciev_spot_signal.connect(self.add_spot_to_table)
            self.run_cluster.bell_bell_signal.connect(self.beep_for_spot)
            self.run_cluster.reciev_string_signal.connect(self.communicate_out)
            self.run_cluster.connected_signal.connect(self.set_telnet_stat)
            self.run_cluster.disconnected_signal.connect(self.cluster_disconnected)
            self._cluster_signals_connected = True
        if not self.run_cluster.isRunning():
            self.run_cluster.start()

    @QtCore.pyqtSlot()
    def open_beep_filter(self):
        """Open the optional beeper filter settings."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Beeper filter")
        dialog.setMinimumWidth(330)
        dialog_layout = QVBoxLayout(dialog)

        enabled_box = QCheckBox("Enable beeper filter")
        enabled_box.setChecked(self._beep_filter_enabled)
        dialog_layout.addWidget(enabled_box)

        form = QFormLayout()
        band_input = QLineEdit(self._beep_filter_band)
        band_input.setPlaceholderText("20 or 20,40,15")
        mode_input = QComboBox()
        mode_input.setEditable(True)
        mode_input.addItems(["", "CW", "SSB", "DIGI", "USB", "LSB", "AM", "FM"])
        mode_input.setCurrentText(self._beep_filter_mode)
        call_input = QLineEdit(self._beep_filter_call)
        call_input.setPlaceholderText("e.g. DL or DL1BCL")
        form.addRow("Band:", band_input)
        form.addRow("Mode:", mode_input)
        form.addRow("Callsign/prefix:", call_input)
        dialog_layout.addLayout(form)

        hint = QLabel("Leave a field empty to ignore it. Separate multiple values with commas.")
        hint.setWordWrap(True)
        dialog_layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._beep_filter_band = band_input.text().strip()
        self._beep_filter_mode = mode_input.currentText().strip()
        self._beep_filter_call = call_input.text().strip()
        self._beep_filter_enabled = enabled_box.isChecked()
        if self._beep_filter_enabled and not any(
            (self._beep_filter_band, self._beep_filter_mode, self._beep_filter_call)
        ):
            self._beep_filter_enabled = False
            QMessageBox.information(
                self,
                "Beeper filter",
                "Set at least one filter value, or leave the filter disabled.",
            )
        self._update_beep_filter_button()

    def open_cluster_filter(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Cluster filter")
        dialog.setMinimumWidth(360)
        dialog_layout = QVBoxLayout(dialog)

        enabled_box = QCheckBox("Enable filter")
        enabled_box.setChecked(self.settings_dict.get("cluster-filter-enabled") == "enable")
        dialog_layout.addWidget(enabled_box)

        form = QFormLayout()
        call_input = QLineEdit(self.settings_dict.get("cluster-filter-call", ""))
        call_input.setPlaceholderText("prefix, e.g. DL or UR")
        band_input = QLineEdit(self.settings_dict.get("cluster-filter-band", ""))
        band_input.setPlaceholderText("20 or 20,40")
        mode_input = QComboBox()
        mode_input.setEditable(True)
        mode_input.addItems(["", "CW", "SSB", "DIGI", "USB", "LSB", "AM", "FM"])
        mode_input.setCurrentText(self.settings_dict.get("cluster-filter-mode", ""))
        presence_input = QComboBox()
        presence_input.addItems(["All", "Worked", "Not worked"])
        presence_value = self.settings_dict.get("cluster-filter-presence", "all")
        presence_map = {"all": 0, "in_base": 1, "not_in_base": 2}
        presence_input.setCurrentIndex(presence_map.get(presence_value, 0))

        form.addRow("Callsign prefix:", call_input)
        form.addRow("Band:", band_input)
        form.addRow("Mode:", mode_input)
        form.addRow("Worked:", presence_input)
        dialog_layout.addLayout(form)

        hint = QLabel("Leave a field empty to ignore it. Separate multiple values with commas.")
        hint.setWordWrap(True)
        dialog_layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.filter_button.setChecked(self.settings_dict.get("cluster-filter-enabled") == "enable")
            self.filter_button.setText("Filter: " + ("ON" if self.settings_dict.get("cluster-filter-enabled") == "enable" else "OFF"))
            return

        enabled = enabled_box.isChecked()
        self.settings_dict["cluster-filter-enabled"] = "enable" if enabled else "disable"
        self.settings_dict["cluster-filter-call"] = call_input.text().strip()
        self.settings_dict["cluster-filter-band"] = band_input.text().strip()
        self.settings_dict["cluster-filter-mode"] = mode_input.currentText().strip()
        presence_values = ["all", "in_base", "not_in_base"]
        self.settings_dict["cluster-filter-presence"] = presence_values[presence_input.currentIndex()]

        if enabled and not any(
            (
                self.settings_dict["cluster-filter-call"],
                self.settings_dict["cluster-filter-band"],
                self.settings_dict["cluster-filter-mode"],
                self.settings_dict["cluster-filter-presence"] != "all",
            )
        ):
            self.settings_dict["cluster-filter-enabled"] = "disable"
            enabled = False
            QMessageBox.information(
                self,
                "Cluster filter",
                "Set at least one filter value, or leave the filter disabled.",
            )

        self.filter_button.setChecked(enabled)
        self.filter_button.setText("Filter: " + ("ON" if enabled else "OFF"))
        self.filter_button.setStyleSheet(
            "font-size: 9px; background-color: " + ("#2e7d32" if enabled else "#555555") + "; color: white;"
        )

    def open_server_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Cluster server")
        dialog.setMinimumWidth(320)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        host_input = QLineEdit(self.settings_dict.get("telnet-host", ""))
        port_input = QLineEdit(str(self.settings_dict.get("telnet-port", "")))
        form.addRow("Server address:", host_input)
        form.addRow("Server port:", port_input)
        layout.addLayout(form)

        enabled_box = QCheckBox("Activate connection")
        enabled_box.setChecked(self.settings_dict.get("cluster-connection-enabled", "enable") == "enable")
        layout.addWidget(enabled_box)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        host = host_input.text().strip()
        port = port_input.text().strip()
        if host:
            self.settings_dict["telnet-host"] = host
            self.host = host
        if port:
            self.settings_dict["telnet-port"] = port
            self.port = port
        if getattr(self, "run_cluster", None) is not None:
            self.run_cluster.host = self.host
            try:
                self.run_cluster.port = int(self.port)
            except (TypeError, ValueError):
                pass
        enabled = enabled_box.isChecked()
        self.settings_dict["cluster-connection-enabled"] = "enable" if enabled else "disable"
        self.server_button.setStyleSheet(
            "font-size: 9px; background-color: " + ("#2e7d32" if enabled else "#7f1d1d") + "; color: white;"
        )

        if enabled:
            if not self.run_cluster.isRunning():
                self.run_cluster = ClusterThread(settings_dict=self.settings_dict, parent=self)
                self.start_cluster()
        else:
            self.stop_cluster()

    def _update_beep_filter_button(self):
        if not self._beep_filter_enabled:
            self.beep_filter_button.setText("Beep filter: OFF")
            self.beep_filter_button.setToolTip("Beeper filter is disabled")
            return
        criteria = [
            value
            for value in (
                self._beep_filter_band,
                self._beep_filter_mode,
                self._beep_filter_call,
            )
            if value
        ]
        self.beep_filter_button.setText("Beep filter: ON")
        self.beep_filter_button.setToolTip("Beeper filter: " + ", ".join(criteria))

    @staticmethod
    def _beep_band_matches(spot_band, filter_value):
        wanted = set()
        for part in _csv_list(filter_value):
            part = part.strip().upper()
            if part.endswith("M") and part[:-1].isdigit():
                part = part[:-1]
            wanted.add(part)
        return not wanted or str(spot_band).strip().upper() in wanted

    @staticmethod
    def _beep_mode_matches(spot_mode, filter_value):
        requested_modes = [part.strip().upper() for part in _csv_list(filter_value)]
        if not requested_modes:
            return True

        spot = str(spot_mode).strip().upper()
        digital_spot_modes = {"DIGU", "DIGL", "DIGI", "DATA"}
        digital_filter_names = {
            "DIGI", "DATA", "FT8", "FT4", "RTTY", "PSK", "PSK31",
            "JS8", "OLIVIA", "JT65", "JT9", "MSK144", "WSPR",
        }
        for requested in requested_modes:
            if spot == requested:
                return True
            if requested == "SSB" and spot in {"USB", "LSB", "SSB"}:
                return True
            if requested in {"PHONE", "PH"} and spot in {"USB", "LSB", "SSB", "AM", "FM"}:
                return True
            if requested in digital_filter_names and spot in digital_spot_modes:
                return True
            if requested == "USB" and spot == "SSB":
                return True
            if requested == "LSB" and spot == "SSB":
                return True
        return False

    @staticmethod
    def _beep_call_matches(spot_call, filter_value):
        prefixes = [
            part.strip().upper().rstrip("*")
            for part in _csv_list(filter_value)
            if part.strip()
        ]
        if not prefixes:
            return True
        call = str(spot_call).strip().upper()
        return any(call.startswith(prefix) for prefix in prefixes)

    def beep_filter_matches(self, spot):
        if not self._beep_filter_enabled:
            return True
        if self._beep_filter_band and not self._beep_band_matches(
            spot.get("band", ""), self._beep_filter_band
        ):
            return False
        if self._beep_filter_mode and not self._beep_mode_matches(
            spot.get("mode", ""), self._beep_filter_mode
        ):
            return False
        if self._beep_filter_call and not self._beep_call_matches(
            spot.get("call", ""), self._beep_filter_call
        ):
            return False
        return True

    @QtCore.pyqtSlot(object)
    def beep_for_spot(self, telnet_string=None):
        # With the filter enabled, beeps are produced for every matching
        # spot in add_spot_to_table(); keep the cluster BEL for the normal,
        # unfiltered mode only so a spot never beeps twice.
        if self._beep_filter_enabled:
            return
        try:
            spot = self.parsing_telnet_string(telnet_string) if telnet_string else None
        except Exception:
            spot = None
        if not isinstance(spot, dict) or not spot.get("call") or not spot.get("freq"):
            return
        # Beep only for spots that pass the cluster filter.
        if not self.cluster_filter(spot):
            return
        frequency = self.beep_frequency_for_spot(telnet_string)
        self.beeper(frequency)

    def beep_frequency_for_spot(self, telnet_string=None):
        """Map the spot distance to a beep frequency (250..4000 Hz)."""
        my_locator = normalize_locator(self.settings_dict.get("my-qth-locator", ""))
        call = ""
        try:
            parsed = self.parsing_telnet_string(telnet_string) if telnet_string else None
            if isinstance(parsed, dict):
                call = str(parsed.get("call") or "").strip()
        except Exception:
            call = ""
        station_locator = normalize_locator(locator_from_callsign(call)[0] if call else "")
        if not my_locator or not station_locator:
            return 700
        try:
            my_lat, my_lon = locator_to_latlon(my_locator)
            station_lat, station_lon = locator_to_latlon(station_locator)
            distance = distance_km(my_lat, my_lon, station_lat, station_lon)
        except (TypeError, ValueError):
            return 700
        # 0 km -> 250 Hz, 20000 km -> 4000 Hz.
        ratio = min(1.0, max(0.0, distance / 20000.0))
        return int(250 + ratio * (4000 - 250))

    @QtCore.pyqtSlot(bool)
    def set_cluster_sound(self, enabled):
        self._beep_enabled = bool(enabled)
        self.sound_button.setText("Beep: ON" if self._beep_enabled else "Beep: OFF")
        self.sound_button.setStyleSheet(
            "font-size: 9px; background-color: " + ("#2e7d32" if self._beep_enabled else "#7f1d1d") + "; color: white;"
        )
        self.settings_dict["cluster-beep-enabled"] = "enable" if self._beep_enabled else "disable"
        if self._beep_enabled:
            # Allow an immediate retry after an audio-device failure.
            self._beep_available = True
            self._beep_warning_shown = False

    @QtCore.pyqtSlot()
    def beeper(self, frequency=700):
        if not self._beep_enabled or not self._beep_available:
            return
        frequency = int(frequency or 700)
        if frequency < 250:
            frequency = 250
        if frequency > 4000:
            frequency = 4000
        duration = 0.2  # секунд
        sample_rate = 44100
        cache = self.__class__._beep_wave
        if not isinstance(cache, dict):
            cache = {}
            self.__class__._beep_wave = cache
        wave = cache.get(frequency)
        if wave is None:
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            wave = np.sin(2 * np.pi * frequency * t)
            cache[frequency] = wave
        try:
            sd.play(wave, sample_rate)
            sd.wait()
        except Exception as error:
            # An unavailable/closed audio device must not crash the whole
            # application.  Pause beeps briefly and retry later while the
            # user's Beep switch stays in its current state.
            self._beep_available = False
            if not self._beep_warning_shown:
                logger.debug(f"Cluster beep paused: {error}")
                self._beep_warning_shown = True
            QTimer.singleShot(self._BEEP_RETRY_MS, self._enable_beeper)

    @QtCore.pyqtSlot()
    def _enable_beeper(self):
        self._beep_available = True

    @QtCore.pyqtSlot()
    def cluster_disconnected(self):
        self.set_telnet_wrong(text="· Telnet")

    def click_to_spot(self):
        item = self.tableWidget.currentItem()
        if item is None:
            return
        row = item.row()
        freq_item = self.tableWidget.item(row, 3)
        call_item = self.tableWidget.item(row, 2)
        if freq_item is None or call_item is None:
            return
        raw_freq = freq_item.text()
        call = call_item.text()
        self.img_search = internetworker.internetWorker(window=internetSearch, settings=self.settings_dict)
        self.img_search.set_callsign_for_search(callsign=call)
        self.img_search.start()
        freq = std.std().std_freq(raw_freq)
        band = std.std().get_std_band(freq)
        mode = std.std().mode_band_plan(band, freq)
        if isinstance(mode, (tuple, list)):
            mode = mode[0]
        complete = 1 if db.search_qso_in_base(call) else 0
        spot = {"call": call,
                "freq": freq,
                "band": band,
                "mode": mode,
                "complete": complete,
                "comment": ""}
        logForm.set_freq(freq)
        logForm.set_call(call=call)
        logForm.set_current_spot(spot)
        logForm.activateWindow()

        if self.settings_dict['tci'] == 'enable':
            try:
                tci_sndr.set_freq(freq)
                if mode != 'ERROR':
                    tci_sndr.set_mode('0', mode)
            except Exception:
                logger.debug("Set_freq_cluster: Can't connection to server:", self.settings_dict['tci-server'], ":",
                      self.settings_dict['tci-port'], "freq:_>", freq)

        if self.settings_dict['cat'] == 'enable':
            try:
                logForm.cat_system.sender_cat(freq=freq, mode=mode)
            except Exception:
                logger.debug("Can't read/write to CAT port")

        if self.settings_dict["rigctl-enabled"] == "enable":
            logForm.rigctl_set_freq_to_trx(freq)



    def cluster_filter(self, spot):
        if self.settings_dict.get("cluster-filter-enabled") != "enable":
            return True
        call = str(spot.get("call", "")).upper()
        band = str(spot.get("band", "")).upper()
        mode = str(spot.get("mode", "")).upper()

        prefix = self.settings_dict.get("cluster-filter-call", "").strip().upper()
        if prefix and not call.startswith(prefix):
            return False

        bands = [item.strip().upper() for item in self.settings_dict.get("cluster-filter-band", "").split(",") if item.strip()]
        if bands and band not in bands:
            return False

        modes = [item.strip().upper() for item in self.settings_dict.get("cluster-filter-mode", "").split(",") if item.strip()]
        if modes and mode not in modes:
            return False

        presence = self.settings_dict.get("cluster-filter-presence", "all")
        if presence in ("in_base", "not_in_base"):
            in_base = False
            try:
                if self.db is not None:
                    in_base = bool(self.db.search_qso_in_base(call))
            except Exception:
                in_base = False
            if presence == "in_base" and not in_base:
                return False
            if presence == "not_in_base" and in_base:
                return False
        return True

    def changeEvent(self, event):

        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            if self.isMinimized():
                self.settings_dict['telnet-cluster-window'] = 'False'
                logger.debug("telnet-cluster-window: changeEvent:_>", self.settings_dict['telnet-cluster-window'])
                # telnetCluster.showMinimized()
            elif self.isVisible():
                self.settings_dict['telnet-cluster-window'] = 'True'
                logger.debug("telnet-cluster-window: changeEvent:_>", self.settings_dict['telnet-cluster-window'])

            QWidget.changeEvent(self, event)

    def refresh_interface(self):
        self.setGeometry(int(self.settings_dict['telnet-cluster-window-left']),
                         int(self.settings_dict['telnet-cluster-window-top']),
                         int(self.settings_dict['telnet-cluster-window-width']),
                         int(self.settings_dict['telnet-cluster-window-height']))

        self.update_color_schemes()

    def update_color_schemes(self):
        style = "background-color:" + self.settings_dict['background-color'] + "; color:" + \
                self.settings_dict['color'] + ";"
        self.labelIonosphereStat.setStyleSheet(style)
        style_form = "background-color:" + self.settings_dict['form-background'] + "; color:" + self.settings_dict[
            'color-table'] + "; font: 12px;  gridline-color: " + self.settings_dict['solid-color'] + ";"
        self.tableWidget.setStyleSheet(style_form)
        color = QColor(self.settings_dict['color-table'])
        rows = self.tableWidget.rowCount()
        cols = self.tableWidget.columnCount()
        for row in range(rows):
            for col in range(cols):
                item = self.tableWidget.item(row, col)
                if item is not None:
                    item.setForeground(color)

        self.setStyleSheet(style)


class InternetSearch(QWidget):

    def __init__(self, settings_dict=None):
        super().__init__()
        self.settings_dict = settings_dict if settings_dict is not None else globals().get("self.settings_dict", {})
        self.labelImage = QLabel(self)
        # self.pixmap=""
        self.initUI()

    def initUI(self):
        self.hbox = QHBoxLayout(self)
        self.hbox.setContentsMargins(26, 18, 10, 10)
        self.pixmap = QPixmap(f"{Path(__file__).parent}/logo.png")
        self.labelImage = QLabel(self)
        self.labelImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.labelImage.setPixmap(self.pixmap)
        self.hbox.addWidget(self.labelImage)
        self.setLayout(self.hbox)

        # self.move(100, 200)
        self.setGeometry(int(self.settings_dict['search-internet-left']),
                         int(self.settings_dict['search-internet-top']),
                         int(self.settings_dict['search-internet-width']),
                         int(self.settings_dict['search-internet-height']))
        self.setWindowIcon(QIcon(f"{Path(__file__).parent}/logo.png"))
        self.setWindowTitle('Image from internet')
        if self.settings_dict['border_wnd'] == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(float(self.settings_dict['searchInetWindow-opacity']))
        style = "QWidget{background-color:" + self.settings_dict['background-color'] + "; color:" + self.settings_dict[
            'color'] + ";}"
        self.setStyleSheet(style)
        # self.show()

    @QtCore.pyqtSlot(str)
    def set_image_path(self, image_path):
        if image_path is None:
            image_path = Path(__file__).parent/"logo.png"
        pixmap = QPixmap(image_path)
        width = max(1, int(self.settings_dict['search-internet-width']) - 36)
        height = max(1, int(self.settings_dict['search-internet-height']) - 28)
        self.labelImage.setPixmap(
            pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)
        )

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.RightButton:
            self.resize_wnd = event.pos()
            self.x = self.width()
            self.y = self.height()
            self.flag_button = "right"
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()
            self.flag_button = "left"


        logger.debug(event.button())

    def mouseMoveEvent(self, event):
        if self.flag_button == "left":
            x = int(event.globalPosition().x())
            y = int(event.globalPosition().y())
            x_w = self.offset.x()
            y_w = self.offset.y()
            self.move(x - x_w, y - y_w)
        if self.flag_button == "right":
            # x = self.width()
            # y = self.height()
            x_r = self.resize_wnd.x() - event.pos().x()
            y_r = self.resize_wnd.y() - event.pos().y()
            logger.debug(event.globalPosition().y(), x_r, self.resize_wnd.x())
            self.resize(self.x - x_r, self.y - y_r)

    def changeEvent(self, event):

        # if event.type() == QtCore.QEvent.WindowStateChange:
        #   if self.isMinimized():
        # self.settings_dict['search-internet-window'] = 'False'
        #       logger.debug("search-internet-window: changeEvent:_>", self.settings_dict['search-internet-window'])
        # telnetCluster.showMinimized()
        #   elif self.isVisible():
        # self.settings_dict['search-internet-window'] = 'True'
        #       logger.debug("search-internet-window: changeEvent:_>", self.settings_dict['search-internet-window'])

        QWidget.changeEvent(self, event)

    def update_photo(self):
        pixmap = QPixmap(Path(__file__).parent/"logo.png")

        # self.labelImage.setFixedWidth(self.settings['image-width'])
        self.labelImage.setPixmap(pixmap)

    def refresh_interface(self):
        self.setGeometry(int(self.settings_dict['search-internet-left']),
                         int(self.settings_dict['search-internet-top']),
                         int(self.settings_dict['search-internet-width']),
                         int(self.settings_dict['search-internet-height']))

        self.update_color_schemes()

    def update_color_schemes(self):
        style = "background-color:" + self.settings_dict['background-color'] + "; color:" + \
                self.settings_dict['color'] + ";"
        self.labelImage.setStyleSheet(style)
        self.setStyleSheet(style)


class hello_window(QWidget):

    def __init__(self, table_columns):
        super().__init__()
        self.table_columns = table_columns
        self.initUI()

    def initUI(self):
        self.style_form = "background-color: " + settingsDict['form-background'] + "; color: " + settingsDict[
            'color-table'] + ";"
        desktop = QApplication.primaryScreen().availableGeometry()
        width_coordinate = (desktop.width() / 2) - 200
        height_coordinate = (desktop.height() / 2) - 125
        # logger.debug("hello_window: ", desktop.width(), width_coordinate)

        self.setGeometry(round(width_coordinate), round(height_coordinate), 400, 250)
        self.setWindowIcon(QIcon('logo.png'))
        self.setWindowTitle('Welcome to LinLog')
        style = "background-color:" + settingsDict['background-color'] + "; color:" + settingsDict[
            'color'] + ";"
        self.setStyleSheet(style)
        style_caption = "background-color:" + settingsDict['background-color'] + "; color:" + settingsDict[
            'color'] + "; font-size: 36px;"
        self.caption_label = QLabel("Hi friend")
        self.caption_label.setStyleSheet(style_caption)
        style_text = "background-color:" + settingsDict['background-color'] + "; color:" + settingsDict[
            'color'] + "; font-size: 12px;"
        self.welcome_text_label = QLabel("It's first runing.\nPlease enter you callsign")
        self.welcome_text_label.setStyleSheet(style_text)
        self.call_input = QLineEdit()
        self.call_input.setStyleSheet(self.style_form)
        self.call_input.setFixedWidth(150)
        self.ok_button = QPushButton("GO")
        self.ok_button.clicked.connect(self.ok_button_push)
        vbox = QVBoxLayout()
        vbox.addWidget(self.caption_label)
        vbox.addWidget(self.welcome_text_label)
        vbox.addWidget(self.call_input)
        vbox.addWidget(self.ok_button)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setLayout(vbox)
        self.show()

    def ok_button_push(self):
        callsign = self.call_input.text().strip().upper()
        if len(callsign) < 3:
            self.call_input.setStyleSheet(self.style_form)
            Messages("Oops!", "Please enter correct HAM callsign")
            self.welcome_text_label.setText("Please enter you callsign")
            return

        db_name = str(settingsDict.get('db-name') or '').strip() or 'linuxlog'
        settingsDict['db-name'] = db_name
        settingsDict['my-call'] = callsign
        try:
            database = Db(settingsDict)
            if not database.check_database(db_name):
                database.create_database()
            if not database.check_table(callsign):
                database.create_table(callsign, self.table_columns)
            settings_file.save_all_settings(self, settingsDict)
        except (OSError, pymysql.MySQLError, ValueError) as error:
            Messages("DB ERROR", f"Unable to set up the logbook database: {error}")
            return

        self.close()
        _run_project_script("main.py")
        raise SystemExit(0)


class settings_file:

    def save_all_settings(self, settingsDict):
        result = config_store.update_settings(settingsDict)
        # New settings must also be written for users whose settings.cfg was
        # created by an older version of the application.
        config_store.ensure_settings({
            'my-qth-locator': settingsDict.get('my-qth-locator', ''),
            'qth-map-window': settingsDict.get('qth-map-window', 'False'),
            'qth-map-window-left': settingsDict.get('qth-map-window-left', '100'),
            'qth-map-window-top': settingsDict.get('qth-map-window-top', '100'),
            'qth-map-window-width': settingsDict.get('qth-map-window-width', '900'),
            'qth-map-window-height': settingsDict.get('qth-map-window-height', '520'),
            'cluster-connection-enabled': settingsDict.get('cluster-connection-enabled', 'enable'),
            'cluster-filter-enabled': settingsDict.get('cluster-filter-enabled', 'disable'),
            'cluster-filter-call': settingsDict.get('cluster-filter-call', ''),
            'cluster-filter-band': settingsDict.get('cluster-filter-band', ''),
            'cluster-filter-mode': settingsDict.get('cluster-filter-mode', ''),
            'cluster-filter-presence': settingsDict.get('cluster-filter-presence', 'all'),
            'theme': settingsDict.get('theme', 'Dark'),
            'cluster-beep-enabled': settingsDict.get('cluster-beep-enabled', 'enable'),
        })
        return result


class ReadStringDb(QThread):
    records_from_base = pyqtSignal(object)
    fill_complite = pyqtSignal()

    def __init__(self, db, parent):
        super().__init__(parent)
        self.parent = parent
        self.db = db

    def run(self):
        try:
            try:
                self.parent.allRows = self.db.count_records()
            except Exception:
                self.parent.allRows = 0
            chunk = []
            for record in self.db.iter_all_records(0):
                chunk.append(record)
                if len(chunk) >= 200:
                    self.records_from_base.emit(chunk)
                    chunk = []
            if chunk:
                self.records_from_base.emit(chunk)
        finally:
            # Re-enable the table even if loading failed.
            self.fill_complite.emit()


class FoundThread(QThread):

    result = QtCore.pyqtSignal(object)

    def __init__(self, connection=None, query=None, parameters=None, connection_factory=None):
        super().__init__()
        self.sql_query_list = []
        self.connection = connection
        self.connection_factory = connection_factory
        self.query = query
        self.parameters = parameters or ()

    def add_to_stack(self, sql_query):
        self.sql_query_list.append(sql_query)

    def run(self):
        connection = self.connection_factory() if self.connection_factory else self.connection
        try:
            with connection.cursor() as cursor:
                cursor.execute(self.query, self.parameters)
                records_dict = cursor.fetchall()
            self.result.emit(records_dict)
        finally:
            if self.connection_factory:
                connection.close()

class Db(QObject):

    search_in_db_like_signal = pyqtSignal(object)
    def __init__(self, settingsDict, db_name='', db_charset='utf8mb4', first_run=False):
        super().__init__()

        self.db_host = settingsDict['db-host']
        self.db_user = settingsDict['db-user']
        self.db_pass = settingsDict['db-pass']
        self.db_name = settingsDict['db-name']
        self.db_charset = settingsDict['db-charset']
        self.settingsDict = settingsDict
        self.possible_search_qso_in_base = True
        self.main_connection = None
        self.connection = None
        self.connect_to_sql = None
        if first_run:
            self.create_database()
        # self.db_conn =
        # logger.debug("Create and run FoundThread")

    @staticmethod
    def quote_identifier(identifier):
        """Quote a MySQL identifier (table/column/database name) safely."""
        identifier = str(identifier)
        if not identifier or "\x00" in identifier:
            raise ValueError("Database identifiers must be non-empty and contain no NUL bytes")
        return "`" + identifier.replace("`", "``") + "`"

    def qso_table(self):
        return self.quote_identifier(self.settingsDict['my-call'])


    def connection_sql(self):
        self.main_connection = pymysql.connect(
            host=self.db_host,
            user=self.db_user,
            password=self.db_pass,
            db=self.db_name,
            charset=self.db_charset,
            cursorclass=DictCursor
        )

    def delete_all_qso(self):
        query_string = f"DELETE FROM {self.qso_table()}"
        sql_connect = self.connect_sql()
        try:
            with sql_connect.cursor() as query:
                query.execute(query_string)
                deleted_count = query.rowcount
            sql_connect.commit()
            return deleted_count
        except Exception:
            sql_connect.rollback()
            raise
        finally:
            sql_connect.close()

    def getQsoByCallPattern(self, patern):
        connection = self.connect_sql()
        try:
            with connection.cursor() as query:
                query.execute(f"SELECT * FROM {self.qso_table()} WHERE `call` LIKE %s", (patern,))
                return query.fetchall()
        finally:
            connection.close()

    def getRange(self, start_id, step):
        db_conn = self.connect_sql()
        try:
            with db_conn.cursor() as query:
                query.execute(
                    f"SELECT * FROM {self.qso_table()} WHERE `id` < %s ORDER BY `id` DESC LIMIT %s",
                    (int(start_id), max(0, int(step))),
                )
                return query.fetchall()
        finally:
            db_conn.close()

    def check_database(self, name_db):
        connection = None
        try:
            connection = pymysql.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_pass,
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                    (name_db,),
                )
                answer = cursor.fetchall()

        except pymysql.MySQLError as error:
            logger.debug(f"MySQL connection failed: {error}")
            _run_project_script("help_system.py", 'db-error')
            raise SystemExit(1)
        finally:
            if connection is not None:
                connection.close()

        return answer

    def create_database(self):

        db_connect_new = pymysql.connect(
            host=self.db_host,
            user=self.db_user,
            password=self.db_pass,

        )
        try:
            with db_connect_new.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.quote_identifier(self.db_name)}")
        finally:
            db_connect_new.close()

    def connect_sql(self):
        connection_options = {
            "host": self.db_host,
            "user": self.db_user,
            "password": self.db_pass,
        }
        if self.db_name:
            connection_options.update({
                "db": self.db_name,
                "charset": self.db_charset,
                "cursorclass": DictCursor,
            })

        try:
            self.connection = pymysql.connect(**connection_options)
        except pymysql.MySQLError as error:
            logger.debug(f"MySQL connection failed: {error}")
            _run_project_script("help_system.py", 'db-error')
            raise SystemExit(1)
        return self.connection

    def create_table(self, name_table, column_list):
        charset = str(self.db_charset)
        if not re.fullmatch(r"[A-Za-z0-9_]+", charset):
            raise ValueError("Invalid database character set")
        column_definitions = ["`id` INT NOT NULL AUTO_INCREMENT"]
        for column in column_list:
            if not isinstance(column, (list, tuple)) or len(column) != 2:
                raise ValueError("Each database column must have a name and a type")
            column_name, column_type = column
            column_type = str(column_type).upper()
            if not re.fullmatch(r"(?:VARCHAR\([1-9][0-9]{0,3}\)|DATE|TIME)", column_type):
                raise ValueError(f"Unsupported database column type: {column_type}")
            column_definitions.append(f"{self.quote_identifier(column_name)} {column_type}")
        sql_query = (
            f"CREATE TABLE {self.quote_identifier(name_table)} "
            f"({', '.join(column_definitions)}, PRIMARY KEY (`id`)) CHARACTER SET {charset}"
        )
        db_conn = self.connect_sql()
        try:
            with db_conn.cursor() as query:
                query.execute(sql_query)
            db_conn.commit()
            return True
        finally:
            db_conn.close()

    def record_qso_to_base(self, qso_dict, mode=''):
        def field_value(name, limit=None):
            value = str(qso_dict.get(name) or '').strip()
            return value[:limit] if limit is not None else value

        raw_time_on = field_value('TIME_ON')
        time_on = parse.normalize_adi_time(raw_time_on)
        if raw_time_on and not time_on:
            raise ValueError(f"Invalid TIME_ON value: {raw_time_on!r}")

        raw_time_off = field_value('TIME_OFF')
        time_off = parse.normalize_adi_time(raw_time_off)
        if raw_time_off and not time_off:
            raise ValueError(f"Invalid TIME_OFF value: {raw_time_off!r}")

        # MySQL TIME accepts HHMMSS; keep NULL when the time is absent.
        time_format = time_on or None
        time_off_format = time_off or time_format

        raw_date = field_value('QSO_DATE')
        qso_date = parse.normalize_adi_date(raw_date)
        if raw_date and not qso_date:
            raise ValueError(f"Invalid QSO_DATE value: {raw_date!r}")
        if qso_date:
            qso_date = f'{qso_date[:4]}-{qso_date[4:6]}-{qso_date[6:]}'
        else:
            qso_date = None

        operator = field_value('OPERATOR') or self.settingsDict['my-call']
        station_call = field_value('STATION_CALLSIGN')
        if station_call:
            operator = station_call
        limits = mode == 'import'
        frequency = field_value('FREQ')
        if limits and frequency:
            # ADIF FREQ is expressed in MHz; the application stores radio
            # frequencies in Hz. Preserve malformed legacy values unchanged.
            frequency_hz = std.std().std_freq(frequency)
            if frequency_hz:
                frequency = frequency_hz
        values = (
            field_value('CALL', 50 if limits else None),
            field_value('MODE', 50 if limits else None),
            field_value('NAME', 50 if limits else None),
            qso_date,
            time_format,
            time_off_format,
            field_value('QTH', 50 if limits else None),
            field_value('RST_RCVD', 50 if limits else None),
            field_value('RST_SENT', 50 if limits else None),
            operator.strip(),
            field_value('COMMENT', 500 if limits else None),
            field_value('EQSL_QSL_SENT'),
            field_value('CLUBLOG_QSO_UPLOAD_STATUS'),
            frequency,
            field_value('BAND'),
            field_value('ITUZ'),
        )
        insert_sql = (
            f"INSERT INTO {self.qso_table()} (`CALL`, `MODE`, `NAME`, `QSO_DATE`, `TIME_ON`, `TIME_OFF`, `QTH`, "
            "`RST_RCVD`, `RST_SENT`, `OPERATOR`, `COMMENT`, `EQSL_QSL_SENT`, `CLUBLOG_QSO_UPLOAD_STATUS`, "
            "`FREQ`, `BAND`, `ITUZ`) VALUES (" + ",".join(["%s"] * len(values)) + ")"
        )
        db_conn = self.connect_sql()
        try:
            with db_conn.cursor() as cursor:
                cursor.execute(insert_sql, values)
                inserted_id = cursor.lastrowid
            db_conn.commit()
            return inserted_id
        except Exception:
            db_conn.rollback()
            raise
        finally:
            db_conn.close()

    def check_table(self, name_table):
        db_conn = self.connect_sql()
        try:
            with db_conn.cursor() as cursor:
                cursor.execute(
                    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
                    (self.db_name, name_table),
                )
                result = cursor.fetchone() is not None
        finally:
            db_conn.close()
        return result

    def get_all_records(self, count=0):
        connection = self.connect_sql()
        try:
            with connection.cursor() as cursor:
                count = int(count or 0)
                if count > 0:
                    cursor.execute(
                        f"SELECT * FROM {self.qso_table()} ORDER BY `QSO_DATE` DESC, `TIME_ON` DESC LIMIT %s",
                        (int(count),),
                    )
                else:
                    cursor.execute(
                        f"SELECT * FROM {self.qso_table()} ORDER BY `QSO_DATE` DESC, `TIME_ON` DESC"
                    )
                return cursor.fetchall()
        finally:
            connection.close()

    def count_records(self):
        connection = self.connect_sql()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) AS `total` FROM {self.qso_table()}")
                row = cursor.fetchone()
                return int(row["total"]) if row else 0
        finally:
            connection.close()

    def iter_all_records(self, count=0):
        """Stream QSO rows without loading the whole log into memory.

        Uses a server-side cursor so the log window can start filling while the
        database is still sending rows.
        """
        connection = self.connect_sql()
        try:
            with connection.cursor(SSDictCursor) as cursor:
                count = int(count or 0)
                if count > 0:
                    cursor.execute(
                        f"SELECT * FROM {self.qso_table()} ORDER BY `QSO_DATE` DESC, `TIME_ON` DESC LIMIT %s",
                        (int(count),),
                    )
                else:
                    cursor.execute(
                        f"SELECT * FROM {self.qso_table()} ORDER BY `QSO_DATE` DESC, `TIME_ON` DESC"
                    )
                yield from cursor
        finally:
            connection.close()

    def get_record_by_id(self, id):
        connection = self.connect_sql()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.qso_table()} WHERE `id`=%s", (id,))
                return cursor.fetchall()
        finally:
            connection.close()

    def search_like_qsos(self, text):
        sql_query = f"SELECT * FROM {self.qso_table()} WHERE `CALL` LIKE %s"
        self.found_thread = FoundThread(
            connection_factory=self.connect_sql,
            query=sql_query,
            parameters=(f"{text}%",),
        )
        self.found_thread.result.connect(self.like_qso_return)
        self.found_thread.start()

    @QtCore.pyqtSlot(object)
    def like_qso_return(self, obj):
        logger.debug("I am Object", obj)
        self.search_in_db_like_signal.emit(obj)

    def search_qso_in_base(self, call):
        connection = self.connect_sql()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.qso_table()} WHERE `CALL`=%s", (call.strip(),))
                return cursor.fetchall()
        finally:
            connection.close()

    def calls_in_base(self, calls):
        """Return the subset of ``calls`` that already exists in the log table."""
        unique_calls = list({str(call).strip().upper() for call in calls if call})
        if not unique_calls:
            return set()
        found = set()
        connection = self.connect_sql()
        try:
            chunk_size = 500
            with connection.cursor() as cursor:
                for start in range(0, len(unique_calls), chunk_size):
                    chunk = unique_calls[start:start + chunk_size]
                    placeholders = ",".join(["%s"] * len(chunk))
                    cursor.execute(
                        f"SELECT DISTINCT `CALL` FROM {self.qso_table()} WHERE `CALL` IN ({placeholders})",
                        tuple(chunk),
                    )
                    found.update(str(row["CALL"]).strip().upper() for row in cursor.fetchall())
            return found
        finally:
            connection.close()

    def search_qso_by_full_data(self, call, date, time_qso, band, mode):
        connection = self.connect_sql()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT * FROM {self.qso_table()} WHERE `CALL`=%s AND `QSO_DATE`=%s AND `TIME_ON`=%s AND `BAND`=%s AND `MODE`=%s",
                    (call.strip(), date.strip(), time_qso.strip(), band.strip(), mode.strip()),
                )
                return cursor.fetchall()
        finally:
            connection.close()

    def edit_qso(self, record_id, object_dict):
        object_dict = dict(object_dict)
        for key in ('TIME_ON', 'TIME_OFF'):
            if key in object_dict:
                object_dict[key] = parse.normalize_adi_time(object_dict[key])
        if 'QSO_DATE' in object_dict:
            normalized_date = parse.normalize_adi_date(object_dict['QSO_DATE'])
            if normalized_date:
                object_dict['QSO_DATE'] = normalized_date
        connection = self.connect_sql()
        try:
            fields = [
                key for key, value in object_dict.items()
                if key in self.settingsDict["db_fields"] and value not in ("", " ")
            ]
            if not fields:
                return 0
            assignments = ", ".join(f"{self.quote_identifier(key)} = %s" for key in fields)
            values = [object_dict[key] for key in fields]
            values.append(int(record_id))
            with connection.cursor() as cursor:
                result = cursor.execute(
                    f"UPDATE {self.qso_table()} SET {assignments} WHERE `id` = %s",
                    values,
                )
            connection.commit()
            return result
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def delete_qso(self, record_id):
        return self.delete_qsos([record_id])

    def delete_qsos(self, record_ids):
        record_ids = tuple(dict.fromkeys(int(record_id) for record_id in record_ids))
        if not record_ids:
            return 0

        connection = self.connect_sql()
        try:
            with connection.cursor() as cursor:
                placeholders = ", ".join(["%s"] * len(record_ids))
                cursor.execute(
                    f"DELETE FROM {self.qso_table()} WHERE `id` IN ({placeholders})",
                    record_ids,
                )
                deleted_count = cursor.rowcount
            connection.commit()
            return deleted_count
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


class Messages(QWidget):
    def __init__(self, caption, text_message):
        super().__init__()

        self.caption = caption
        self.text_message = text_message
        self.initUI()

    def initUI(self):
        message = QMessageBox(self)
        # message.setFixedWidth(350)
        # message.setFixedHeight(200)
        # Geometry(500, 300, 1000, 700)
        message.setWindowTitle("Information")
        message.setText(self.caption)
        message.setInformativeText(self.text_message)
        message.setStandardButtons(QMessageBox.Ok)
        message.exec()


class AppEnv:
    def __init__(self, data_dict):
        self.data_dict = data_dict

    def appVersion(self):
        return self.data_dict['APP_VERSION']


if __name__ == '__main__':
    #exit(0)
    APP_VERSION = '2.5.1'
    settingsDict = {}
    settingsDict.update({"APP_VERSION": APP_VERSION})
    settingsDict.update({"adi_fields": ['QSO_DATE', 'TIME_ON', 'BAND', 'CALL', 'FREQ', 'MODE', 'RST_RCVD', 'RST_SENT',
     'NAME', 'QTH', 'COMMENT', 'ITUZ', 'TIME_OFF', 'EQSL_QSL_RCVD', 'OPERATOR', 'EQSL_QSL_SENT',
     'CLUBLOG_QSO_UPLOAD_STATUS', 'STATION_CALLSIGN']})

    table_columns = [
        ["CALL", "VARCHAR(50)"],
        ["MODE", "VARCHAR(50)"],
        ["FREQ", "VARCHAR(50)"],
        ["BAND", "VARCHAR(50)"],
        ["NAME", "VARCHAR(50)"],
        ["OPERATOR", "VARCHAR(50)"],
        ["CLUBLOG_QSO_UPLOAD_DATE", "VARCHAR(50)"],
        ["CLUBLOG_QSO_UPLOAD_STATUS", "VARCHAR(50)"],
        ["CNTY", "VARCHAR(50)"],
        ["COMMENT", "VARCHAR(500)"],
        ["COUNTRY", "VARCHAR(50)"],
        ["DXCC", "VARCHAR(50)"],
        ["EQSL_QSL_RCVD", "VARCHAR(50)"],
        ["EQSL_QSL_SENT", "VARCHAR(50)"],
        ["HRDLOG_QSO_UPLOAD_DATE", "VARCHAR(50)"],
        ["HRDLOG_QSO_UPLOAD_STATUS", "VARCHAR(50)"],
        ["LOTW_QSLRDATE", "VARCHAR(50)"],
        ["LOTW_QSLSDATE", "VARCHAR(50)"],
        ["LOTW_QSL_RCVD", "VARCHAR(50)"],
        ["LOTW_QSL_SENT", "VARCHAR(50)"],
        ["QRZCOM_QSO_UPLOAD_DATE", "VARCHAR(50)"],
        ["QRZCOM_QSO_UPLOAD_STATUS", "VARCHAR(50)"],
        ["QSL_RCVD", "VARCHAR(50)"],
        ["QSL_SENT", "VARCHAR(50)"],
        ["QSO_DATE", "DATE"],
        ["TIME_ON", "TIME"],
        ["TIME_OFF", "TIME"],
        ["QTH", "VARCHAR(50)"],
        ["ITUZ", "VARCHAR(50)"],
        ["RST_RCVD", "VARCHAR(50)"],
        ["RST_SENT", "VARCHAR(50)"],
    ]
    settingsDict.update({"db_fields": [field[0] for field in table_columns]})

    settingsDict.update(config_store.load_settings())
    for problem in config_store.validate_settings(settingsDict):
        logger.warning("Configuration problem: %s", problem)

    from app_context import AppContext
    app_context = AppContext(settings=settingsDict)

    ####
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = QApplication(sys.argv)
    app.setApplicationName("LinuxLog")
    app.setApplicationDisplayName("LinuxLog")
    app.setDesktopFileName("linuxlog")
    app.setWindowIcon(QIcon(str(Path(__file__).parent / 'logo.png')))
    settingsDict.update({"app":app})
    app_context.app = app
    flag = 1
    if settingsDict['my-call'] == "":
        hello_window = hello_window(table_columns)

    else:
        settingsDict['db-name'] = str(settingsDict.get('db-name') or '').strip() or 'linuxlog'
        db = Db(settingsDict=settingsDict)
        answer = db.check_database(settingsDict['db-name'])
        try:
            if not answer:
                db.create_database()
            else:
                logger.debug("Database found")

            if db.check_table(settingsDict['my-call']):
                logger.debug("Get table")
            else:
                db.create_table(settingsDict['my-call'].upper(), table_columns)
                logger.debug("Create table")
        except (pymysql.MySQLError, ValueError) as error:
            logger.debug(f"Database setup failed: {error}")
            _run_project_script("help_system.py", 'db-error')
            raise SystemExit(1)

        # global table_columns

        # init all global class
        logWindow = Log_Window_2(settingsDict)
        logSearch = LogSearch(settingsDict)
        internetSearch = InternetSearch(settingsDict)
        qthMap = qth_map.QTHMapWindow(settingsDict)
        logForm = LogForm(settingsDict, logSearch)
        logForm.qth_map = qthMap
        qthMap.map.cluster_spot_clicked.connect(logForm.fill_from_map_spot)
        app_context.log_window = logWindow
        app_context.log_search = logSearch
        app_context.internet_search = internetSearch
        app_context.qth_map = qthMap
        app_context.log_form = logForm

        def _update_qth_map_from_event(payload):
            if isinstance(payload, dict):
                logForm.update_qth_map(
                    payload.get("call"), payload.get("locator"), payload.get("source")
                )
            else:
                logForm.update_qth_map(payload)

        subscribe("qth.map.update", _update_qth_map_from_event)
        telnetCluster = TelnetCluster(settingsDict)
        app_context.telnet_cluster = telnetCluster
        tci_recv = tci.tci_connect(settingsDict, log_form=logForm)
        about_window = About_window("LinuxLog",
                                    "Version: " + APP_VERSION + "<br><a href='https://github.com/bastonc/linuxlog-2_5#linuxlog----ham-logger-for-amateur-radio-station'>LinuxLog on GitHub</a><br>Baston Sergey<br>UR4LGA<br>bastonsv@gmail.com")
        env_dict = {
            "APP_VERSION": APP_VERSION
        }
        app_env = AppEnv(env_dict)



        if settingsDict['cw'] == "True":
            logForm.cw_machine_gui()
        if settingsDict['log-window'] == 'True':
            pass
            # logWindow.show()
        if settingsDict['log-search-window'] == 'True':
            # logSearch.show()
            pass
        if settingsDict['search-internet-window'] == 'True':
            # internetSearch.show()
            pass
        if settingsDict['log-form-window'] == 'True':
            logForm.show()
            #
        if settingsDict['telnet-cluster-window'] == 'True':
            pass
            # telnetCluster.show()
        if settingsDict.get('qth-map-window') == 'True':
            qthMap.show()
        if settingsDict['cat'] == 'enable':
            pass
            # logForm.start_cat()
        tci_sndr = tci.Tci_sender(settingsDict["tci-server"] + ":" + settingsDict["tci-port"], "Disable", logForm, settingsDict)
        if settingsDict['tci'] == 'enable':
            tci_recv.start_tci(settingsDict["tci-server"], settingsDict["tci-port"])
    sys.exit(app.exec())
