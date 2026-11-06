#!/usr/bin/python3
# -*- coding: utf-8 -*-
#from PyQt6 import QtCore
import signal


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

    def __init__(self, settingsDict, log_form, adi_file, diplomname='', list_data=[]):
        super().__init__()
        # print("Diplom_form(QWidget) init_")
        self.logForm = log_form
        self.diplomname = diplomname
        self.settingsDict = settingsDict
        self.adi = adi_file
        self.list_data = list_data
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
        settings_list = []
        # Validate Line edit name of awards
        flag = 0
        if self.name_input.text().strip() != '':
            flag = 1
        else:
            flag = 0
            self.name_input.setStyleSheet("border: 2px solid #DD5555;")
        # Validate color button
        if self.color_button.text() != 'Select color':
            flag = 1
        else:
            flag = 0
            self.color_button.setStyleSheet("border: 2px solid #DD5555;")
        # end validate
        # logic of saving award data
        if flag == 1:
            name_programm = self.name_input.text().strip()
            score_complite = self.score_input.text().strip()
            repeats = self.repeat_combo.currentIndex()
            only_band = self.only_bands.currentText()
            count_sps = self.sps_table_widget.rowCount()
            for row in range(count_sps):
                score_sps = '0'
                if self.sps_table_widget.item(row, 0) != None:
                    if self.sps_table_widget.item(row, 1) != None:
                        if self.sps_table_widget.item(row, 1).text().isnumeric():
                            score_sps = str(self.sps_table_widget.item(row, 1).text())
                    print('Item content call', self.sps_table_widget.item(row, 0).text())
                    list_to_json.append({'call': self.sps_table_widget.item(row, 0).text().upper(),
                                         'score': score_sps,
                                         'mode': self.combo_mode_list[row]['combo' + str(row)].currentText(),
                                         'name': name_programm,
                                         'colorR': self.colorR,
                                         'colorG': self.colorG,
                                         'colorB': self.colorB,
                                         'color_name': self.color_name,
                                         'repeats': repeats,
                                         'only_bands_enable': self.only_bands_checkable.isChecked(),
                                         'only_bands': self.only_bands.currentText(),
                                         'score_complite': score_complite,
                                         'prefix': self.prefix_check_box.isChecked()
                                         })

            self.write_rules_to_file(list_to_json, name_output_file=name_programm)
            if self.settingsDict['diploms-json'] != "":
                settings_list = json.loads(self.settingsDict['diploms-json'])
            else:
                self.settingsDict['diploms-json'] = json.dumps([{'name_programm': name_programm}])
                main.Settings_file.update_file_to_disk(self)
            if len(settings_list) > 0:
                for i in range(len(settings_list)):
                    if name_programm == str(settings_list[i]['name_programm']) and self.diplomname == '':
                        std.std.message(self, "Programm with that name already exists", "Repeats")
                        repeat_flag = 1
                        break
                    else:
                        repeat_flag = 0
            else:
                repeat_flag = 0
            if repeat_flag == 0:
                if self.diplomname == '':
                    settings_list.append({'name_programm': name_programm})
                    self.settingsDict['diploms-json'] = json.dumps(settings_list)
                    main.Settings_file.update_file_to_disk(self)

                    self.logForm.menu_add(name_menu=self.name_input.text())
                    self.adi.create_adi(name_programm + ".adi")
                    self.close()
                else:
                    programs = len(settings_list)
                    for i in range(programs):
                        if settings_list[i]['name_programm'] == self.diplomname:
                            self.adi.rename_adi(settings_list[i]['name_programm'] + ".adi",
                                                self.name_input.text() + ".adi")
                            settings_list[i]['name_programm'] = self.name_input.text()

                    self.settingsDict['diploms-json'] = json.dumps(settings_list)
                    main.Settings_file.update_file_to_disk(self)
                    self.logForm.menu_rename_diplom()
                    self.logForm.diploms_init()
                    self.logForm.menu()
                    self.close()
            self.logForm.diploms_init()
        elif flag == 0:
            pass

    def write_rules_to_file(self, data_to_json, name_output_file):
        filename = str(name_output_file).strip() + '.rules'
        with open(Path(__file__).parent/filename, 'w') as f:
            f.write(json.dumps(data_to_json))


