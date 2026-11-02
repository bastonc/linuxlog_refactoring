from pathlib import Path
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import re

from PyQt6.QtWidgets import QMessageBox, QLineEdit, QWidget, QLabel, QPushButton, \
    QVBoxLayout, QApplication
from PyQt6 import QtCore


_BAND_RANGES = (
    (1_800_000, 2_000_000, "160"),
    (3_500_000, 3_800_000, "80"),
    (7_000_000, 7_200_000, "40"),
    (10_100_000, 10_150_000, "30"),
    (14_000_000, 14_500_000, "20"),
    (18_068_000, 18_168_000, "17"),
    (21_000_000, 21_450_000, "15"),
    (24_890_000, 24_990_000, "12"),
    (28_000_000, 29_700_000, "10"),
    (50_000_000, 54_000_000, "6"),
    (144_000_000, 146_500_000, "2"),
)


@lru_cache(maxsize=1)
def _load_band_rules():
    rules = {}
    path = Path(__file__).parent / "bandplan.cfg"
    with path.open("r", encoding="utf-8") as config_file:
        for line in config_file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            rules[key.strip()] = value.strip()
    return rules


class std:
    def __init__(self):
        self.band_rules = _load_band_rules().copy()

    def mode_band_plan(self, band, freq):
        try:
            if int(self.band_rules["start-cw"+band]) < int(freq) <= int(self.band_rules["end-cw"+band]):
                mode = "CW"
            elif int(self.band_rules["start-ssb"+band]) < int(freq) <= int(self.band_rules["end-ssb"+band]):
                if int(band) < 40:
                    mode = "USB"
                else:
                    mode = "LSB"
            elif int(self.band_rules["start-digi"+band]) < int(freq) <= int(self.band_rules["end-digi"+band]):
                if int(band) < 40:
                    mode = ("DIGU", "PKTUSB")
                else:
                    mode = ("DIGL", "PKTLSB")
            else:
                mode = "ERROR"
        except (KeyError, TypeError, ValueError):
            mode = "ERROR"
        return mode


    def get_index_column(self, tableWidget_qso):
        supported_columns = {
            'id', 'QSO_DATE', 'TIME_ON', 'CALL', 'RST_RCVD', 'RST_SENT',
            'NAME', 'QTH', 'BAND', 'COMMENT', 'TIME_OFF', 'EQSL_QSL_SENT',
            'MODE', 'CLUBLOG_QSO_UPLOAD_STATUS',
        }
        index_columns = {}
        for index in range(tableWidget_qso.columnCount()):
            header_item = tableWidget_qso.horizontalHeaderItem(index)
            if header_item is None:
                continue
            column = header_item.text()
            if column in supported_columns:
                index_columns[column] = index
        return index_columns

    def get_std_band(self, freq):  # get Band in m
        try:
            normalized_frequency = self.std_freq(freq)
            if not normalized_frequency:
                return "GEN"
            frequency = int(normalized_frequency)
        except (TypeError, ValueError, InvalidOperation):
            return "GEN"

        for lower, upper, band in _BAND_RANGES:
            if lower <= frequency <= upper:
                return band
        return "GEN"

    def std_freq(self, freq):   # get format freq in Hz (Ex.14000000)
        frequency_text = str(freq).strip().replace(",", ".")
        if re.fullmatch(r"\d{1,3}(?:\.\d{3}){2,}", frequency_text):
            frequency_text = frequency_text.replace(".", "")
        try:
            frequency = Decimal(frequency_text)
        except (InvalidOperation, ValueError):
            return ""
        if not frequency.is_finite() or frequency < 0:
            return ""

        # Cluster spots are commonly sent in MHz with a decimal point, while
        # integer values of 4-6 digits are commonly kHz and 7+ digits are Hz.
        if frequency < 1_000_000:
            if "." in frequency_text or len(frequency_text.lstrip("0")) <= 3:
                frequency *= 1_000_000
            else:
                frequency *= 1_000
        return str(int(frequency)).zfill(8)

    def message(self, detail_text, text_short):
        message = QMessageBox()
        message.setGeometry(500, 300, 1000, 500)
        message.setWindowTitle("Information")
        message.setText(text_short)
        message.setInformativeText(detail_text)
        message.setStandardButtons(QMessageBox.StandardButton.Ok)
        message.exec()

    @staticmethod
    def _time_parts(value):
        text = str(value or "").strip()
        if ":" in text:
            parts = text.split(":")
            if len(parts) not in (2, 3) or any(not part.isdigit() or len(part) > 2 for part in parts):
                return None
            hours, minutes = map(int, parts[:2])
            seconds = int(parts[2]) if len(parts) == 3 else 0
            has_seconds = len(parts) == 3
        else:
            if not text.isdigit() or len(text) not in (4, 6):
                return None
            hours = int(text[:2])
            minutes = int(text[2:4])
            seconds = int(text[4:6]) if len(text) == 6 else 0
            has_seconds = len(text) == 6

        if hours > 23 or minutes > 59 or seconds > 59:
            return None
        return hours, minutes, seconds, has_seconds

    def std_time(self, string_time):
        parts = self._time_parts(string_time)
        if parts is None:
            return ""
        hours, minutes, seconds, has_seconds = parts
        time_string = f"{hours:02d}{minutes:02d}"
        return time_string + f"{seconds:02d}" if has_seconds else time_string

    def adi_time_to_std_time(self, adi_time):
        parts = self._time_parts(adi_time)
        if parts is None:
            return ""
        hours, minutes, seconds, _has_seconds = parts
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def adi_date_to_std_date(self, adi_date):
        date = adi_date[:4] + "-" + adi_date[4:6] + "-" + adi_date[6:]
        return date

    def adi_time_add_seconds(self, adi_time):
        parts = self._time_parts(adi_time)
        if parts is None:
            return str(adi_time or "")
        hours, minutes, seconds, _has_seconds = parts
        return f"{hours:02d}{minutes:02d}{seconds:02d}"
class wnd_what(QWidget):
    ok = QtCore.pyqtSignal(str)
    def __init__(self, header_text):
        super(wnd_what, self).__init__()
        self.header_text = header_text
        self.initUI()

    def initUI(self):
        desktop = QApplication.primaryScreen().availableGeometry()
        width_coordinate = (desktop.width() / 2 - 75)
        height_coordinate = (desktop.height() / 2) - 40
        self.setGeometry(round(width_coordinate), round(height_coordinate), 300, 80)
        self.setFixedWidth(170)
        self.setFixedHeight(90)
        self.label = QLabel(str(self.header_text))
        self.input_line = QLineEdit()
        self.input_line.setFixedWidth(150)
        self.input_line.setFixedHeight(25)
        self.button_ok = QPushButton("Save")
        self.button_ok.setFixedWidth(50)
        self.button_ok.setFixedHeight(20)
        self.button_ok.clicked.connect(self.out_data)
        self.v_box = QVBoxLayout()
        self.v_box.totalHeightForWidth(100)
        self.v_box.addWidget(self.label)
        self.v_box.addWidget(self.input_line)
        self.v_box.addWidget(self.button_ok)
        self.setLayout(self.v_box)
        self.show()
    def out_data(self):
        if self.input_line.text().strip() != '':
            self.ok.emit(self.input_line.text().strip())
            self.close()
            return self.input_line.text().strip()
