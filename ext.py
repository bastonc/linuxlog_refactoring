#!/usr/bin/python3
# -*- coding: utf-8 -*-
#from PyQt6 import QtCore
import signal
from collections import Counter
from pathlib import Path


from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget, QApplication, QSizePolicy, QSpacerItem, QColorDialog, QTableWidget, \
        QPushButton, \
        QCalendarWidget, QLayout, QHBoxLayout, QLineEdit, QVBoxLayout, QLabel, QCheckBox, QTableWidgetItem, QComboBox
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import QObject
import settings
import parse
import json
import main
import std
import os
import tempfile


def _award_path(filename):
    """Resolve an award data filename inside the application directory."""
    filename = str(filename or "").strip()
    if (
        not filename
        or filename in {".", ".."}
        or Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
        or any(ord(character) < 32 for character in filename)
    ):
        raise ValueError("Invalid award filename")
    return Path(__file__).parent / filename


class test:
    def __init__(self):
        list = [{"call":
                     "EH8URT",
                 "score": "10"},
                {"call": "Z81D",
                 "score": "10"},
                {"call": "Z81D",
                 "score": "10"},
                {"call": "VP8PJ",
                 "score": "10"},
                {"call": "VP8LP",
                 "score": "10"}

                ]
        with open(Path(__file__).parent/"rules.json", 'w') as f:
            f.write(json.dumps(list))
        # print("json.dumps", json.dumps(list))