class Diplom(QObject):
    name = ''

    def __init__(self, name, settingsDict, parent=''):
        super().__init__()
        self.name = name
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
        self.adiFile = main.Adi_file("in", self.settingsDict, self.diplomDataList[0]['name'] + ".adi")
        # 3
        self.qsoData = self.getQsoData()

    def getQsoData(self):
        '''
        Parse .adi file and generated the dictionary object for QSOs
        :return: qsoDataList - object [{... QSO 1 info...},{...QSO 2 info...}]
        '''
        qsoDataList = parse.getAllRecord(self.allCollumn, self.diplomDataList[0]['name'] + ".adi", key="import")
        print("->-" * 10)
        print(qsoDataList)
        print("==" * 10)
        return qsoDataList

    def getRules(self):
        with open(Path(__file__).parent/self.name + ".rules", 'r') as rules:
            s = rules.readline()
            # print("s", s)
            rulesObject = json.loads(s)
        return rulesObject

    def complete(self):
        score = self.getScore()
        scoreComplete = self.diplomDataList[0]['score_complite']
        if int(score) >= int(scoreComplete):
            return True
        return False

    def getScore(self):
        totalScore = 0
        for callFromRules in self.diplomDataList:
            for qso in self.qsoData:
                if qso['CALL'] == callFromRules['call']:
                    totalScore = totalScore + int(callFromRules['score'])

        return totalScore

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
        self.file = file
        self.file_rules = file_rules.strip()
        self.allCollumn = ['records_number', 'QSO_DATE', 'TIME_ON', 'BAND', 'CALL', 'MODE', 'RST_RCVD', 'RST_SENT',
                           'NAME', 'QTH', 'COMMENTS', 'TIME_OFF', 'eQSL_QSL_RCVD']
        self.allRecord = parse.getAllRecord(self.allCollumn, self.file)
        # print("diplom:", self.allRecord)
        self.decode_data = self.get_rules(self.file_rules)
        if settingsDict != '':
            self.settingsDict = settingsDict

    def get_rules(self, name):
        with open(Path(__file__).parent/name, "r") as f:
            return json.load(f)

    def search_call_in_base(self, call):
        search_calls = []

        # records = parse.getAllRecord(self.allCollumn, self.file)
        record_count = len(self.allRecord)
        for record in range(record_count):
            if self.allRecord[record]['CALL'] == call:
                search_calls.append(self.allRecord[record])
                # print("AllRecords:_>", self.allRecord[record])
                # print("Search_call_in_base:_>", records[record])
        return search_calls

    def get_color_bg(self):
        color = QColor(int(self.decode_data[0]['colorR']),
                       int(self.decode_data[0]['colorG']),
                       int(self.decode_data[0]['colorB']))

        return color

    def filter(self, call_dict):
        '''

        This function chek rules for qso.
        The function get on input dictionary with data qso (call, mode,
        band) and check it on rules for currently awards object
            :param call_dict: dictionary with keys: call, mode, band
            :return: boolean
        '''
        print("HEllo I am filter")
        count_sps_call = len(self.decode_data)
        call_found_status = 0
        for i in range(count_sps_call):
            if self.decode_data[i]['prefix']:
                if call_dict['call'].find(self.decode_data[i]['call']) != -1:
                    call_found_status = 1
            else:
                if self.decode_data[i]['call'] == call_dict['call']:
                    call_found_status = 1

        # if filter using for cluster
        if call_dict['mode'] == 'cluster' and call_found_status == 1:
            return True
        else:
            # print("repeats:_>", self.decode_data[0]['repeats'])
            found_records_in_base_list = self.search_call_in_base(call_dict['call'])
            # repeat 0 - resolved other bands

            if str(self.decode_data[0]['repeats']) == '0' and call_found_status == 1:

                # print("Found QSO(s) in base", len(found_records_in_base_list))

                if len(found_records_in_base_list) == 0:

                    return True
                else:
                    count_records_in_base_list = len(found_records_in_base_list)
                    flag = True
                    for i in range(count_records_in_base_list):
                        if found_records_in_base_list[i]['BAND'] == call_dict['band']:
                            flag = False
                    if flag:
                        return True
                    else:
                        return False

            # repeat 1 - resolved other mods
            if str(self.decode_data[0]['repeats']) == '1' and call_found_status == 1:
                # print("Found QSO(s) in base", found_records_in_base_list)
                if len(found_records_in_base_list) == 0:
                    for i in range(count_sps_call):
                        if (self.decode_data[i]['mode'] == 'all'):
                            if call_dict['mode'] == self.decode_data[i]['mode'] \
                                    and call_dict['call'] == self.decode_data[i]['call']:
                                return True
                            else:
                                return False
                        if (self.decode_data[i]['mode'] == 'prefix'):
                            if call_dict['mode'] == self.decode_data[i]['mode'] \
                                    and call_dict['call'].find(self.decode_data[i]['call']) != -1:
                                return True
                            else:
                                return False

                else:
                    count_records_in_base_list = len(found_records_in_base_list)
                    flag = True

                    for i in range(count_sps_call):
                        if call_dict['mode'] == self.decode_data[i]['mode'] \
                                and call_dict['call'] == self.decode_data[i]['call']:

                            for j in range(count_records_in_base_list):
                                if call_dict['mode'] == found_records_in_base_list[j]['MODE']:
                                    flag = False
                        else:
                            flag = False
                    if flag:
                        return True
                    else:
                        return False

            # repeat 2 - resolved other mods and bands
            if str(self.decode_data[0]['repeats']) == '2' and call_found_status == 1:
                # print("Found QSO(s) in base", len(found_records_in_base_list),
                #     found_records_in_base_list)
                mode_status = 0
                for i in range(count_sps_call):
                    # print("call_dict['mode']", call_dict['mode'], "self.decode_data[i]['mode']",
                    #  self.decode_data[i]['mode'])
                    if (self.decode_data[i]['mode'] == 'all'):
                        if call_dict['mode'] == self.decode_data[i]['mode'] \
                                and call_dict['call'] == self.decode_data[i]['call']:
                            mode_status = 1
                    if (self.decode_data[i]['mode'] == 'prefix'):
                        if call_dict['mode'] == self.decode_data[i]['mode'] \
                                and call_dict['call'].find(self.decode_data[i]['call']) != -1:
                            mode_status = 1

                count_records_in_base_list = len(found_records_in_base_list)
                # print ("mode status:_>", mode_status)
                # print("Found in Base", len(found_records_in_base_list), found_records_in_base_list)
                if count_records_in_base_list == 0 and mode_status == 1:
                    # print("mode ok")
                    return True
                if count_records_in_base_list > 0 and mode_status == 1:
                    flag = True
                    for j in range(count_records_in_base_list):
                        if call_dict['mode'] == found_records_in_base_list[j]['MODE'] \
                                or call_dict['band'] == found_records_in_base_list[j]['BAND']:
                            # print("QSO on this Band and this Mode found", found_records_in_base_list[j])
                            flag = False

                    if flag:
                        # print("Filter out True")
                        return True
                    else:
                        # print("Filter out False")
                        return False

            # repeat 3 - resolved other mods and bands
            if str(self.decode_data[0]['repeats']) == '3' \
                    and call_found_status == 1 \
                    and len(found_records_in_base_list) == 0:
                flag = False
                for i in range(count_sps_call):

                    if call_dict['mode'] == self.decode_data[i]['mode'] \
                            and call_dict['call'] == self.decode_data[i]['call']:
                        mode_status = 1
                        flag = True
            else:
                flag = False
            if flag:
                return True
            else:
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
        # print("List_data", list_data)
        index = len(list_data)
        with open(Path(__file__).parent/self.file, 'a') as file:
            stringToAdiFile = "<BAND:" + str(len(list_data['BAND'])) + ">" + list_data['BAND'] + "<CALL:" + \
                              str(len(list_data['CALL'])) + ">"

            stringToAdiFile = stringToAdiFile + list_data['CALL'] + "<FREQ:" + str(
                len(list_data['FREQ'])) + ">" + \
                              list_data['FREQ']
            stringToAdiFile = stringToAdiFile + "<MODE:" + str(len(list_data['MODE'])) + ">" + list_data[
                'MODE'] + "<OPERATOR:" + str(len(list_data['OPERATOR']))
            stringToAdiFile = stringToAdiFile + ">" + list_data['OPERATOR'] + "<QSO_DATE:" + str(
                len(list_data['QSO_DATE'])) + ">"
            stringToAdiFile = stringToAdiFile + list_data['QSO_DATE'] + "<TIME_ON:" + str(
                len(list_data['TIME_ON'])) + ">"
            stringToAdiFile = stringToAdiFile + list_data['TIME_ON'] + "<RST_RCVD:" + \
                              str(len(list_data['RST_RCVD'])) + ">" + list_data['RST_RCVD']
            stringToAdiFile = stringToAdiFile + "<RST_SENT:" + str(len(list_data['RST_SENT'])) + ">" + \
                              list_data['RST_SENT'] + "<NAME:" + str(len(list_data['NAME'])) + ">" + \
                              list_data['NAME'] + \
                              "<QTH:" + str(len(list_data['QTH'])) + ">" + list_data['QTH'] + "<COMMENTS:" + \
                              str(len(list_data['COMMENTS'])) + ">" + list_data['COMMENTS'] + "<TIME_OFF:" + \
                              str(len(list_data['TIME_OFF'])) + ">" + list_data[
                                  'TIME_OFF'] + "<eQSL_QSL_RCVD:1>Y<EOR>\n"
            # print("string to ADI:", stringToAdiFile)
            file.write(stringToAdiFile)
            # print ("list_data:_>", list_data)
            self.allRecord.append(list_data)

    def get_count_qso(self):
        return len(self.allRecord)

    def get_all_qso(self):
        return self.allRecord

    def get_data(self):
        return self.decode_data

    def del_dilpom(self, name_diplom, settingsDict, logForm):
        self.settingsDict = settingsDict
        if self.settingsDict['diploms-json'] != '':
            list_string = json.loads(self.settingsDict['diploms-json'])
            # print(type(list_string))
            count_diploms = len(list_string)
            for i in range(count_diploms):
                if list_string[i]['name_programm'] == name_diplom:
                    del list_string[i]
            self.settingsDict['diploms-json'] = json.dumps(list_string)
            main.Settings_file.update_file_to_disk(self)

        # print("del_dilpom", list_string)
        os.remove(name_diplom + '.rules')
        os.remove(name_diplom + '.adi')
        logForm.menu_rename_diplom()
        logForm.diploms_init()
        logForm.menu()

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
        self.rules = diplom.get_rules(diplom, self.diplom_name + '.rules')
        self.score_final_label.setText("Total score need: " + str(self.rules[0]['score_complite']))
        self.all_records = parse.getAllRecord(self.all_column, self.diplom_name + '.adi')
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