class Diplom_form(QWidget):

    def __init__(self, settingsDict, log_form, adi_file, diplomname='', list_data=None):
        super().__init__()
        # print("Diplom_form(QWidget) init_")
        self.logForm = log_form
        self.diplomname = diplomname
        self.settingsDict = settingsDict
        self.adi = adi_file
        self.list_data = list_data if list_data is not None else []
        self.initUI()

    def initUI(self):
        if self.diplomname == '':
            self.setWindowTitle("Create diplom")
        else:
            self.setWindowTitle("Edit diplom " + self.diplomname)

            # rules = diplom.get_rules(diplom, self.diplomname+".rules")
        self.setGeometry(300, 500, 500, 300)
        # self.setFixedWidth(450)
        # self.setFixedHeight(450)
        self.setWindowIcon(QIcon('logo.png'))
        style = "QWidget{background-color:" + self.settingsDict['background-color'] + "; color:" + self.settingsDict[
            'color'] + ";}"
        styleform = "background :" + self.settingsDict['form-background'] + "; font-weight: bold; color:" + \
                    self.settingsDict['color-table'] + ";"
        self.setGeometry(int(self.settingsDict['log-form-window-left']), int(self.settingsDict['log-form-window-top']),
                         int(self.settingsDict['log-form-window-width']),
                         int(self.settingsDict['log-form-window-height']))

        self.setStyleSheet(style)
        self.name_layout = QHBoxLayout()
        self.name_label = QLabel("Name of Awards:")
        self.name_label.setFixedWidth(150)
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(styleform)
        self.name_input.setFixedWidth(200)
        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_input)
        self.name_layout.addStretch(300)
        #
        self.score_layout = QHBoxLayout()
        score_text = QLabel("How many points for complite finish")
        score_text.setStyleSheet(style)
        self.score_input = QLineEdit()
        self.score_input.setStyleSheet(styleform)
        self.score_input.setText("0")
        self.score_layout.addWidget(score_text)
        self.score_layout.addWidget(self.score_input)
        #
        self.repeat_layout = QHBoxLayout()
        self.only_bands_checkable = QCheckBox("Only band:")
        self.text_repeat = QLabel("Repeats:")
        self.text_repeat.setStyleSheet("font: 10px;")
        self.repeat_combo = QComboBox()

        self.repeat_combo.setFixedWidth(200)
        self.repeat_combo.setStyleSheet("font: 10px;")
        self.repeat_combo.addItems(
            ["Resolved other bands", "Resolved others mod", "Resolving other mods and bands", "Not resolving"])
        self.only_bands = QComboBox()
        self.only_bands.setStyleSheet("font: 10px;")
        self.only_bands.setFixedWidth(90)

        self.only_bands_checkable.setStyleSheet("font: 10px;")
        self.only_bands_layout = QHBoxLayout()
        self.only_bands_layout.addWidget(self.only_bands_checkable)
        self.only_bands_layout.addWidget(self.only_bands)
        self.only_bands.addItems(["Not use", "160", "80", "40", "30", "20", "17", "15", "12", "10", "6", "2"])
        # mapping checkable
        if self.only_bands_checkable.isChecked():
            self.repeat_combo.setEnabled(False)

        self.repeat_layout.addWidget(self.text_repeat)
        self.repeat_layout.addWidget(self.repeat_combo)
        self.repeat_layout.addLayout(self.only_bands_layout)
        self.repeat_layout.addStretch(100)
        #
        self.sps_layout = QHBoxLayout()
        self.prefix_check_box = QCheckBox("as Prefix")
        self.prefix_check_box.setChecked(False)
        self.sps_text = QLabel("Special calls \n or prefix:")
        self.sps_table_widget = QTableWidget()
        self.sps_table_widget.setStyleSheet(styleform)
        self.sps_table_widget.setFixedWidth(260)
        self.sps_table_widget.setFixedHeight(200)
        self.sps_table_widget.setColumnCount(3)
        self.sps_table_widget.setColumnWidth(0, 80)
        self.sps_table_widget.setColumnWidth(1, 50)
        self.sps_table_widget.setColumnWidth(2, 80)
        self.sps_table_widget.setRowCount(10)
        self.sps_table_widget.setHorizontalHeaderLabels(['call', 'score', 'mode'])
        self.sps_table_widget.horizontalHeaderItem(0).setToolTip("Enter special call")
        self.sps_table_widget.horizontalHeaderItem(1).setToolTip("Enter scores for QSO")
        self.sps_table_widget.horizontalHeaderItem(2).setToolTip("Select mode")
        # self.combo_mode = QComboBox()
        # self.combo_mode2 = QComboBox()
        # self.combo_mode.addItems(['SSB', 'CW', 'DIGI'])
        # self.combo_mode2.addItems(['SSB', 'CW', 'DIGI'])
        row_count = self.sps_table_widget.rowCount()
        self.combo_mode_list = []
        if self.diplomname == '':

            for row in range(row_count):
                self.combo_mode_list.append({'combo' + str(row): QComboBox()})
                self.combo_mode_list[row]['combo' + str(row)].addItems(['SSB', 'CW', 'DIGI'])
                self.combo_mode_list[row]['combo' + str(row)].setFixedWidth(80)
                self.sps_table_widget.setCellWidget(row, 2, self.combo_mode_list[row]['combo' + str(row)])

        add_row = QPushButton("Add rows")
        add_row.clicked.connect(self.add_row)
        self.prefix_lay = QVBoxLayout()
        self.prefix_lay.setAlignment(QtCore.Qt.AlignVCenter)
        self.prefix_lay.addWidget(self.prefix_check_box)
        self.prefix_lay.addWidget(self.sps_text)
        self.sps_layout.addLayout(self.prefix_lay)
        self.sps_layout.addWidget(self.sps_table_widget)
        self.sps_layout.addWidget(add_row)
        #
        self.button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.ok_button = QPushButton("Save award")
        self.ok_button.clicked.connect(self.save_diplom)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.ok_button)
        #
        self.color_label = QLabel()
        self.color_label.setStyleSheet(style)
        self.color_label.setText("Select color for telnet highlight")
        self.color_button = QPushButton()
        # self.color_button.setFixedWidth(100)
        self.color_button.clicked.connect(self.select_color)
        if self.diplomname == '':
            self.color_button.setText("Select color")

        self.color_layout = QHBoxLayout()
        self.color_layout.addWidget(self.color_label)
        self.color_layout.addWidget(self.color_button)
        #
        self.global_layout = QVBoxLayout()
        self.global_layout.addLayout(self.name_layout)
        # self.global_layout.addLayout(self.date_layout)
        # self.spaceItem = QSpacerItem(15, 10)
        # self.global_layout.addSpacerItem(self.spaceItem)
        self.global_layout.addLayout(self.color_layout)
        # self.global_layout.addSpacerItem(self.spaceItem)
        self.global_layout.addLayout(self.score_layout)
        self.global_layout.addLayout(self.repeat_layout)
        self.global_layout.addLayout(self.sps_layout)
        self.global_layout.addLayout(self.button_layout)
        self.setLayout(self.global_layout)
        if self.diplomname != '':
            self.add_info(self.list_data)

    def select_color(self):
        color = QColorDialog.getColor(initial=QColor(self.color_button.text()), parent=None,
                                      title="Select color for cluster highlight")
        if color.isValid():
            self.colorR = color.red()
            self.colorG = color.green()
            self.colorB = color.blue()
            self.color_name = color.name()
            self.color_button.setStyleSheet("background:" + color.name())
            self.color_button.setText(color.name())

    def add_info(self, list_data):
        # print ("list_data:_>",list_data)
        self.color_name = list_data[0]['color_name']
        self.colorR = list_data[0]['colorR']
        self.colorG = list_data[0]['colorG']
        self.colorB = list_data[0]['colorB']
        self.color_button.setStyleSheet("background:" + self.color_name)
        self.color_button.setText(self.color_name)
        self.name_input.setText(list_data[0]['name'])
        self.score_input.setText(list_data[0]['score_complite'])
        self.repeat_combo.setCurrentIndex(list_data[0]['repeats'])
        rows = len(list_data)
        self.only_bands_checkable.setChecked(self.list_data[0]['only_bands_enable'])
        self.only_bands.setCurrentText(self.list_data[0]['only_bands'])
        self.sps_table_widget.setRowCount(rows)
        for row in range(rows):
            self.sps_table_widget.setRowHeight(row, 20)
            self.sps_table_widget.setItem(row, 0, QTableWidgetItem(list_data[row]['call']))
            self.sps_table_widget.setItem(row, 1, QTableWidgetItem(list_data[row]['score']))

            self.combo_mode_list.append({'combo' + str(row): QComboBox()})
            self.combo_mode_list[row]['combo' + str(row)].addItems(['SSB', 'CW', 'DIGI'])
            self.combo_mode_list[row]['combo' + str(row)].setFixedHeight(20)
            self.combo_mode_list[row]['combo' + str(row)].setCurrentText(list_data[row]['mode'])
            self.sps_table_widget.setCellWidget(row, 2, self.combo_mode_list[row]['combo' + str(row)])
            self.prefix_check_box.setChecked(self.list_data[row]['prefix'])
        self.sps_table_widget.resizeRowsToContents()

    def add_row(self):
        self.sps_table_widget.insertRow(self.sps_table_widget.rowCount())
        counter = self.sps_table_widget.rowCount()
        len(self.combo_mode_list)
        self.combo_mode_list.append({'combo' + str(counter - 1): QComboBox()})
        # print ("all rows:_>", counter, len(self.combo_mode_list))
        self.combo_mode_list[len(self.combo_mode_list) - 1]['combo' + str(counter - 1)].addItems(['SSB', 'CW', 'DIGI'])
        self.sps_table_widget.setCellWidget(counter - 1, 2, self.combo_mode_list[len(self.combo_mode_list) - 1][
            'combo' + str(counter - 1)])

    def save_diplom(self):
        list_to_json = []
        name_programm = self.name_input.text().strip()
        try:
            _award_path(f"{name_programm}.rules")
            name_valid = bool(name_programm) and name_programm not in {".", ".."}
        except ValueError:
            name_valid = False
        if not name_valid:
            self.name_input.setStyleSheet("border: 2px solid #DD5555;")
            std.std.message(self, "Invalid award name", "Enter a name without path separators.")
            return

        if self.color_button.text() == 'Select color':
            self.color_button.setStyleSheet("border: 2px solid #DD5555;")
            std.std.message(self, "Select award color", "Choose a color for this award before saving.")
            return

        settings_text = self.settingsDict.get('diploms-json', '')
        try:
            settings_list = json.loads(settings_text) if settings_text else []
        except json.JSONDecodeError:
            std.std.message(self, "Invalid award settings", "The saved award list is not valid JSON.")
            return
        if not isinstance(settings_list, list):
            std.std.message(self, "Invalid award settings", "The saved award list must be a list.")
            return

        old_name = self.diplomname.strip()
        if old_name:
            try:
                _award_path(f"{old_name}.rules")
            except ValueError:
                std.std.message(self, "Invalid saved award name", "The existing award name cannot be used as a file path.")
                return
        if any(not isinstance(item, dict) for item in settings_list):
            std.std.message(self, "Invalid award settings", "Each saved award entry must be an object.")
            return
        existing_names = [str(item.get('name_programm', '')) for item in settings_list]
        if old_name and old_name not in existing_names:
            std.std.message(self, "Award not found", "The award being edited is no longer in the saved list.")
            return
        if any(name == name_programm for name in existing_names if name != old_name):
            std.std.message(self, "Programm with that name already exists", "Repeats")
            return

        old_rules = _award_path(f"{old_name}.rules") if old_name else None
        old_adi = _award_path(f"{old_name}.adi") if old_name else None
        new_rules = _award_path(f"{name_programm}.rules")
        new_adi = _award_path(f"{name_programm}.adi")
        is_new_award = not old_name
        if is_new_award and (new_rules.exists() or new_adi.exists()):
            std.std.message(self, "Award files already exist", "Choose another name to avoid replacing existing data.")
            return
        if old_name and name_programm != old_name and (new_rules.exists() or new_adi.exists()):
            std.std.message(self, "Award files already exist", "Choose another name to avoid replacing existing data.")
            return

        score_complete = self.score_input.text().strip()
        if not score_complete.isascii() or not score_complete.isdigit():
            self.score_input.setStyleSheet("border: 2px solid #DD5555;")
            std.std.message(self, "Invalid completion score", "Enter a non-negative whole number.")
            return

        repeats = self.repeat_combo.currentIndex()
        for row in range(self.sps_table_widget.rowCount()):
            call_item = self.sps_table_widget.item(row, 0)
            if call_item is None or not call_item.text().strip():
                continue
            score_item = self.sps_table_widget.item(row, 1)
            score = score_item.text().strip() if score_item else ""
            if score and (not score.isascii() or not score.isdigit()):
                score_item.setStyleSheet("border: 2px solid #DD5555;")
                std.std.message(self, "Invalid award score", "Use ASCII digits for each callsign's score.")
                return
            score = score or "0"
            list_to_json.append({
                'call': call_item.text().strip().upper(),
                'score': score,
                'mode': self.combo_mode_list[row]['combo' + str(row)].currentText(),
                'name': name_programm,
                'colorR': self.colorR,
                'colorG': self.colorG,
                'colorB': self.colorB,
                'color_name': self.color_name,
                'repeats': repeats,
                'only_bands_enable': self.only_bands_checkable.isChecked(),
                'only_bands': self.only_bands.currentText(),
                'score_complite': score_complete,
                'prefix': self.prefix_check_box.isChecked(),
            })
        if not list_to_json:
            std.std.message(self, "Award has no calls", "Add at least one callsign or prefix before saving.")
            return

        old_rules_moved = False
        old_adi_moved = False
        try:
            if old_name and name_programm != old_name:
                if old_rules is not None and old_rules.exists():
                    old_rules.rename(new_rules)
                    old_rules_moved = True
                if old_adi is not None and old_adi.exists():
                    old_adi.rename(new_adi)
                    old_adi_moved = True

            self.write_rules_to_file(list_to_json, name_output_file=name_programm)
            if is_new_award:
                self.adi.create_adi(name_programm + ".adi")
        except OSError as error:
            if is_new_award:
                if new_adi.exists():
                    new_adi.unlink()
                if new_rules.exists():
                    new_rules.unlink()
            if old_adi_moved and new_adi.exists():
                new_adi.rename(old_adi)
            if old_rules_moved and new_rules.exists():
                new_rules.rename(old_rules)
            std.std.message(self, "Unable to save award", str(error))
            return

        if is_new_award:
            settings_list.append({'name_programm': name_programm})
        else:
            for item in settings_list:
                if item.get('name_programm') == old_name:
                    item['name_programm'] = name_programm
                    break

        self.settingsDict['diploms-json'] = json.dumps(settings_list)
        main.Settings_file.update_file_to_disk(self)
        if is_new_award:
            self.logForm.menu_add(name_menu=name_programm)
        else:
            self.logForm.menu_rename_diplom()
            self.logForm.menu()
        self.logForm.diploms_init()
        self.close()

    def write_rules_to_file(self, data_to_json, name_output_file):
        rules_path = _award_path(f"{str(name_output_file).strip()}.rules")
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=rules_path.parent,
                prefix=f".{rules_path.name}.", suffix='.tmp', delete=False,
            ) as rules_file:
                temporary_path = Path(rules_file.name)
                json.dump(data_to_json, rules_file, ensure_ascii=False)
                rules_file.flush()
                os.fsync(rules_file.fileno())
            os.replace(temporary_path, rules_path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()


class Diplom(QObject):
    name = ''

    def __init__(self, name, settingsDict, parent=''):
        super().__init__()
        self.name = str(name).strip()
        self.rules_path = _award_path(f"{self.name}.rules")
        self.settingsDict = settingsDict
        if parent != '':
            self.parentWindow = parent
        else:
            self.parentWindow = None
        self.allCollumn = ['records_number', 'QSO_DATE', 'TIME_ON', 'BAND', 'CALL', 'FREQ', 'MODE', 'RST_RCVD',
                           'RST_SENT',
                           'NAME', 'QTH', 'COMMENT', 'ITUZ', 'TIME_OFF', 'eQSL_QSL_RCVD', 'OPERATOR', 'EQSL_QSL_SENT',
                           'CLUBLOG_QSO_UPLOAD_STATUS']

        self.initial()

    def initial(self):
        '''
        initial self variables for using in internal logic
        :return: self.diplomDataList - Object (List) with full data about awards program,
        self.adiFile - Data from <awards name>.adi file with QSO for diplom,
        self.qsoData - object [{qso 1 data}...{qso n data}] with All QSO data.
        '''
        # 1
        self.diplomDataList = self.getRules()
        # 2
        self.adi_path = _award_path(f"{self.diplomDataList[0]['name']}.adi")
        self.adiFile = main.Adi_file("in", self.settingsDict, self.adi_path.name)
        # 3
        self.qsoData = self.getQsoData()

    def getQsoData(self):
        '''
        Parse .adi file and generated the dictionary object for QSOs
        :return: qsoDataList - object [{... QSO 1 info...},{...QSO 2 info...}]
        '''
        return parse.getAllRecord(self.allCollumn, self.adi_path.name, key="import")

    def getRules(self):
        with self.rules_path.open('r', encoding='utf-8') as rules:
            rulesObject = json.load(rules)
        if not isinstance(rulesObject, list) or not rulesObject:
            raise ValueError("Award rules must be a non-empty list")
        if any(not isinstance(rule, dict) for rule in rulesObject):
            raise ValueError("Each award rule must be an object")
        return rulesObject

    def complete(self):
        score = self.getScore()
        scoreComplete = self.diplomDataList[0]['score_complite']
        if int(score) >= int(scoreComplete):
            return True
        return False

    @staticmethod
    def _rule_matches_call(call, rule):
        call = str(call or "").strip().upper()
        rule_call = str(rule.get('call', '')).strip().upper()
        if not call or not rule_call:
            return False
        if rule.get('prefix'):
            return any(component.startswith(rule_call) for component in call.split('/'))
        return call == rule_call

    def getScore(self):
        call_counts = Counter(
            str(qso.get('CALL') or '').strip().upper()
            for qso in self.qsoData
            if qso.get('CALL')
        )
        total_score = 0
        for rule in self.diplomDataList:
            if rule.get('prefix'):
                match_count = sum(
                    count for call, count in call_counts.items()
                    if self._rule_matches_call(call, rule)
                )
            else:
                rule_call = str(rule.get('call', '')).strip().upper()
                match_count = call_counts.get(rule_call, 0)
            total_score += int(rule['score']) * match_count
        return total_score

    def filter(self, callDict):
        if self.checkQso(callDict):
            return True

    def checkQso(self, callDict):
        pass


class diplom:
    '''
    This class work with extended functions for diplom module
    '''

    def __init__(self, file, file_rules, settingsDict=''):
        self.file = _award_path(file).name
        self.file_rules = _award_path(file_rules).name
        self.allCollumn = ['records_number', 'QSO_DATE', 'TIME_ON', 'BAND', 'CALL', 'MODE', 'RST_RCVD', 'RST_SENT',
                           'NAME', 'QTH', 'COMMENTS', 'TIME_OFF', 'eQSL_QSL_RCVD']
        self.allRecord = parse.getAllRecord(self.allCollumn, self.file)
        # print("diplom:", self.allRecord)
        self.decode_data = self.get_rules(self.file_rules)
        if settingsDict != '':
            self.settingsDict = settingsDict

    @staticmethod
    def get_rules(name):
        with _award_path(name).open("r", encoding="utf-8") as f:
            rules = json.load(f)
        if not isinstance(rules, list) or not rules or any(not isinstance(rule, dict) for rule in rules):
            raise ValueError("Award rules must be a list of objects")
        return rules

    def search_call_in_base(self, call):
        call = str(call or "").strip().upper()
        return [
            record for record in self.allRecord
            if str(record.get('CALL', '')).strip().upper() == call
        ]

    def get_color_bg(self):
        color = QColor(int(self.decode_data[0]['colorR']),
                       int(self.decode_data[0]['colorG']),
                       int(self.decode_data[0]['colorB']))

        return color

    @staticmethod
    def _mode_family(mode):
        mode = str(mode or "").strip().upper()
        if mode in {"SSB", "USB", "LSB", "DSB", "AM", "SAM", "FM", "NFM", "WFM"}:
            return "SSB"
        if mode in {"CW", "CWR"}:
            return "CW"
        if mode in {"DIGI", "DIGU", "DIGL", "FT8", "FT4", "RTTY", "PSK", "PSK31", "JT65", "JT9",
                    "WSPR", "PKTUSB", "PKTLSB", "DATA", "MFSK"}:
            return "DIGI"
        return mode

    @staticmethod
    def _band_number(band):
        digits = "".join(character for character in str(band or "") if character.isdigit())
        return digits.lstrip("0") or "0"

    @staticmethod
    def _matches_rule_call(call, rule):
        call = str(call or "").strip().upper()
        rule_call = str(rule.get("call", "")).strip().upper()
        if not call or not rule_call:
            return False
        if rule.get("prefix"):
            return any(component.startswith(rule_call) for component in call.split("/"))
        return call == rule_call

    def filter(self, call_dict):
        """Return whether a QSO or cluster spot still satisfies this award."""
        rules = self.decode_data
        if not rules:
            return False

        matching_rules = [rule for rule in rules if self._matches_rule_call(call_dict.get("call"), rule)]
        if not matching_rules:
            return False

        # Cluster rows are highlighted for any configured callsign, regardless
        # of current QSO mode or whether the award has already been completed.
        if str(call_dict.get("mode", "")).lower() == "cluster":
            return True

        target_mode = self._mode_family(call_dict.get("mode"))
        matching_rules = [
            rule for rule in matching_rules
            if str(rule.get("mode", "")).strip().lower() in {"all", "prefix"}
            or self._mode_family(rule.get("mode")) == target_mode
        ]
        if not matching_rules:
            return False

        first_rule = rules[0]
        band_restricted = first_rule.get("only_bands_enable")
        band_restricted = band_restricted is True or str(band_restricted).lower() == "true"
        if band_restricted:
            required_band = self._band_number(first_rule.get("only_bands"))
            if required_band in {"", "0"} or self._band_number(call_dict.get("band")) != required_band:
                return False

        call = str(call_dict.get("call", "")).strip().upper()
        call_records = [record for record in self.search_call_in_base(call)]
        try:
            repeats = int(first_rule.get("repeats", 0))
        except (TypeError, ValueError):
            return False
        band = self._band_number(call_dict.get("band"))
        mode = target_mode

        if repeats == 0:
            return not any(self._band_number(record.get("BAND")) == band for record in call_records)
        if repeats == 1:
            return not any(self._mode_family(record.get("MODE")) == mode for record in call_records)
        if repeats == 2:
            return not any(
                self._mode_family(record.get("MODE")) == mode
                and self._band_number(record.get("BAND")) == band
                for record in call_records
            )
        if repeats == 3:
            return not call_records
        return False

    def add_qso(self, list_data):
        '''
         This function recieve List (list_data) with Dictionary with QSO-data
         Dictionary including:
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
        qso = dict(list_data)
        comment = qso.get('COMMENT', qso.get('COMMENTS', ''))
        fields = (
            ('BAND', qso.get('BAND', '')),
            ('CALL', qso.get('CALL', '')),
            ('FREQ', main.Adi_file._format_adif_frequency(qso.get('FREQ'))),
            ('MODE', qso.get('MODE', '')),
            ('OPERATOR', qso.get('OPERATOR', '')),
            ('QSO_DATE', qso.get('QSO_DATE', '')),
            ('TIME_ON', qso.get('TIME_ON', '')),
            ('RST_RCVD', qso.get('RST_RCVD', '')),
            ('RST_SENT', qso.get('RST_SENT', '')),
            ('NAME', qso.get('NAME', '')),
            ('QTH', qso.get('QTH', '')),
            ('COMMENTS', comment),
            ('TIME_OFF', qso.get('TIME_OFF', '')),
            ('eQSL_QSL_RCVD', 'Y'),
        )
        record = ''.join(main._format_adi_field(name, value) for name, value in fields) + '<EOR>\n'
        path = _award_path(self.file)
        with path.open('a', encoding='utf-8') as file:
            file.write(record)
        self.allRecord.append(qso)

    def get_count_qso(self):
        return len(self.allRecord)

    def get_all_qso(self):
        return self.allRecord

    def get_data(self):
        return self.decode_data

    def del_dilpom(self, name_diplom, settingsDict, logForm):
        self.settingsDict = settingsDict
        try:
            rules_path = _award_path(f"{name_diplom}.rules")
            adi_path = _award_path(f"{name_diplom}.adi")
            saved_awards = json.loads(self.settingsDict.get('diploms-json') or '[]')
            if not isinstance(saved_awards, list):
                raise ValueError("The saved award list is invalid")
            remaining_awards = [
                award for award in saved_awards
                if not isinstance(award, dict) or award.get('name_programm') != name_diplom
            ]
            if len(remaining_awards) == len(saved_awards):
                raise ValueError("The award was not found in the saved list")

            previous_value = self.settingsDict.get('diploms-json', '')
            paths_to_remove = [path for path in (rules_path, adi_path) if path.is_file()]
            with tempfile.TemporaryDirectory(
                prefix='.award-delete-', dir=Path(__file__).parent
            ) as backup_directory:
                backup_directory = Path(backup_directory)
                moved_files = []
                try:
                    for source in paths_to_remove:
                        backup = backup_directory / source.name
                        source.rename(backup)
                        moved_files.append((backup, source))

                    self.settingsDict['diploms-json'] = json.dumps(remaining_awards)
                    main.Settings_file.update_file_to_disk(self)
                except Exception:
                    self.settingsDict['diploms-json'] = previous_value
                    for backup, source in reversed(moved_files):
                        if backup.exists():
                            backup.rename(source)
                    raise
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            std.std.message(logForm, "Unable to delete award", str(error))
            return False

        logForm.menu_rename_diplom()
        logForm.diploms_init()
        logForm.menu()
        return True

    def checkQso(self, callDict):
        self.diplomsObject = self.get_data()
        if self.filter({'call': callDict['CALL'], 'mode': callDict['MODE'], 'band': callDict['BAND']}):
            print("~" * 20)
            print("Check QSO on Awards list")
            print("~" * 20)

    # def check(self):
    #     self.diplomsObject = self.get_data()
    #     for diplom in self.diplomsObject:
    #         print("*" * 20)
    #         print(type(diplom), diplom)
    #         print("*" * 20)
    #         foundQsoList = main.Db(self.settingsDict).getQsoByCallPattern(diplom['call'])
    #         countQso = len(foundQsoList)
    #         for qso in foundQsoList:
    #             if self.filter({'call': qso['CALL'], 'mode': qso['MODE'], 'band': qso['BAND']}):
    #                 print("**" * 20)
    #                 print("Filter ok" * 10)
    #                 print("**" * 20)
    #         #
    #         print("Len qso in checkDiploms:", countQso)


class static_diplom(QWidget):
    def __init__(self, diplom_name, settingsDict):
        super().__init__()
        self.diplom_name = diplom_name
        self.settingsDict = settingsDict
        self.initUI()
        self.update()

    def initUI(self):
        # self.setGeometry(300, 500, 500, 300)
        style = "QWidget{background-color:" + self.settingsDict['background-color'] + "; color:" + self.settingsDict[
            'color'] + ";}"
        styleform = "background :" + self.settingsDict['form-background'] + "; font-weight: bold; color:" + \
                    self.settingsDict['color-table']
        self.setGeometry(int(self.settingsDict['diplom-statistic-window-left']),
                         int(self.settingsDict['diplom-statistic-window-top']),
                         int(self.settingsDict['diplom-statistic-window-width']),
                         int(self.settingsDict['diplom-statistic-window-height']))

        self.setStyleSheet(style)
        self.setWindowTitle("Statistic diplom: " + str(self.diplom_name))

        self.score_final_label = QLabel()
        self.score_final_label.setStyleSheet("font-size: 12px;")
        self.score_total_label = QLabel()
        self.score_total_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(self.score_final_label)
        self.top_layout.addWidget(self.score_total_label)
        self.table_widget = QTableWidget()
        self.table_widget.setStyleSheet(styleform)

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addLayout(self.top_layout)
        self.vertical_layout.addWidget(self.table_widget)

        self.setLayout(self.vertical_layout)

    def update(self):
        self.all_column = ['records_number', 'QSO_DATE', 'TIME_ON', 'BAND', 'CALL', 'MODE', 'RST_RCVD', 'RST_SENT',
                           'NAME', 'QTH', 'COMMENTS', 'TIME_OFF', 'eQSL_QSL_RCVD']
        self.rules = diplom.get_rules(_award_path(f"{self.diplom_name}.rules").name)
        self.score_final_label.setText("Total score need: " + str(self.rules[0]['score_complite']))
        self.all_records = parse.getAllRecord(
            self.all_column, _award_path(f"{self.diplom_name}.adi").name
        )
        records_count = len(self.all_records)
        column_count = len(self.all_column)
        self.table_widget.move(0, 0)
        fnt = self.table_widget.font()
        fnt.setPointSize(9)
        self.table_widget.setFont(fnt)
        self.table_widget.verticalHeader().hide()
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setRowCount(records_count)
        self.table_widget.setColumnCount(column_count)
        self.table_widget.setHorizontalHeaderLabels(
            ["No", "   Date   ", " Time ", "Band", "   Call   ", "Mode", "RST r",
             "RST s", "      Name      ", "      QTH      ", " Comments ", " Time off ", " eQSL Rcvd "])
        for record in range(records_count):
            for column in range(column_count):
                self.table_widget.setItem(record, column,
                                          QTableWidgetItem(self.all_records[record][self.all_column[column]]))
        self.table_widget.resizeRowsToContents()
        self.table_widget.resizeColumnsToContents()
        total_score = 0
        for record in self.all_records:
            for i in range(len(self.rules)):
                if record['CALL'] == self.rules[i]['call'] and \
                        record['MODE'] == self.rules[i]['mode']:
                    total_score += int(self.rules[i]['score'])

        self.score_total_label.setText("Total score: " + str(total_score))


class Filter_log(QWidget):
    def __init__(self, settingsDict, All_records=None):
        super().__init__()
        self.settingsDict = settingsDict
        self.all_records = All_records
        self.allCollumn = ['records_number', 'QSO_DATE', 'TIME_ON', 'BAND', 'CALL', 'MODE', 'RST_RCVD', 'RST_SENT',
                           'NAME', 'QTH', 'COMMENTS', 'TIME_OFF', 'EQSL_QSL_SENT', 'CLUBLOG_QSO_UPLOAD_STATUS']

        self.initUI()

    def initUI(self):
        self.setGeometry(int(self.settingsDict['log-window-left']),
                         int(self.settingsDict['log-window-top']) + 50,
                         int(self.settingsDict['filter-width']),
                         int(self.settingsDict['filter-height']))
        self.setWindowIcon(QIcon('logo.png'))
        self.setWindowTitle('LinuxLog | Filter')
        style = "background-color:" + self.settingsDict['background-color'] + "; color:" + self.settingsDict[
            'color'] + ";"
        self.setStyleSheet(style)

        # Create table widget - "Buffer"
        self.tw_buffer = QTableWidget()
        self.tw_buffer.setColumnCount(len(self.allCollumn) + 1)
        style_table = "background-color:" + self.settingsDict['form-background'] + "; color:" + self.settingsDict[
            'color-table'] + "; font: 12px;  gridline-color: " + self.settingsDict['solid-color'] + ";"
        self.tw_buffer.setStyleSheet(style_table)
        fnt = self.tw_buffer.font()
        fnt.setPointSize(9)
        self.tw_buffer.setHorizontalHeaderLabels(
            ["No", "     Date     ", "   Time   ", "Band", "   Call   ", "Mode", "RST r",
             "RST s", "      Name      ", "      QTH      ", " Comments ",
             " Time off ", " eQSL Sent ", "Club Log Sent", "Operation"])
        self.tw_buffer.resizeColumnsToContents()

        # Create layer button for "Buffer table"
        self.bt_for_buffer = QHBoxLayout()

        self.bt_clear_all = QPushButton('Clear all "Buffer"')
        self.bt_clear_all.setFixedWidth(70)
        self.bt_clear_all.setFixedHeight(20)
        self.bt_clear_all.clicked.connect(self.clear_all_buffer)
        self.bt_for_buffer.addWidget(self.bt_clear_all)

        # Create layer button for find
        self.bt_for_find = QHBoxLayout()
        # Button add all
        self.bt_add_all = QPushButton("Add all")
        self.bt_add_all.setFixedWidth(70)
        self.bt_add_all.setFixedHeight(20)
        self.bt_add_all.clicked.connect(self.add_all_find)
        # Button clear find
        self.bt_clear_find = QPushButton('Clear all "Find"')
        self.bt_clear_find.setFixedWidth(70)
        self.bt_clear_find.setFixedHeight(20)
        self.bt_clear_find.clicked.connect(self.clear_all_find)

        self.bt_for_find.addWidget(self.bt_add_all)
        self.bt_for_find.addWidget(self.bt_clear_find)

        # Create table widget Find
        self.tw_find = QTableWidget()
        self.tw_find.setColumnCount(len(self.allCollumn) + 1)
        style_table = "background-color:" + self.settingsDict['form-background'] + "; color:" + self.settingsDict[
            'color-table'] + "; font: 12px;  gridline-color: " + self.settingsDict['solid-color'] + ";"
        self.tw_find.setStyleSheet(style_table)
        fnt = self.tw_buffer.font()
        fnt.setPointSize(9)
        self.tw_find.setHorizontalHeaderLabels(
            ["No", "     Date     ", "   Time   ", "Band", "   Call   ", "Mode", "RST r",
             "RST s", "      Name      ", "      QTH      ", " Comments ",
             " Time off ", " eQSL Sent ", "Club Log Sent", "Operation"])
        self.tw_find.resizeColumnsToContents()

        # Create horizontal layer with two vertical layers with fields and button
        self.horizontal_layer_fields = QHBoxLayout()
        self.find_fields = QVBoxLayout()
        # call field
        self.call_find_lay = QHBoxLayout()
        self.call_label = QLabel("Call (with RegExp)")
        self.call_label.setFixedWidth(150)
        self.call_label.setStyleSheet(style)

        self.call_input = QLineEdit()
        self.call_input.setFixedWidth(120)
        self.call_input.setFixedHeight(30)
        self.call_input.setStyleSheet(style_table)
        self.call_find_lay.addWidget(self.call_label)
        self.call_find_lay.addWidget(self.call_input)

        # Band field
        self.band_find_lay = QHBoxLayout()
        self.band_label = QLabel("Band(s)")
        self.band_label.setFixedWidth(150)
        self.band_label.setStyleSheet(style)
        self.band_input = QLineEdit()
        self.band_input.setFixedWidth(120)
        self.band_input.setFixedHeight(30)
        self.band_input.setStyleSheet(style_table)

        self.band_find_lay.addWidget(self.band_label)
        self.band_find_lay.addWidget(self.band_input)

        # Freq field
        self.freq_find_lay = QHBoxLayout()
        self.freq_label = QLabel("Freq(s)")
        self.freq_label.setFixedWidth(150)
        self.freq_label.setStyleSheet(style)
        self.freq_input = QLineEdit()
        self.freq_input.setFixedWidth(120)
        self.freq_input.setFixedHeight(30)
        self.freq_input.setStyleSheet(style_table)

        self.freq_find_lay.addWidget(self.freq_label)
        self.freq_find_lay.addWidget(self.freq_input)

        # Mode field
        self.mode_find_lay = QHBoxLayout()
        self.mode_label = QLabel("Mode(s)")
        self.mode_label.setFixedWidth(150)
        self.mode_label.setStyleSheet(style)
        self.mode_input = QLineEdit()
        self.mode_input.setFixedWidth(120)
        self.mode_input.setFixedHeight(30)
        self.mode_input.setStyleSheet(style_table)

        self.mode_find_lay.addWidget(self.mode_label)
        self.mode_find_lay.addWidget(self.mode_input)

        # Date field
        self.date_find_lay = QHBoxLayout()
        self.date_label = QLabel("Date(s)")
        self.date_label.setFixedWidth(150)
        self.date_label.setStyleSheet(style)
        self.date_input = QLineEdit()
        self.date_input.setFixedWidth(120)
        self.date_input.setFixedHeight(30)
        self.date_input.setStyleSheet(style_table)

        self.date_find_lay.addWidget(self.date_label)
        self.date_find_lay.addWidget(self.date_input)

        # Time field
        self.time_find_lay = QHBoxLayout()
        self.time_label = QLabel("Time(s)")
        self.time_label.setFixedWidth(150)
        self.time_label.setStyleSheet(style)
        self.time_input = QLineEdit()
        self.time_input.setFixedWidth(120)
        self.time_input.setFixedHeight(30)
        self.time_input.setStyleSheet(style_table)

        self.time_find_lay.addWidget(self.time_label)
        self.time_find_lay.addWidget(self.time_input)

        # Search button lay
        self.search_find_lay = QHBoxLayout()
        self.search_bt = QPushButton("Search")
        self.search_bt.setFixedWidth(120)
        self.search_bt.setFixedHeight(30)
        self.search_bt.setStyleSheet(style)
        self.search_label = QLabel()
        self.search_label.setFixedWidth(150)
        self.search_label.setStyleSheet(style)

        self.search_find_lay.addWidget(self.search_bt)
        self.search_find_lay.addWidget(self.search_label)

        self.find_fields.addLayout(self.call_find_lay)
        self.find_fields.addLayout(self.band_find_lay)
        self.find_fields.addLayout(self.freq_find_lay)
        self.find_fields.addLayout(self.mode_find_lay)
        self.find_fields.addLayout(self.date_find_lay)
        self.find_fields.addLayout(self.time_find_lay)
        self.find_fields.addLayout(self.search_find_lay)

        self.buffer_fields = QVBoxLayout()

        # Send eQSL PB
        self.bt_send_eqsl = QPushButton("Send eQSL")
        self.bt_send_eqsl.setFixedWidth(150)
        self.bt_send_eqsl.clicked.connect(self.send_eqsl)

        # send to CL PB
        self.bt_send_cl = QPushButton("Send to Club Log")
        self.bt_send_cl.setFixedWidth(150)
        self.bt_send_cl.clicked.connect(self.send_cl)

        # export to ADI
        self.bt_export_adi = QPushButton('Export to ADI')
        self.bt_export_adi.setFixedWidth(150)
        self.bt_export_adi.clicked.connect(self.export_adi)

        # delete from Club Log button
        self.bt_delete_cl = QPushButton("Delete from Club Log")
        self.bt_delete_cl.setFixedWidth(150)
        self.bt_delete_cl.clicked.connect(self.delete_cl)

        self.buffer_fields.addWidget(self.bt_send_eqsl)
        self.buffer_fields.addWidget(self.bt_send_cl)
        self.buffer_fields.addWidget(self.bt_export_adi)
        self.buffer_fields.addWidget(self.bt_delete_cl)

        self.horizontal_layer_fields.addLayout(self.find_fields)
        self.horizontal_layer_fields.addLayout(self.buffer_fields)
        self.filter_main_lay = QVBoxLayout()
        self.filter_main_lay.addLayout(self.horizontal_layer_fields)
        self.filter_main_lay.addWidget(self.tw_find)
        self.filter_main_lay.addLayout(self.bt_for_find)
        self.filter_main_lay.addWidget(self.tw_buffer)
        self.filter_main_lay.addLayout(self.bt_for_buffer)
        self.setLayout(self.filter_main_lay)

    def clear_all_buffer(self):
        print("clear_all_buffer")

    def add_all_find(self):
        print("add_all_find")

    def clear_all_find(self):
        print("clear_all_find")

    def send_eqsl(self):
        print("send_eqsl")

    def send_cl(self):
        print("send_cl")

    def export_adi(self):
        print("export_adi")

    def delete_cl(self):
        print("delete_cl")
