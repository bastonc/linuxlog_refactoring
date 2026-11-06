#!/usr/bin/python3
# -*- coding: utf-8 -*-
import signal
import sys



import re
import os
import datetime
import traceback
import subprocess

import ext
import cat
from pathlib import  Path
import PyQt6.QtCore
from PyQt6.QtWidgets import QApplication, QProgressBar, QCheckBox, QMenu, QMessageBox, \
    QWidget, \
    QMainWindow, QTableWidget, QTabWidget, QTableWidgetItem, \
    QLineEdit, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QPlainTextEdit, QFrame
from PyQt6.QtCore import pyqtSignal, QObject, QEvent
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QAction
from PyQt6 import QtGui, QtCore
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtCore import QThread


def SIGSEGV_signal_arises(signalNum, stack):
    print(f"{signalNum} : SIGSEGV arises")
    # Your code

signal.signal(signal.SIGSEGV, SIGSEGV_signal_arises)

import json
import requests
import pymysql

from functools import partial
from os.path import expanduser
from pymysql.cursors import DictCursor
from bs4 import BeautifulSoup
# from gi.repository import Notify, GdkPixbuf

from time import gmtime, strftime, localtime, sleep

import internetworker
import time
import tci
import eqsl_inbox
import std
import settings
from cluster import ClusterThread
from qrzcom import QrzLogbook, QrzComApi
from rigctl import Rigctl_sender
from threads_lib import Rigctl_thread, RigctlMainLoop


class Settings_file:
    def update_file_to_disk(self):
        # self.settingsDict = self
        filename = 'settings.cfg'
        with open(Path(__file__).parent/filename, 'r') as f:
            old_data = f.readlines()
        for index, line in enumerate(old_data):
            key_from_line = line.split('=')[0]
            # print ("key_from_line:",key_from_line)
            for key in self.settingsDict:

                if key_from_line == key:
                    # print("key",key , "line", line)
                    old_data[index] = key + "=" + self.settingsDict[key] + "\n"
        with open(Path(__file__).parent/filename, 'w') as f:
            f.writelines(old_data)
        # print("Update_to_disk: ", old_data)
        return True


class Adi_file:

    def __init__(self, app_version, settingsDict, filename='log.adi'):
        self.APP_VERSION = app_version
        self.settingsDict = settingsDict
        self.filename = filename
        try:
            with open(Path(__file__).parent/self.filename, 'r') as file:  # read all strings

                self.strings_in_file = file.readlines()
        except Exception:
            self.strings_in_file = []

    def get_last_string(self):
        return len(self.strings_in_file)

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

        # print("hello  store_changed_qso method in Adi_file class\n", object)
        stringToAdiFile = "<BAND:" + str(len(obj['BAND'])) + ">" + obj['BAND'] + "<CALL:" + str(
            len(obj['CALL'])) + ">"

        stringToAdiFile = stringToAdiFile + obj['CALL'] + "<FREQ:" + str(len(obj['FREQ'])) + ">" + \
                          obj['FREQ']
        stringToAdiFile = stringToAdiFile + "<MODE:" + str(len(obj['MODE'])) + ">" + obj[
            'MODE'] + "<OPERATOR:" + str(len(obj['OPERATOR']))
        stringToAdiFile = stringToAdiFile + ">" + obj['OPERATOR'] + "<QSO_DATE:" + str(
            len(obj['QSO_DATE'])) + ">"
        stringToAdiFile = stringToAdiFile + obj['QSO_DATE'] + "<TIME_ON:" + str(
            len(obj['TIME_ON'])) + ">"
        stringToAdiFile = stringToAdiFile + obj['TIME_ON'] + "<RST_RCVD:" + \
                          str(len(obj['RST_RCVD'])) + ">" + obj['RST_RCVD']
        stringToAdiFile = stringToAdiFile + "<RST_SENT:" + str(len(obj['RST_SENT'])) + ">" + \
                          obj['RST_SENT'] + "<NAME:" + str(len(obj['NAME'])) + ">" + obj['NAME'] + \
                          "<QTH:" + str(len(obj['QTH'])) + ">" + obj['QTH'] + "<COMMENTS:" + \
                          str(len(obj['COMMENTS'])) + ">" + obj['COMMENTS'] + "<TIME_OFF:" + \
                          str(len(obj['TIME_OFF'])) + ">" + obj['TIME_OFF'] + "<EQSL_QSL_SENT:" + \
                          str(len(obj['EQSL_QSL_SENT'])) + ">" + obj['EQSL_QSL_SENT'] + \
                          "<CLUBLOG_QSO_UPLOAD_STATUS:" + str(len(obj['CLUBLOG_QSO_UPLOAD_STATUS'])) + ">" + obj[
                              'CLUBLOG_QSO_UPLOAD_STATUS'] + "<EOR>\n"
        print("store_changed_qso: stringToAdiFile", stringToAdiFile)

        self.strings_in_file[int(obj['string_in_file']) - 1] = stringToAdiFile
        with open(Path(__file__).parent/self.filename, 'w') as file:
            # file.seek(0, 2)
            file.writelines(self.strings_in_file)

        # print("this:", self.strings_in_file[int(object['string_in_file'])-1])

    def delete_qso_from_file(self, row_in_file):
        with open(Path(__file__).parent/self.filename, 'r') as file:
            # file.seek(0, 2)
            lines_in_file = file.readlines()

        print("Delete QSO from file \nAll lines", len(lines_in_file), "\nrow_in_files:_>", row_in_file)
        lines_in_file[int(row_in_file) - 1] = ''
        with open(Path(__file__).parent/self.filename, 'w') as file:
            # file.seek(0, 2)
            file.writelines(lines_in_file)

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
        print(band)
        band_table = {160: 1800,
                      80: 3500,
                      40: 7000,
                      30: 10000,
                      20: 14000,
                      17: 18000,
                      15: 21000,
                      12: 24890,
                      10: 28000}
        return band_table[int(band)]

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
        index = len(list_data)
        with open(Path(__file__).parent/name_file, 'w') as file:
            file.write(self.get_header())
            for qso in list_data:
                for field in fields_list:
                    if field[0] in qso is False or qso.get(field[0]) is None:
                        qso[field[0]] = ""

            for i in range(index):
                time_on_dirty = list_data[i].get('TIME_ON')
                time_on = str(time_on_dirty).replace(":", '')
                time_off_dirty = list_data[i].get('TIME_OFF')
                time_off = str(time_off_dirty).replace(":", '')
                qso_date_dirty = str(list_data[i].get('QSO_DATE'))
                qso_date = qso_date_dirty.replace("-", '')
                print(list_data)
                if list_data[i].get("FREQ") in (None,""):
                    freq = self.band_to_freq(int(list_data[i]["BAND"][:2]))

                stringToAdiFile = "<BAND:" + str(len(list_data[i]['BAND'])) + ">" + list_data[i][
                    'BAND'] + " <CALL:" + str(
                    len(list_data[i]['CALL'])) + ">"
                stringToAdiFile = stringToAdiFile + list_data[i]['CALL'] + " <FREQ:" + str(
                    len(str(freq))) + ">" + str(freq)
                stringToAdiFile = stringToAdiFile + " <MODE:" + str(len(list_data[i]['MODE'])) + ">" + list_data[i][
                    'MODE'] + " <OPERATOR:" + str(len(list_data[i]['OPERATOR']))
                stringToAdiFile = stringToAdiFile + ">" + list_data[i]['OPERATOR'] + " <QSO_DATE:" + str(len(qso_date)) + ">"
                stringToAdiFile = stringToAdiFile + qso_date + " <TIME_ON:" + str(len(time_on)) + ">"
                stringToAdiFile = stringToAdiFile + time_on + " <RST_RCVD:" + \
                                  str(len(list_data[i]['RST_RCVD'])) + ">" + list_data[i]['RST_RCVD']
                stringToAdiFile = stringToAdiFile + " <RST_SENT:" + str(len(list_data[i]['RST_SENT'])) + ">" + \
                                  list_data[i]['RST_SENT'] + " <NAME:" + str(len(list_data[i]['NAME'])) + ">" + \
                                  list_data[i]['NAME'] + \
                                  " <QTH:" + str(len(list_data[i]['QTH'])) + ">" + list_data[i]['QTH'] + " <COMMENTS:" + \
                                  str(len(list_data[i]['COMMENT'])) + ">" + list_data[i]['COMMENT'] + " <TIME_OFF:" + \
                                  str(len(time_off)) + ">" + time_off + " <EQSL_QSL_RCVD:" + \
                                  str(len(list_data[i]['EQSL_QSL_RCVD'])) + ">" + list_data[i]['EQSL_QSL_RCVD'] + \
                                  " <EQSL_QSL_SENT:" + str(len(list_data[i]['EQSL_QSL_SENT'])) + ">" + list_data[i][
                                      'EQSL_QSL_SENT'] + \
                                  " <CLUBLOG_QSO_UPLOAD_STATUS:" + str(
                    len(list_data[i]['CLUBLOG_QSO_UPLOAD_STATUS'])) + ">" + list_data[i][
                                      'CLUBLOG_QSO_UPLOAD_STATUS'] + " <EOR>\n"

                file.write(stringToAdiFile)


    def create_adi(self, name):
        with open(Path(__file__).parent/name, 'w') as f:
            f.writelines(self.get_header())


class Filter_event_table_qso(QObject):

    def eventFilter(self, widget, event):

        if event.type() == QEvent.Type.Wheel:
            logWindow.append_record()
            print("Scroll__")  # do something useful
            # you could emit a signal here if you wanted

            return True
        else:
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
            # print(f"widget {widget}")
            textCall = logForm.inputCall.text()

            if textCall != '' and textCall != self.previous_call:
                self.previous_call = textCall
                foundList = db.search_qso_in_base(textCall)
                print("found_list", foundList)
                if foundList != ():
                    logForm.set_data_qso(foundList)
                else:
                    logForm.get_info_from_qrz(textCall)
                    print("Not found in Base")
                freq = logForm.get_freq()
                country = logForm.get_country(textCall)
                # print(country)
                if country != []:
                    logForm.set_country_label(country[0] + ' <h6 style="font-size: 10px;">ITU: ' + country[1] + '</h6>')

                if settingsDict['search-internet-window'] == 'True':

                    self.previous_call = textCall
                    self.img_search.set_callsign_for_search(textCall)
                    self.img_search.start()
                    if settingsDict['tci'] == 'enable':
                        try:
                            tci_sndr.set_spot(textCall, freq)
                        except:
                            print("Filter: Can't connect to TCI-server")

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



class Communicate(QObject):
    signalComplited = pyqtSignal(int)

class Qso_counter:
    def __init__(self, counter):
        self.counter = counter
        qso_counter = self.counter

class Log_Window_2(QWidget):

    def __init__(self):
        super().__init__()
        self.allCollumn = ['QSO_DATE', 'BAND', 'FREQ', 'CALL', 'MODE', 'RST_RCVD', 'RST_SENT', 'TIME_ON',
                           'NAME', 'QTH', 'COMMENT', 'TIME_OFF', 'EQSL_QSL_SENT', 'CLUBLOG_QSO_UPLOAD_STATUS', 'id', 'select']  #todo add field, 'select' for multi select
        self.fill_flag = 0
        self.qso_last_id = None
        self.select_id_list = []
        self.read_base_string = ReadStringDb(db=db, parent=self)
        self.read_base_string.dict_from_base.connect(self.fill_qso_table)
        self.read_base_string.fill_complite.connect(self.fill_complited)
        self.tableWidget_qso = QTableWidget()
        self.qrz_com_logbook = QrzLogbook(settingsDict)
        self.initUI()
        self.refresh_data()

    def initUI(self):
        '''
            Design of log window

        '''
        self.setGeometry(int(settingsDict['log-window-left']),
                         int(settingsDict['log-window-top']),
                         int(settingsDict['log-window-width']),
                         int(settingsDict['log-window-height']))


        self.setWindowTitle("General log")
        self.setWindowIcon(QIcon(f'{Path(__file__).parent }/logo.png'))
        if settingsDict['border_wnd'] == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(float(settingsDict['logWindow-opacity']))
        style = "background-color:" + settingsDict['background-color'] + "; color:" + settingsDict[
            'color'] + ";"
        self.setStyleSheet(style)
        self.event_qso_table = Filter_event_table_qso()
        self.tableWidget_qso.installEventFilter(self.event_qso_table)
        self.tableWidget_qso.move(0, 0)
        self.tableWidget_qso.verticalHeader().hide()
        style_table = "background-color:" + settingsDict['form-background'] + "; color:" + settingsDict[
            'color-table'] + "; font: 12px;  gridline-color: " + settingsDict['solid-color'] + ";"
        self.tableWidget_qso.setStyleSheet(style_table)
        fnt = self.tableWidget_qso.font()
        fnt.setPointSize(9)
        self.tableWidget_qso.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableWidget_qso.customContextMenuRequested.connect(self.context_menu)
        self.tableWidget_qso.setFont(fnt)
        self.tableWidget_qso.setColumnCount(len(self.allCollumn))
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

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


    def mouseDoubleClickEvent(self, event):
        self.setWindowTitle("LinuxLog")

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.RightButton:
            self.x = self.width()
            self.y = self.height()
            self.resize_wnd = event.pos()
            self.flag_button = "right"
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()
            self.flag_button = "left"

        print(event.button())

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
            print(event.globalPosition().y(), x_r, self.resize_wnd.x())
            self.resize(self.x - x_r, self.y - y_r)

    def append_qso(self):
        self.append_record()

    def append_record(self):
        count_col = len(self.allCollumn)
        # print("Bottom ---", self.tableWidget_qso.rowCount())
        for col in range(count_col):
            if self.allCollumn[col] == "id":
                if self.tableWidget_qso.item(self.tableWidget_qso.rowCount(), col):
                    start_id = self.tableWidget_qso.item(self.tableWidget_qso.rowCount(), col).text()
                else:
                    start_id = 0
        step = 100
        print("start_id", start_id)
        page = db.getRange(start_id, step)
        if page:
            page_count = len(page)
            col_count = len(self.allCollumn)
            for record in page:
                next_string = self.tableWidget_qso.rowCount()
                self.tableWidget_qso.insertRow(self.tableWidget_qso.rowCount())
                for col in range(col_count):
                    pole = self.allCollumn[col]
                    if self.allCollumn[col] == 'id':
                        self.tableWidget_qso.setItem(next_string, col,
                                                     self.protectionItem(
                                                         str(record[pole]),
                                                         Qt.ItemIsSelectable | Qt.ItemIsEnabled))
                        self.tableWidget_qso.item(next_string, col).setForeground(
                            QColor(settingsDict["color-table"]))

                        # QTableWidgetItem(self.allRecord[(self.allRows - 1) - row][pole]))
                    elif self.allCollumn[col] == 'QSO_DATE':
                        date = str(record[pole])
                        # date_formated = date[:4] + "-" + date[4:6] + "-" + date[6:]
                        # print(time_formated)
                        self.tableWidget_qso.setItem(
                            next_string, col,
                            self.protectionItem(
                                QTableWidgetItem(date),
                                Qt.ItemIsSelectable | Qt.ItemIsEnabled
                            )
                        )
                        self.tableWidget_qso.item(next_string, col).setForeground(
                            QColor(settingsDict["color-table"]))

                    elif self.allCollumn[col] == 'TIME_ON':
                        time = str(record[pole])
                        # time_formated = time[:2] + ":" + time[2:4] + ":" + time[4:]
                        # print(time_formated)
                        self.tableWidget_qso.setItem(
                            next_string, col,
                            self.protectionItem(
                                QTableWidgetItem(time),
                                Qt.ItemIsSelectable | Qt.ItemIsEnabled
                            )
                        )
                        self.tableWidget_qso.item(next_string, col).setForeground(
                            QColor(settingsDict["color-table"]))
                    elif self.allCollumn[col] == 'TIME_OFF':
                        time = str(record[pole])
                        # time_formated = time[:2] + ":" + time[2:4] + ":" + time[4:]
                        self.tableWidget_qso.setItem(
                            next_string, col,
                            self.protectionItem(
                                QTableWidgetItem(time),
                                Qt.ItemIsSelectable | Qt.ItemIsEnabled
                            )
                        )
                        self.tableWidget_qso.item(next_string, col).setForeground(
                            QColor(settingsDict["color-table"]))

                    else:
                        if record[pole] is None:
                            record[pole] = ''
                        self.tableWidget_qso.setItem(
                            next_string, col,
                            self.protectionItem(
                                str(record[pole]),
                                Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                        )
                        self.tableWidget_qso.item(next_string, col).setForeground(
                            QColor(settingsDict["color-table"]))

                    if record['EQSL_QSL_SENT'] == 'Y':
                        self.tableWidget_qso.item(next_string, col).setBackground(
                            QColor(settingsDict['eqsl-sent-color']))

            self.tableWidget_qso.resizeRowsToContents()
            self.tableWidget_qso.resizeColumnsToContents()
            self.tableWidget_qso.repaint()

        # print ("Bottom", page)

    def refresh_data_button(self):
        # self.tableWidget_qso.clear()
        self.refresh_data()

    def filter_log_pressed(self):
        self.filter_log = ext.Filter_log(settingsDict)
        self.filter_log.show()

    #  print("filter_log_pressed")

    def context_menu(self, point):

        self.collumns_index = std.std.get_index_column(self, self.tableWidget_qso)
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)
        context_menu = QMenu()
        style_table = f"font-size: 12px;  color: {settingsDict['color']}; background: {settingsDict['background-color']};"
        context_menu.setStyleSheet(style_table)
        # context_menu.setFixedWidth(120)
        # context_menu.set
        if self.tableWidget_qso.itemAt(point):
            index_row = self.tableWidget_qso.currentItem().row()
            call = self.tableWidget_qso.item(index_row, self.collumns_index['CALL']).text()
            delete_record = QAction("Delete QSO with " + call, context_menu)
            delete_record.triggered.connect(lambda:
                                            self.delete_qso(self.tableWidget_qso.currentItem().row()))
            edit_record = QAction("Edit QSO with " + call, context_menu)
            edit_record.triggered.connect(lambda:
                                          self.edit_qso(self.tableWidget_qso.currentItem().row()))
            send_eqsl = QAction("Send eQSL for " + call, context_menu)
            send_eqsl.triggered.connect(lambda:
                                        self.send_eqsl_for_call(self.tableWidget_qso.currentItem().row()))
            if self.tableWidget_qso.item(index_row, self.collumns_index['EQSL_QSL_SENT']).text() == "Y":
                send_eqsl.setEnabled(False)
            else:
                send_eqsl.setEnabled(True)
            # Set add to Club log menu
            send_to_clublog = QAction("Send QSO to Club log", context_menu)
            send_to_clublog.triggered.connect(lambda:
                                              self.sent_clublog_for_call(self.tableWidget_qso.currentItem().row()))
            if self.tableWidget_qso.item(index_row, self.collumns_index['CLUBLOG_QSO_UPLOAD_STATUS']).text() == "Y" \
                    or self.tableWidget_qso.item(index_row,
                                                 self.collumns_index['CLUBLOG_QSO_UPLOAD_STATUS']).text() == "M":
                send_to_clublog.setEnabled(False)
            else:
                send_to_clublog.setEnabled(True)
            # Set Delete from Club log menu
            del_from_clublog = QAction("Delete QSO from Club log", context_menu)
            del_from_clublog.triggered.connect(lambda: self.del_from_clublog(self.tableWidget_qso.currentItem().row()))
            if self.tableWidget_qso.item(index_row, self.collumns_index['CLUBLOG_QSO_UPLOAD_STATUS']).text() == "Y" \
                    or self.tableWidget_qso.item(index_row,
                                                 self.collumns_index['CLUBLOG_QSO_UPLOAD_STATUS']).text() == "M":
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

    # print(self.tableWidget_qso.mapToGlobal(point))

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
        self.columns_index = std.std.get_index_column(self, self.tableWidget_qso)
        self.record_id = self.tableWidget_qso.item(row, self.columns_index['id']).text()
        row_data = self.data_from_row(row)
        time_string = std.std.std_time(self, row_data["time"])

        # time_to_adi = time_string[:2]+":"+time_string[2:4]+":"+time_string[4:]
        # print ("time_to_adi", time_to_adi)
        adi_string = "<BAND:" + str(len(str(row_data['band']))) + ">" + str(row_data['band']) + "M" \
                                                                                                "<CALL:" + str(
            len(str(row_data['call']))) + ">" + str(row_data['call']) + \
                     "<QSO_DATE:" + str(len(str(row_data['date']))) + ">" + str(row_data['date']) + \
                     "<FREQ:" + str(len(str(row_data['freq']))) + ">" + str(row_data['freq']) + \
                     "<MODE:" + str(len(str(row_data['mode']))) + ">" + str(row_data['mode']) + \
                     "<OPERATOR:" + str(len(str(row_data['operator']))) + ">" + str(row_data['operator']) + \
                     "<TIME_ON:" + str(len(time_string)) + ">" + str(time_string) + \
                     "<RST_RCVD:" + str(len(str(row_data['rstR']))) + ">" + str(row_data['rstR']) + \
                     "<RST_SENT:" + str(len(str(row_data['rstS']))) + ">" + str(row_data['rstS']) + \
                     "<NAME:" + str(len(str(row_data['name']))) + ">" + str(row_data['name']) + \
                     "<QTH:" + str(len(str(row_data['qth']))) + ">" + str(row_data['qth']) + \
                     "<COMMENTS:" + str(len(str(row_data['comment']))) + ">" + str(row_data['comment']) + \
                     "<TIME_OFF:" + str(len(time_string)) + ">" + str(time_string) + \
                     "<EQSL_QSL_SENT:" + str(len(str(row_data['EQSL_QSL_SENT']))) + ">" + str(
            row_data['EQSL_QSL_SENT']) + \
                     "<EOR>"

        try:
            clublog = internetworker.Clublog(settingsDict, adi_string=adi_string)
            clublog.sent_qso_no.connect(self.clublog_sent_no_call)
            clublog.sent_qso_ok.connect(self.clublog_sent_ok_call)
            response = clublog.add_record()
            #  print(response.status_code, response.content)
            if response.status_code == 200:
                #     print("response for Club log:_>", response, response.headers)
                std.std.message(self, "Club log: " + response.content.decode(settingsDict['encodeStandart']),
                                "<p style='color: green;'><b>OK</b></p>")
                row = self.tableWidget_qso.currentItem().row()
                self.tableWidget_qso.setItem(row, self.collumns_index['CLUBLOG_QSO_UPLOAD_STATUS'],
                                             QTableWidgetItem("Y"))
                self.store_change_record(row)
            else:
                #       print("response for Club log:_>", response, response.content)
                std.std.message(self,
                                "Club log: " + response.content.decode(settingsDict['encodeStandart']) + "\n",
                                "<p style='color: red;'>ERROR</p>")

        except Exception:
            std.std.message(self,
                            "<b>Can't sent to Club log</b><br>" + traceback.format_exc(),
                            "<p style='color: red;'>ERROR Club log</p>")

    def del_from_clublog(self, row):
        record_object = self.data_from_row(row)
        # print("Standatrt record_object:_>", record_object)
        club_log = internetworker.Clublog(settingsDict)
        club_log.del_qso_ok.connect(self.del_from_clublog_ok)
        club_log.del_qso_no.connect(self.del_from_clublog_no)
        club_log.network_error.connect(self.network_error)
        club_log.del_record(record_object)

    @QtCore.pyqtSlot(object)
    def clublog_sent_ok_call(self, response):
        self.tableWidget_qso.setItem(self.row, self.columns_index['CLUBLOG_QSO_UPLOAD_STATUS'], QTableWidgetItem('Y'))
        self.store_change_record(row_arg=self.row)
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot(object)
    def clublog_sent_no_call(self, response):
        self.tableWidget_qso.setItem(self.row, self.columns_index['CLUBLOG_QSO_UPLOAD_STATUS'], QTableWidgetItem('N'))
        # self.store_change_record(row_arg=self.row)
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot(object)
    def del_from_clublog_ok(self, response):
        print("Del response OK:_>", response)
        row = self.tableWidget_qso.currentItem().row()
        self.tableWidget_qso.setItem(row, self.collumns_index['CLUBLOG_QSO_UPLOAD_STATUS'], QTableWidgetItem("N"))
        std.std.message(self, "Club log: Delete " + response.content.decode(settingsDict['encodeStandart']),
                        "<p style='color: green;'><b>OK</b></p>")
        self.store_change_record(row)
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot(object)
    def del_from_clublog_no(self, response):
        print("Del response NO:_>", response, response.content)
        std.std.message(self, "Club log: Delete " + response.content.decode(settingsDict['encodeStandart']),
                        "<p style='color: red;'><b>ERROR</b></p>")
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot()
    def network_error(self):

        std.std.message(self, "<strong>Can't do it</strong><br>Check internet connection",
                        "<p style='color: red;'><b>ERROR</b></p>")

    def data_from_row(self, row):

        self.record_id = self.tableWidget_qso.item(row, self.collumns_index['id']).text()
        print(self.record_id)
        data_from_base = db.get_record_by_id(self.record_id)
        print(data_from_base)
        date = str(data_from_base[0]["QSO_DATE"]).replace("-", "")
        time_on = str(data_from_base[0]["TIME_ON"])
        # .replace(":","")
        time_off = str(data_from_base[0]["TIME_OFF"])
        # .replace(":", "")
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
            "operator": settingsDict['my-call']
        }
        # self.operator = All_records[int(data_from_string['record_number']) - 1]['OPERATOR']
        # data_from_string.update({"operator": self.operator})

        return data_from_string

    def send_eqsl_for_call(self, row):
        # row = self.tableWidget.currentItem().row()

        # record_number = self.tableWidget_qso.item(row, 0).text()
        self.collumns_index = std.std.get_index_column(self, self.tableWidget_qso)
        print("send_eqsl_for_call:_>", self.collumns_index)
        record_id = self.tableWidget_qso.item(row, self.collumns_index['id']).text()
        time_formated = std.std.std_time(self, self.tableWidget_qso.item(row, self.collumns_index['TIME_ON']).text())

        qso_data = db.get_record_by_id(record_id)
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
            settingsDict=settingsDict,
            recordObject=recordObject,
            std=std.std,
            parent_window=self)
        self.eqsl_send.send_ok.connect(self.procesing_row)
        self.eqsl_send.error_signal.connect(self.error_eqsl)

    @QtCore.pyqtSlot(name='send_eqsl_ok')
    def procesing_row(self):
        row = self.tableWidget_qso.currentItem().row()
        cols = self.tableWidget_qso.columnCount()
        # index_columns = std.std.get_index_column(self, self.tableWidget_qso)
        print("Processing_row:_>", self.collumns_index)
        self.tableWidget_qso.setItem(row, self.collumns_index['EQSL_QSL_SENT'], QTableWidgetItem("Y"))
        for i in range(cols):
            self.tableWidget_qso.item(row, i).setBackground(QColor(settingsDict['eqsl-sent-color']))
        self.store_change_record()
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)
        print("It's slot processing_row")

    @QtCore.pyqtSlot(name='error_sent_eqsl')
    def error_eqsl(self):

        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    def edit_qso(self, row):
        row = self.tableWidget_qso.currentItem().row()
        # self.collumns_index = std.std.get_index_column(self, self.tableWidget_qso)

        self.record_id = self.tableWidget_qso.item(row, self.collumns_index['id']).text()
        print("record_id", self.record_id)
        qso_data = db.get_record_by_id(self.record_id)
        date = self.tableWidget_qso.item(row, self.collumns_index['QSO_DATE']).text()
        time = self.tableWidget_qso.item(row, self.collumns_index['TIME_ON']).text()
        call = self.tableWidget_qso.item(row, self.collumns_index['CALL']).text()
        freq = qso_data[0]['FREQ']
        rstR = self.tableWidget_qso.item(row, self.collumns_index['RST_RCVD']).text()
        rstS = self.tableWidget_qso.item(row, self.collumns_index['RST_SENT']).text()
        name = self.tableWidget_qso.item(row, self.collumns_index['NAME']).text()
        qth = self.tableWidget_qso.item(row, self.collumns_index['QTH']).text()
        self.operator_edit = qso_data[0]['OPERATOR']
        band = self.tableWidget_qso.item(row, self.collumns_index['BAND']).text()
        comment = self.tableWidget_qso.item(row, self.collumns_index['COMMENT']).text()
        time_off = self.tableWidget_qso.item(row, self.collumns_index['TIME_OFF']).text()
        EQSL_QSL_SENT = self.tableWidget_qso.item(row, self.collumns_index['EQSL_QSL_SENT']).text()

        mode = self.tableWidget_qso.item(row, self.collumns_index['MODE']).text()

        # GUI for edit window
        self.edit_window = QWidget()
        self.edit_window.setGeometry(int(settingsDict['log-window-left']),
                                     int(settingsDict['log-window-top']),
                                     300,
                                     500)
        self.edit_window.setWindowTitle('Edit QSO with ' + call)

        style = "background-color:" + settingsDict['background-color'] + "; color:" + \
                settingsDict['color'] + ";"
        style_table = "background-color:" + settingsDict['form-background'] + \
                      "; color:" + settingsDict['color-table'] + "; font: 12px; "
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

        if data_from_row['CLUBLOG_QSO_UPLOAD_STATUS'] == "Y" \
                or data_from_row['CLUBLOG_QSO_UPLOAD_STATUS'] == "M":
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

        print("eqsl:_>", eqsl)
        time_format = self.time_input.text().strip().replace(":", '')
        print("Time format:_>", time_format)
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
        # columns_index = std.std.get_index_column(self, self.tableWidget_qso)
        record_id = self.tableWidget_qso.item(row, self.collumns_index['id']).text()
        print(record_id, row)
        self.tableWidget_qso.removeRow(row)
        # self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)
        # self.tableWidget_qso.removeRow(0)
        db.delete_qso(record_id)

        # self.refresh_data()

    def changeEvent(self, event):

        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            if self.isMinimized():
                settingsDict['log-window'] = 'False'
                # print("log-window: changeEvent:_>", settingsDict['log-window'])
                # telnetCluster.showMinimized()
            elif self.isVisible():
                settingsDict['log-window'] = 'True'
                # print("log-window: changeEvent:_>", settingsDict['log-window'])
            QWidget.changeEvent(self, event)

    def refresh_data(self):
        if self.fill_flag == 0:
            self.fill_flag = 1
            self.tableWidget_qso.setRowCount(0)
            self.read_base_string.start()

    @QtCore.pyqtSlot(object)
    def fill_qso_table(self, dict_db):
        row = self.tableWidget_qso.rowCount()
        self.tableWidget_qso.insertRow(self.tableWidget_qso.rowCount())
        all_cols = len(self.allCollumn)
        for col in range(all_cols):
            field = self.allCollumn[col]
            if field == 'id':
                self.tableWidget_qso.setItem(row,
                                             col,
                                             self.protectionItem(
                                                 str(dict_db[field]),
                                                 Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled))
                self.tableWidget_qso.item(row, col).setForeground(
                    QColor(settingsDict["color-table"]))

            elif field == 'QSO_DATE':
                date = dict_db[field].strftime("%Y-%m-%d")
                self.tableWidget_qso.setItem(
                    row, col,
                    self.protectionItem(
                        QTableWidgetItem(date),
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                    )
                )
                self.tableWidget_qso.item(row, col).setForeground(
                    QColor(settingsDict["color-table"]))

            elif field == 'TIME_ON':
                time = str(dict_db[field])
                self.tableWidget_qso.setItem(
                    row, col,
                    self.protectionItem(
                        QTableWidgetItem(time),
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                    )
                )
                self.tableWidget_qso.item(row, col).setForeground(
                    QColor(settingsDict["color-table"]))

            elif field == 'TIME_OFF':
                time = str(dict_db[field])
                # time_formated = time[:2] + ":" + time[2:4] + ":" + time[4:]
                self.tableWidget_qso.setItem(
                    row, col,
                    self.protectionItem(
                        QTableWidgetItem(time),
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                    )
                )
                self.tableWidget_qso.item(row, col).setForeground(
                    QColor(settingsDict["color-table"]))
            elif field == "select":
                self.select_checkbox = QCheckBox()
                self.select_checkbox.setStyleSheet("QCheckBox::indicator"
                                                   "{ border : 1px solid " + settingsDict["color-table"] + "; "
                                                   "width: 10px;"
                                                   "height: 10px;"
                                                   "border-radius: 3px; }"
                                                   "QCheckBox::indicator:checked"
                                                   "{border: 2px solid rgb(255, 90, 90);"
                                                   "width: 10px;"
                                                   "height: 10px;"
                                                   "border-radius: 5px;"
                                                   "background-color:" + settingsDict["color-table"] + ";"
                                                    "}")
                self.select_checkbox.stateChanged.connect(self.multi_select_cheked)
                self.tableWidget_qso.setItem(row,col, QTableWidgetItem(""))
                self.tableWidget_qso.setCellWidget(row, col, self.select_checkbox)
            else:
                if dict_db[field] == "None":
                    dict_db[field] = ""
                self.tableWidget_qso.setItem(
                    row, col,
                    self.protectionItem(
                        str(dict_db[field]),
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                )
                self.tableWidget_qso.item(row, col).setForeground(
                    QColor(settingsDict["color-table"]))

            if dict_db['EQSL_QSL_SENT'] == 'Y':
                self.tableWidget_qso.item(row, col).setBackground(
                    QColor(settingsDict['eqsl-sent-color']))
        self.load_bar.setValue(round(row * 100 / len(self.allRows)))

    def multi_select_cheked(self):
        self.select_id_list.clear()
        for row in range(self.tableWidget_qso.rowCount()):
            if self.tableWidget_qso.cellWidget(row, self.tableWidget_qso.columnCount() - 1).isChecked():
                self.select_id_list.append(self.tableWidget_qso.item(row, self.tableWidget_qso.columnCount() - 2).text())

        if self.select_id_list:
            self.show_action_buttons()
        else:
            self.hide_action_buttons()

        print(f"id list {self.select_id_list}")
        print("checked")

    def show_action_buttons(self):
        self.multi_frame.show()

    def hide_action_buttons(self):
        self.multi_frame.hide()

    def multi_delete_qso(self):
        for id in self.select_id_list:
            print (f"select id: {id}")
            db.delete_qso(id)
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
        self.tableWidget_qso.sortByColumn(0, QtCore.Qt.SortOrder.DescendingOrder)
        self.tableWidget_qso.resizeRowsToContents()
        self.tableWidget_qso.resizeColumnsToContents()
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
            row = self.tableWidget_qso.currentItem().row()
        else:
            row = int(row_arg)
        record_id = self.tableWidget_qso.item(row, self.collumns_index['id']).text()
        date = str(self.tableWidget_qso.item(row, self.collumns_index['QSO_DATE']).text())
        date_formated = date.replace("-", "")
        time_str = str(self.tableWidget_qso.item(row, self.collumns_index['TIME_ON']).text())
        time_formated = time_str.replace(":", "")
        call = self.tableWidget_qso.item(row, self.collumns_index['CALL']).text()
        rstR = self.tableWidget_qso.item(row, self.collumns_index['RST_RCVD']).text()
        rstS = self.tableWidget_qso.item(row, self.collumns_index['RST_SENT']).text()
        name = self.tableWidget_qso.item(row, self.collumns_index['NAME']).text()
        qth = self.tableWidget_qso.item(row, self.collumns_index['QTH']).text()
        operator = settingsDict['my-call']
        band = self.tableWidget_qso.item(row, self.collumns_index['BAND']).text()
        comment = self.tableWidget_qso.item(row, self.collumns_index['COMMENT']).text()
        time_off = self.tableWidget_qso.item(row, self.collumns_index['TIME_OFF']).text()
        EQSL_QSL_SENT = self.tableWidget_qso.item(row, self.collumns_index['EQSL_QSL_SENT']).text()
        CLUBLOG_QSO_UPLOAD_STATUS = self.tableWidget_qso.item(row,
                                                              self.collumns_index['CLUBLOG_QSO_UPLOAD_STATUS']).text()
        mode = self.tableWidget_qso.item(row, self.collumns_index['MODE']).text()

        new_object = {'BAND': band, 'CALL': call, 'MODE': mode, 'OPERATOR': operator,
                      'QSO_DATE': date_formated, 'TIME_ON': time_formated, 'RST_RCVD': rstR, 'RST_SENT': rstS,
                      'NAME': name, 'QTH': qth, 'COMMENT': comment, 'TIME_OFF': time_off,
                      'EQSL_QSL_SENT': EQSL_QSL_SENT,
                      'CLUBLOG_QSO_UPLOAD_STATUS': CLUBLOG_QSO_UPLOAD_STATUS
                      }
        db.edit_qso(record_id, new_object)

    def refresh_interface(self):
        self.setGeometry(int(settingsDict['log-window-left']),
                         int(settingsDict['log-window-top']),
                         int(settingsDict['log-window-width']),
                         int(settingsDict['log-window-height']))

        self.update_color_schemes()

    def update_color_schemes(self):
        style = "background-color:" + settingsDict['background-color'] + "; color:" + \
                settingsDict['color'] + ";"

        style_form = "background-color:" + settingsDict['form-background'] + "; color:" + settingsDict[
            'color-table'] + "; font: 12px; gridline-color:" + settingsDict['solid-color'] + ";"
        self.tableWidget_qso.setStyleSheet(style_form)
        all_rows = self.tableWidget_qso.rowCount()
        all_cols = self.tableWidget_qso.columnCount()
        for row in range(all_rows):
            for col in range(all_cols):
                self.tableWidget_qso.item(row, col).setForeground(QColor(settingsDict["color-table"]))
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

        self.collumns_index = std.std.get_index_column(self, self.tableWidget_qso)
        if settingsDict['eqsl'] == 'enable':
            try:
                self.sync_eqsl = internetworker.Eqsl_services(settingsDict=settingsDict, recordObject=recordObject,
                                                              std=std.std, parent_window=self)
                self.sync_eqsl.send_ok.connect(self.eqsl_ok)
                self.sync_eqsl.error_signal.connect(self.eqsl_error)
            except Exception:
                print("Don't sent eQSL")

        stringToAdiFile = "<BAND:" + str(len(recordObject['BAND'])) + ">" + recordObject['BAND'] + "<CALL:" + str(
            len(recordObject['CALL'])) + ">"

        stringToAdiFile = stringToAdiFile + recordObject['CALL'] + "<FREQ:" + str(len(recordObject['FREQ'])) + ">" + \
                          recordObject['FREQ']
        stringToAdiFile = stringToAdiFile + "<MODE:" + str(len(recordObject['MODE'])) + ">" + recordObject[
            'MODE'] + "<OPERATOR:" + str(len(recordObject['OPERATOR']))
        stringToAdiFile = stringToAdiFile + ">" + recordObject['OPERATOR'] + "<QSO_DATE:" + str(
            len(recordObject['QSO_DATE'])) + ">"
        stringToAdiFile = stringToAdiFile + recordObject['QSO_DATE'] + "<TIME_ON:" + str(
            len(recordObject['TIME_ON'])) + ">"
        stringToAdiFile = stringToAdiFile + recordObject['TIME_ON'] + "<RST_RCVD:" + str(
            len(recordObject['RST_RCVD'])) + ">" + recordObject['RST_RCVD']
        stringToAdiFile = stringToAdiFile + "<RST_SENT:" + str(len(recordObject['RST_SENT'])) + ">" + recordObject[
            'RST_SENT'] + "<NAME:" + str(
            len(recordObject['NAME'])) + ">" + recordObject['NAME'] + "<QTH:" + str(
            len(recordObject['QTH'])) + ">" + recordObject['QTH'] + "<COMMENTS:" + str(
            len(recordObject['COMMENT'])) + ">" + recordObject[
                              'COMMENT'] + "<TIME_OFF:" + str(len(recordObject['TIME_OFF'])) + ">" + recordObject[
                              'TIME_OFF'] + "<EQSL_QSL_SENT:" + str(len(recordObject['EQSL_QSL_SENT'])) + ">" + str(
            recordObject['EQSL_QSL_SENT']) + \
                          "<CLUBLOG_QSO_UPLOAD_STATUS:" + str(
            len(recordObject['CLUBLOG_QSO_UPLOAD_STATUS'])) + ">" + str(
            recordObject['CLUBLOG_QSO_UPLOAD_STATUS'])
        stringToAdiFile = stringToAdiFile + "<STATION_CALLSIGN:" + str(len(recordObject['STATION_CALLSIGN'])) + ">" + str(recordObject['STATION_CALLSIGN']) + " "
        stringToAdiFile = stringToAdiFile + "<EOR>\n"

        # record to table
        allCols = len(self.allCollumn)
        self.tableWidget_qso.insertRow(0)
        last_id = db.record_qso_to_base(recordObject)
        for col in range(allCols):
            header = self.tableWidget_qso.horizontalHeaderItem(col).text()
            if header == 'id':
                self.tableWidget_qso.setItem(
                    0,
                    col,
                    self.protectionItem(str(last_id[0]['LAST_INSERT_ID()']), Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                )
            elif header == 'QSO_DATE':
                date = str(recordObject[self.allCollumn[col]])
                date_formated = date[:4] + "-" + date[4:6] + "-" + date[6:]
                self.tableWidget_qso.setItem(0, col, QTableWidgetItem(date_formated))
            elif header == 'TIME_ON' or header == 'TIME_OFF':
                time = str(recordObject[self.allCollumn[col]])
                time_formated = time[:2] + ":" + time[2:4] + ":" + time[4:]
                self.tableWidget_qso.setItem(0, col, QTableWidgetItem(time_formated))
            elif self.allCollumn[col] == "select":
                self.select_checkbox = QCheckBox()
                self.select_checkbox.setStyleSheet("QCheckBox::indicator"
                                                   "{ border : 1px solid " + settingsDict["color-table"] + "; "
                                                   "width: 10px;"
                                                   "height: 10px;"
                                                   "border-radius: 3px; }"
                                                   "QCheckBox::indicator:checked"
                                                   "{border: 2px solid rgb(255, 90, 90);"
                                                   "width: 10px;"
                                                   "height: 10px;"
                                                   "border-radius: 5px;"
                                                   "background-color:" + settingsDict["color-table"] + ";"
                                                   "}")
                self.select_checkbox.stateChanged.connect(self.multi_select_cheked)
                self.tableWidget_qso.setItem(0, col, QTableWidgetItem(""))
                self.tableWidget_qso.setCellWidget(0, col, self.select_checkbox)
            else:
                self.tableWidget_qso.setItem(0, col, QTableWidgetItem(str(recordObject[self.allCollumn[col]])))
            self.tableWidget_qso.item(0, col).setForeground(QColor(settingsDict['color-table']))
        self.tableWidget_qso.resizeRowsToContents()
        if settingsDict['clublog'] == 'enable':
            self.clublog_thread = QThread()
            self.clublog = internetworker.Clublog(settingsDict, adi_string=stringToAdiFile)
            self.clublog.moveToThread(self.clublog_thread)
            self.clublog.sent_qso_ok.connect(self.clublog_sent_ok)
            self.clublog.sent_qso_no.connect(self.clublog_sent_no)
            self.clublog.sent_qso_error.connect(self.clublog_sent_error)
            self.clublog_thread.started.connect(self.clublog.add_record)
            self.clublog_thread.start()
        if settingsDict['qrz-com-logbook-enable'] == "enable":
            self.qrz_com_logbook.send_qso_to_logbook(stringToAdiFile)

    @QtCore.pyqtSlot(object)
    def clublog_sent_ok(self, response):
        self.tableWidget_qso.setItem(0, 13, QTableWidgetItem('Y'))
        self.store_change_record(row_arg=0)
        self.clublog_thread.exec()
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot(object)
    def clublog_sent_no(self, response):
        std.std.message(self,
                        "Club log: " + response.content.decode(settingsDict['encodeStandart']) + "\n",
                        "ERROR")
        self.tableWidget_qso.setItem(0, 13, QTableWidgetItem('N'))
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)
        self.clublog_thread.exec()

    @QtCore.pyqtSlot()
    def clublog_sent_error(self):
        std.std.message(self,
                        "<strong>Can't send to Club Log</strong><br>Check internet connection<br><br><i><p style='font-size: 12px;'>You can disable auto send to Club log <br> (Settings -> Services -> Auto sent to Club log after QSO )</p></i>",
                        "<p style='color: red'>ERROR Clublog</p>")
        self.tableWidget_qso.setItem(0, 13, QTableWidgetItem('N'))
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)
        self.clublog_thread.exec()

    @QtCore.pyqtSlot(name='eqsl_ok')
    def eqsl_ok(self):
        self.tableWidget_qso.setItem(0, self.collumns_index['EQSL_QSL_SENT'], QTableWidgetItem('Y'))
        allCols = len(self.allCollumn)
        for col in range(allCols):
            self.tableWidget_qso.item(0, col).setBackground(QColor(settingsDict['eqsl-sent-color']))

        self.store_change_record(row_arg=0)
        self.tableWidget_qso.setHorizontalHeaderLabels(self.allCollumn)

    @QtCore.pyqtSlot()
    def eqsl_error(self):
        pass

    def search_in_table(self, call):
        list_dict = []
        if self.tableWidget_qso.rowCount() > 0:
            for rows in range(self.tableWidget_qso.rowCount()):
                try:
                    if self.tableWidget_qso.item(rows, 4).text() == call:
                        row_in_dict = {"No": self.tableWidget_qso.item(rows, 0).text(),
                                       "Date": self.tableWidget_qso.item(rows, 1).text(),
                                       "Time": self.tableWidget_qso.item(rows, 2).text(),
                                       "Band": self.tableWidget_qso.item(rows, 3).text(),
                                       "Call": self.tableWidget_qso.item(rows, 4).text(),
                                       "Mode": self.tableWidget_qso.item(rows, 5).text(),
                                       "Rstr": self.tableWidget_qso.item(rows, 6).text(),
                                       "Rsts": self.tableWidget_qso.item(rows, 7).text(),
                                       "Name": self.tableWidget_qso.item(rows, 8).text(),
                                       "Qth": self.tableWidget_qso.item(rows, 9).text(),
                                       "Comments": self.tableWidget_qso.item(rows, 10).text(),
                                       "Time_off": self.tableWidget_qso.item(rows, 11).text(),
                                       "Eqsl_sent": self.tableWidget_qso.item(rows, 12).text()}
                        list_dict.append(row_in_dict)
                except Exception:
                    print("> Search in table > Don't Load text from table")
            return list_dict


class LogSearch(QWidget):
    def __init__(self):
        super().__init__()
        self.foundList = []
        self.initUI()

    def initUI(self):

        self.setGeometry(int(settingsDict['log-search-window-left']), int(settingsDict['log-search-window-top']),
                         int(settingsDict['log-search-window-width']), int(settingsDict['log-search-window-height']))
        self.setWindowTitle('Repeats')
        self.setWindowIcon(QIcon(f'{Path(__file__).parent}/logo.png'))
        if settingsDict['border_wnd'] == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(float(settingsDict['logSearch-opacity']))
        style = "background-color:" + settingsDict['background-color'] + "; color:" + settingsDict[
            'color'] + "; font: 12px;"
        self.setStyleSheet(style)
        self.tableWidget = QTableWidget()
        style_table = "background-color:" + settingsDict['form-background'] + "; color:" + settingsDict[
            'color-table'] + "; font: 12px;  gridline-color: " + settingsDict['solid-color'] + ";"
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
                settingsDict['log-search-window'] = 'False'
            elif self.isVisible():
                settingsDict['log-search-window'] = 'True'
            QWidget.changeEvent(self, event)

    def overlap_qso_info(self, foundList):
        if foundList:
            allRows = len(foundList)
            self.tableWidget.clearContents()
            self.tableWidget.setRowCount(allRows)
            self.tableWidget.setColumnCount(10)
            self.tableWidget.setHorizontalHeaderLabels(
                ["   Date   ", "Band", "   Freq   ", "Call", "Mode", "RST r",
                 "RST s", " Time ", "      Name      ", "      QTH      "])
            # self.tableWidget.resizeColumnsToContents()
            allCols = self.tableWidget.columnCount()
            for row in range(allRows):
                for col in range(allCols):
                    pole = logWindow.allCollumn[col]
                    self.tableWidget.setItem(row, col, QTableWidgetItem(str(foundList[row][pole])))
                    self.tableWidget.item(row, col).setForeground(QColor(settingsDict["color-table"]))
            self.tableWidget.resizeRowsToContents()
            self.tableWidget.resizeColumnsToContents()
            self.foundList = foundList
        else:
            self.tableWidget.clearContents()
            self.tableWidget.setRowCount(0)

    def refresh_interface(self):

        self.setGeometry(int(settingsDict['log-search-window-left']), int(settingsDict['log-search-window-top']),
                         int(settingsDict['log-search-window-width']), int(settingsDict['log-search-window-height']))

        self.update_color_schemes()

    def update_color_schemes(self):
        style = "background-color:" + settingsDict['background-color'] + "; color:" + \
                settingsDict['color'] + ";"

        style_form = "background-color:" + settingsDict['form-background'] + "; color:" + settingsDict[
            'color-table'] + "; font: 12px"
        self.tableWidget.setStyleSheet(style_form)
        rows = self.tableWidget.rowCount()
        cols = self.tableWidget.columnCount()
        for row in range(rows):
            for col in range(cols):
                self.tableWidget.item(row, col).setForeground(QColor(settingsDict['color-table']))

        self.setStyleSheet(style)


class check_update:

    def __init__(self, APP_VERSION, settingsDict, parrentWindow):
        # super().__init__()
        self.version = APP_VERSION
        self.settingsDict = settingsDict
        self.parrent = parrentWindow
        self.run()

    def run(self):
        server_url_get = self.settingsDict['server-upd']
        uri_for_check_update = "/api/v1/updater/"
        url_action = f"{server_url_get}{uri_for_check_update}{self.version}/{self.settingsDict['my-call']}"
        try:
            response = requests.get(url_action)
            if response.status_code == 200:
                update_obj = json.loads(response.content)
                if update_obj["status"]:
                    self.update_processing(update_obj)
                else:
                    self.no_new_version()
        except BaseException:
            print(f"Don't connected to update server")
            self.no_new_version()

    def update_processing(self, update_obj):
        update_result = QMessageBox.question(self.parrent, "LinuxLog | Updater",
                                             f"Found new version {update_obj['version']} install it?",
                                             buttons=QMessageBox.Yes | QMessageBox.No,
                                             defaultButton=QMessageBox.Yes
                                             )
        if update_result == QMessageBox.Yes:
            print("Start update process")
        if update_result == QMessageBox.No:
            print("Not start update process")
            self.enable_upd_button()
        print(f"Class check_upate.update_processing.\nInput: {update_obj}")

    def no_new_version(self):
        std.std.message(self.parrent, "You have latest version", "UPDATER")
        self.enable_upd_button()

    def enable_upd_button(self):
        self.parrent.check_update.setText("> Check update <")
        self.parrent.check_update.setEnabled(True)

class Check_update_thread(QtCore.QObject):
    update_response = QtCore.pyqtSignal(object)

    def __init__(self, url_query):
        super().__init__()
        self.url_query = url_query

    def run(self):
        # print("Test")
        try:
            self.response_upd_server = requests.get(self.url_query)
            self.update_response.emit(self.response_upd_server)
        except Exception:
            print("Can't check update")


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
        # self.text.setFixedHeight(200)
        self.text.setStyleSheet("font-size: 12px")
        self.about_layer = QVBoxLayout()
        self.image = QPixmap("logo.png")
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
        # self.check.start()


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

        # create button 1
        self.button_1 = QPushButton("1")
        self.button_1.setStyleSheet(self.style)
        self.button_1.setFixedSize(40, 40)
        self.button_1.clicked.connect(self.num_clicked)
        self.button_1.setShortcut('1')
        # create button 2
        self.button_2 = QPushButton("2")
        self.button_2.setStyleSheet(self.style)
        self.button_2.setFixedSize(40, 40)
        self.button_2.clicked.connect(self.num_clicked)
        self.button_2.setShortcut('2')
        # create button 3
        self.button_3 = QPushButton("3")
        self.button_3.setStyleSheet(self.style)
        self.button_3.setFixedSize(40, 40)
        self.button_3.clicked.connect(self.num_clicked)
        self.button_3.setShortcut('3')
        # create button 4
        self.button_4 = QPushButton("4")
        self.button_4.setStyleSheet(self.style)
        self.button_4.setFixedSize(40, 40)
        self.button_4.clicked.connect(self.num_clicked)
        self.button_4.setShortcut('4')
        # create button 5
        self.button_5 = QPushButton("5")
        self.button_5.setStyleSheet(self.style)
        self.button_5.setFixedSize(40, 40)
        self.button_5.clicked.connect(self.num_clicked)
        self.button_5.setShortcut('5')
        # create button 6
        self.button_6 = QPushButton("6")
        self.button_6.setStyleSheet(self.style)
        self.button_6.setFixedSize(40, 40)
        self.button_6.clicked.connect(self.num_clicked)
        self.button_6.setShortcut('6')
        # create button 7
        self.button_7 = QPushButton("7")
        self.button_7.setStyleSheet(self.style)
        self.button_7.setFixedSize(40, 40)
        self.button_7.clicked.connect(self.num_clicked)
        self.button_7.setShortcut('7')
        # create button 8
        self.button_8 = QPushButton("8")
        self.button_8.setStyleSheet(self.style)
        self.button_8.setFixedSize(40, 40)
        self.button_8.clicked.connect(self.num_clicked)
        self.button_8.setShortcut('8')
        # create button 9
        self.button_9 = QPushButton("9")
        self.button_9.setStyleSheet(self.style)
        self.button_9.setFixedSize(40, 40)
        self.button_9.clicked.connect(self.num_clicked)
        self.button_9.setShortcut('9')
        # create button 1
        self.button_0 = QPushButton("0")
        self.button_0.setStyleSheet(self.style)
        self.button_0.setFixedSize(40, 40)
        self.button_0.clicked.connect(self.num_clicked)
        self.button_0.setShortcut('0')
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

    def num_clicked(self):
        button = self.sender()
        freq = self.freq_label.text()
        digit_freq = self.freq_label.text().replace('.', '')
        digit_freq = digit_freq.replace(' Hz', '')
        if self.freq_status == 0:
            digit_freq = ''
            self.freq_status = 1
        future_freq = digit_freq + button.text()
        if int(future_freq) < 146000000:
            freq_string_to_label = self.freq_to_sting(future_freq)
            self.freq_label.setText(freq_string_to_label + " Hz")
        else:
            self.freq_label.setText("146.000.000 Hz")
        # if len(digit_freq) == 0:
        #    digit_freq = '0'

    def freq_to_sting(self, freq):
        len_freq = len(freq)
        if len_freq <= 3:
            freq_to_label = freq
        elif len_freq > 3 and len_freq <= 6:
            freq_to_label = freq[0:len_freq - 3] + '.' + freq[len_freq - 3:]
        elif len_freq > 6 and len_freq <= 8:
            freq_to_label = freq[0:len_freq - 6] + '.' + freq[len_freq - 6:len_freq - 3] + '.' + freq[len_freq - 3:]
        elif len_freq > 8 and len_freq <= 9:
            freq_to_label = freq[0:len_freq - 6] + '.' + freq[len_freq - 6:len_freq - 3] + '.' + freq[len_freq - 3:]
        return freq_to_label

    def enter_freq(self):
        std_value = std.std()
        frequency = self.freq_label.text().replace(" Hz", '')
        frequency = frequency.replace('.', '')
        if len(frequency) > 3 and int(frequency) > 0:
            logForm.set_freq(frequency)
            if self.settings_dict['rigctl-enabled'] == "enable":
                self.parent_window.rigctl_set_freq_to_trx(frequency)
            if self.settings_dict['tci'] == 'enable':
                # if len(frequency) <= 8:
                frequency = frequency.zfill(8)
                band = std_value.get_std_band(frequency)
                mode = std_value.mode_band_plan(band, frequency)
                try:
                    tci_sndr.set_freq(frequency)
                    tci_sndr.set_mode("0", mode)
                except Exception:
                    print("enter_freq:_> Can't setup tci_freq")
            if self.settings_dict['cat'] == 'enable':
                # print("freq in window freq", frequency)
                frequency = frequency.zfill(8)
                self.parent_window.set_freq_for_cat(frequency)
        if self.close_checkbox.isChecked():
            self.close()

    def delete_symbol_freq(self):
        self.freq_status = 1
        freq_str = self.freq_label.text()
        # .replace(".","")
        freq_str = freq_str.replace(" Hz", "")
        freq_str_del = freq_str[:len(freq_str) - 1]
        # freq_str_formated = self.freq_to_sting(freq_str_del)

        self.freq_label.setText(freq_str_del + " Hz")

    def save_freq_to_memory(self):
        self.memory_list.append(self.freq_label.text())
        self.active_memory_element = str(len(self.memory_list))
        self.memory_label.setText(self.active_memory_element)
        self.memory_label_show.setText("Mem: " + self.active_memory_element +
                                       " Frq: " + str(self.memory_list[int(self.active_memory_element) - 1]))

    def set_freq(self, freq):
        freq_formated = self.freq_to_sting(freq)
        self.freq_label.setText(freq_formated + " Hz")

    def change_memory_element(self):
        button = self.sender()
        if button.text() == "▲" and self.memory_label.text() != '':

            if int(self.memory_label.text()) - 1 == 0:
                self.index = len(self.memory_list)
                # index_to_label = 1
                self.memory_label.setText(str(self.index))
            else:
                self.index = int(self.memory_label.text()) - 1
                self.memory_label.setText(str(self.index))

        if button.text() == "▼" and self.memory_label.text() != '':
            if int(self.memory_label.text()) + 1 > len(self.memory_list):
                self.index = 1
                self.memory_label.setText(str(self.index))
            else:
                self.index = int(self.memory_label.text()) + 1
                self.memory_label.setText(str(self.index))
        if self.memory_label.text() != '':
            self.memory_label_show.setText("Mem: " + str(self.index) +
                                           " Frq: " + self.memory_list[self.index - 1])

    def delete_from_memory(self):
        if self.memory_label.text() != '':
            index = int(self.memory_label.text()) - 1
            del self.memory_list[index]
            if len(self.memory_list) == 0:
                self.memory_label.setText('')
                self.memory_label_show.setText('No freq in memory')
            elif index == 0:
                self.memory_label.setText(str(index + 1))
            else:
                self.memory_label.setText(str(index))

    def recal_from_memory(self):
        if self.memory_label.text() != '':
            index = int(self.memory_label.text()) - 1
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
        self.close()


class LogForm(QMainWindow):
    change_mode_signal = QtCore.pyqtSignal(str)

    def __init__(self, settings_dict, log_search):
        super().__init__()
        self.settings_dict = settings_dict
        self.logSearch = log_search
        self._filter = Filter(internetSearch, self.settings_dict)
        self.diploms_init()
        self.spot_index_by_band = {}
        # self.updater = update_after_run(version=APP_VERSION, settings_dict=settingsDict)
        self.country_dict = self.get_country_dict()
        self.mode = settingsDict['mode']
        self.db = db
        self.db.search_in_db_like_signal.connect(self.olerlap_found_qso)
        self.diplomsCheck()
        self.qrz_com_ready = False
        self.rigctl_main_loop = None
        self.sender = None
        self.current_spot = None
        self.prev_spots = None
        self.trx = None

        self.initUI()
        if self.settings_dict["qrz-com-enable"] == "enable" and \
            self.settings_dict["qrz-com-username"] != "" and \
                self.settings_dict["qrz-com-password"] != "":
                self.qrz_com = QrzComApi(self.settings_dict["qrz-com-username"],
                                      self.settings_dict["qrz-com-password"])
                self.qrz_com.data_info.connect(self.fill_form)
                self.qrz_com.qrz_com_connect.connect(self.qrz_com_status)
                self.qrz_com.qrz_com_error.connect(self.qrz_com_error)
                #self.qrz_com_ready = True
        self.rigctl_init_base_data()


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
        print(f"rigctl _start_main_loop")
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
        print(f"stoped: {input_thread.isRunning()}")
        self.trx.socket_shutdown()
        self.rigctl_init_base_data()

    @QtCore.pyqtSlot()
    def rigctl_stat_off(self):
        self.set_rigctl_stat(color="#aaaaaa")
        print(f"Restart main loop: {self.rigctl_main_loop.isRunning()}")

    def rigctl_set_freq_to_trx(self, freq):
        if self.sender is not None:
            band = std.std().get_std_band(freq)
            mode = std.std().mode_band_plan(band, freq)
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
        print(f"vfo_str in logForm: {vfo_str}")

    @QtCore.pyqtSlot(object)
    def rigctl_set_mode(self, mode):
        self.set_mode_rigctl(mode)
        print(f"mode in logForm: {mode}")

    @QtCore.pyqtSlot(object)
    def rigctl_set_ptt(self, ptt):
        print(f"ptt in logForm: {ptt}")

    def get_qrz_com_ready(self):
        return self.qrz_com_ready

    def get_info_from_qrz(self, text_call):
        if self.qrz_com_ready:
            self.qrz_com.get_callsign_info(text_call)

    @PyQt6.QtCore.pyqtSlot(bool)
    def qrz_com_status(self, connect):
        if connect:
            self.set_qrz_com_stat()
            self.qrz_com_ready = True
        else:
            self.set_qrz_com_wrong("qrz.com")

    @PyQt6.QtCore.pyqtSlot(object)
    def qrz_com_error(self, error_message):
        std.std().message(error_message, "QRZ.COM ERROR")

    @PyQt6.QtCore.pyqtSlot(object)
    def fill_form(self, data):
        print(f"fill_form: {data}")
        if data is not None:
            self.set_qrz_com_stat()
            if data["f_name"] is not None:
                self.inputName.setText(data["f_name"])
            elif data["s_name"]:
                self.inputName.setText(data["s_name"])
            else:
                self.inputName.clear()
            if data["qth"] is not None:
                self.inputQth.setText(data["qth"])
            else:
                self.inputQth.clear()
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
        print(internetSearch.isVisible())
        logWindow_geometry = logWindow.geometry()
        logSearch_geometry = logSearch.geometry()
        logForm_geometry = logForm.geometry()
        telnetCluster_geometry = telnetCluster.geometry()
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

                               })
        return self.parameter

    def save_coordinate_to_new_profile(self):

        self.name = std.wnd_what("Save Profile as...")
        self.name.ok.connect(self.save_profile_name)

    def save_coordinate_to_profile(self):
        self.coordinates_w = self.get_coordinate_windows()
        print(self.coordinates_w)
        profile_list = json.loads(settingsDict['coordinate-profile'])

        for elem in profile_list:
            if elem['name'] == settingsDict['active-profile']:
                elem.update(self.coordinates_w)
        json_string = json.dumps(profile_list)
        settingsDict['coordinate-profile'] = json_string
        self.param = {'coordinate-profile': json_string,
                      'active-profile': settingsDict['active-profile']}
        self.remember_in_cfg(self.param)

    @QtCore.pyqtSlot(str)
    def save_profile_name(self, name):
        json_list = json.loads(settingsDict['coordinate-profile'])
        self.coordinates = self.get_coordinate_windows()
        self.coordinates.update({"name": name})
        json_list.append(self.coordinates)
        json_string = json.dumps(json_list)
        # print("json_string:_>", json_string)
        settingsDict['coordinate-profile'] = json_string
        self.param = {'coordinate-profile': json_string,
                      'active-profile': name}
        self.remember_in_cfg(self.param)
        settingsDict['active-profile'] = name
        self.update_cordinates()
        self.profile_name = QAction(name)
        self.profile_name.triggered.connect(partial(self.set_active_profile, settingsDict['active-profile']))
        self.profiles.addAction(self.profile_name)

    def trx_enable(self, parameter):
        if parameter == 'rx':
            try:
                self.cw_machine.reset()

            except BaseException:
                pass
            print("RX")

        if parameter == 'tx':
            try:
                self.cw_machine.set_tx_stat()
            except BaseException:
                pass

            print("TX")

    def update_cordinates(self):
        json_list = json.loads(settingsDict['coordinate-profile'])
        for elem in json_list:
            if elem['name'] == settingsDict['active-profile']:
                for key in elem:
                    if key != "name":
                        settingsDict[key] = elem[key]
        logSearch.refresh_interface()
        logWindow.refresh_interface()
        telnetCluster.refresh_interface()
        internetSearch.refresh_interface()
        logForm.refresh_interface()

    def change_profile(self, text):
        print(text)

    def tx_tci(self, flag):
        print("FLag", flag)
        if flag == "restart":
            print("FLag", flag)
            tci_sndr.update_tx_tci()

    def sendMesageToTCI(self, message):
        ...
        #tci_recv.tci_reciever.tci_send_command("RX_SENSORS_ENABLE:true,500;")
        #tci_sndr.send_command(message)

    def dBm_to_S(self, dBm):
        if float(dBm) <= (-121):
            return "1"
        elif (-121) <= float(dBm) < (-115):
            return "1"
        elif (-115) <= float(dBm) < (-109):
            return "2"
        elif (-109) <= float(dBm) < (-103):
            return "3"
        elif (-103) <= float(dBm) < (-97):
            return "4"
        elif (-97) <= float(dBm) < (-91):
            return "5"
        elif (-91) <= float(dBm) < (-85):
            return "6"
        elif (-85) <= float(dBm) < (-79):
            return "7"
        elif (-79) <= float(dBm) < (-73):
            return "8"
        elif (-73) <= float(dBm) < (-68):
            return "9"
        elif (-68) <= float(dBm) < (-63):
            return "9+5"
        elif (-63) <= float(dBm) < (-58):
            return "9+10"
        elif (-58) <= float(dBm) < (-53):
            return "9+15"
        elif (-53) <= float(dBm) < (-48):
            return "9+20"
        elif (-48) <= float(dBm) < (-43):
            return "9+25"
        elif (-43) <= float(dBm) < (-38):
            return "9+30"
        elif (-38) <= float(dBm) < (-33):
            return "9+35"
        elif (-33) <= float(dBm) < (-28):
            return "9+40"
        elif (-38) <= float(dBm) < (-23):
            return "9+45"
        elif (-23) <= float(dBm) < (-18):
            return "9+50"
        elif (-18) <= float(dBm) < (-13):
            return "9+55"
        elif (-13) <= float(dBm):
            return "9+60"

    def set_rs_s(self, dBm):
        self.inputRstS.setText(f"5{self.dBm_to_S(dBm) if self.comboMode.currentText() != 'DIGI' else dBm}")

    def set_data_qso(self, found_list):
        # print("Found_list:", found_list)
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

        with open(Path(__file__).parent / settingsDict['country-file'], 'r') as f:
            country_json = json.load(f)

        return country_json

    def start_cat(self):
        self.cat_system = cat.Cat_start(settingsDict, self)
        # self.cat_system.start_reciever_cat()

    def stop_cat(self):
        print("stoped CAT")
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
        print("get last general spot")
        all_spots = telnetCluster.get_all_spots()
        #print(all_spots)
        if all_spots and self.current_spot != all_spots[-1]:
            self.prev_spots = self.current_spot
            self.current_spot = all_spots[-1]
            self.fill_qso_form_from_cluster(self.current_spot)
        else:
            print("No spots")

    def get_prev_general_spot(self):
        print("get prev spot")
        if self.prev_spots is not None:
            spot = self.prev_spots
            self.prev_spots = self.current_spot
            self.current_spot = spot
            self.fill_qso_form_from_cluster(self.current_spot)
        else:
            print(f"No prev spots")

    def get_last_spot_on_band(self):
        print("get last spot on band")
        spots_on_band = self.get_spots_for_current_band()
        if spots_on_band:
            self.prev_spots = self.current_spot
            self.current_spot = spots_on_band[-1]
            self.fill_qso_form_from_cluster(self.current_spot)
        else:
            print("No spots")

    def get_next_spot_on_band(self):
        print(f"All spots{telnetCluster.get_all_spots()}")
        spots_on_band = [spot for spot in telnetCluster.get_all_spots() if spot is not None and
                         spot['band'] == self.get_current_band() and
                         db.search_qso_in_base(spot['call']) == ()]
        print(f"Spots on band {spots_on_band}")
        if spots_on_band:
            self.spot_index_by_band[self.get_current_band()] += 1
            if len(spots_on_band) - 1 >= self.spot_index_by_band[self.get_current_band()]:
                print(f"Plus: {self.spot_index_by_band[self.get_current_band()]}")
                self.prev_spots = self.current_spot
                self.current_spot = spots_on_band[self.spot_index_by_band[self.get_current_band()]]
                self.fill_qso_form_from_cluster(self.current_spot)
            else:
                self.spot_index_by_band[self.get_current_band()] -= 1
                print(f"Last spot by next")
            print(f"Select spot: {self.current_spot}")
        else:
            print(f"For this band no spot")

    def get_prev_spot_on_band(self):
        spots_on_band = [spot for spot in telnetCluster.get_all_spots() if
                         spot is not None and spot['band'] == self.get_current_band() and
                         db.search_qso_in_base(spot['call']) == ()]
        print(f"Spots on band {spots_on_band}")
        if spots_on_band:
            if self.spot_index_by_band[self.get_current_band()] > 0:
                self.spot_index_by_band[self.get_current_band()] -= 1
            if self.spot_index_by_band[self.get_current_band()] >= 0 and\
                    len(spots_on_band) - 1 >= self.spot_index_by_band[self.get_current_band()]:

                print(f"Minus: {self.spot_index_by_band[self.get_current_band()]}")
                self.prev_spots = self.current_spot
                self.current_spot = spots_on_band[self.spot_index_by_band[self.get_current_band()]]
                self.fill_qso_form_from_cluster(self.current_spot)
            else:
                self.spot_index_by_band[self.get_current_band()] += 1
                print(f"Last spot by prev")
            print(f"Select spot: {self.current_spot}")
        else:
            print(f"For this band no spot")

    def get_spots_for_current_band(self):
        return [spot for spot in telnetCluster.get_all_spots() if spot is not None and
                         spot['band'] == self.get_current_band() and
                         db.search_qso_in_base(spot['call']) == ()]
    def fill_qso_form_from_cluster(self, qso_data):
        if qso_data is not None:
            self.inputCall.setText(self.current_spot['call'])
            self.set_freq(self.current_spot['freq'])
            self.get_info_from_qrz(self.current_spot['call'])
            if self.settings_dict["rigctl-enabled"] == "enable":
                self.rigctl_set_freq_to_trx(self.current_spot['freq'])
            if settingsDict['tci'] == 'enable':
                try:
                    tci_sndr.set_freq(self.current_spot['freq'])
                    if self.current_spot['mode'] != 'ERROR':
                        tci_sndr.set_mode('0', self.current_spot['mode'])
                        tci_sndr.set_mode('0', self.current_spot['mode'])
                        tci_sndr.set_mode('0', self.current_spot['mode'])
                except BaseException:
                    print("Set_freq_cluster: Can't connection to server:", settingsDict['tci-server'], ":",
                          settingsDict['tci-port'], "freq:_>", self.current_spot['freq'])

            if settingsDict['cat'] == 'enable':
                try:
                    logForm.cat_system.sender_cat(freq=self.current_spot['freq'], mode=self.current_spot['mode'])
                except Exception:
                    print("Can't read/write to CAT port")

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
        self.profiles = QMenu("Profiles")
        self.profiles.setStyleSheet(
            "QWidget{font: 10px; background-color: " + settingsDict['background-color'] + "; color: " + settingsDict[
                'color'] + ";}")

        # self.profiles.addSection()
        self.profiles.addAction(self.profile_name)
        self.profiles.addAction(self.profile_save)
        self.profiles.addSeparator()
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
                print("self.diplomsName:_>", diplom_data)
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
        self.eqsl_inbox_window = eqsl_inbox.EqslWindow(settings_dict=settingsDict, db=db, log_window=logWindow)

    def profile_update_menu(self):
        profiles = json.loads(settingsDict["coordinate-profile"])
        profile_action_list = []
        self.profiles.clear()
        self.profiles.addAction(self.profile_name)
        self.profiles.addAction(self.profile_save)
        self.profiles.addSeparator()
        self.profiles.addSeparator()
        for profile in profiles:
            tmp_profile = QAction(profile['name'], self)
            # tmp_profile.setChecked(True)
            tmp_profile.setCheckable(True)
            if profile['name'] == settingsDict['active-profile']:
                tmp_profile.setChecked(True)
            else:
                tmp_profile.setChecked(False)
            tmp_profile.triggered.connect(partial(self.set_active_profile, profile['name']))
            profile_action_list.append(tmp_profile)
        for profile_action in profile_action_list:
            self.profiles.addAction(profile_action)

    def set_active_profile(self, name):
        # print(name)
        self.settingsDict = settingsDict
        self.settingsDict['active-profile'] = name
        # self.update_settings(self.settingsDict)
        # print("settingsDict['active-profile']: ", settingsDict['active-profile'])
        Settings_file.update_file_to_disk(self)
        self.update_cordinates()

    def menu_add(self, name_menu):
        # diplom
        # self.diplomMenu = self.awardsMenu.addMenu('&Awards')
        print('name_menu', name_menu)
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
        all_data = ext.diplom.get_rules(self=ext.diplom, name=name + ".rules")
        self.edit_window = ext.Diplom_form(settingsDict=settingsDict, log_form=self,
                                           adi_file=Adi_file(APP_VERSION, settingsDict), diplomname=name,
                                           list_data=all_data)
        self.edit_window.show()

        # print("edit_diplom:_>", name, "all_data:", all_data)

    def show_statistic_diplom(self, name):
        self.stat_diplom = ext.static_diplom(diplom_name=name, settingsDict=settingsDict)
        self.stat_diplom.show()
        # print("show_statistic_diplom:_>", name)

    def del_diplom(self, name):
        ext.diplom.del_dilpom(ext.diplom, name, settingsDict, self)
        # print("del_diplom:_>", name)

    def new_diplom(self):
        self.new_diploma = ext.Diplom_form(settingsDict=settingsDict, adi_file=Adi_file(APP_VERSION, settingsDict),
                                           log_form=logForm)

        self.new_diploma.show()

    def about_window(self):
        # print("About_window")
        pass
        about_window.show()

    def searchWindow(self):
        logSearch.hide()

    def cw_machine_gui(self):
        self.cw_machine = CW(parent_window=self, settings_dict=settingsDict)
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
        font = QFont(settingsDict['font-app'], 10, QFont.Weight.Normal)

        QApplication.setFont(font)
        QApplication.setApplicationName('LinuxLog ' + APP_VERSION + ' | ' + settingsDict['my-call'])
        styleform = f"background-color: {settingsDict['form-background']}; color: {settingsDict['color-table']}; padding: 0em;"
        self.setGeometry(int(settingsDict['log-form-window-left']), int(settingsDict['log-form-window-top']),
                         int(settingsDict['log-form-window-width']), int(settingsDict['log-form-window-height']))
        self.setWindowTitle('LinuxLog | Form')
        self.setWindowIcon(QIcon('logo.png'))
        if self.settings_dict['border_wnd'] == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        style = f"background-color:{settingsDict['background-color']}; color: {settingsDict['color']};"
        self.setStyleSheet(style)
        self.menu()

        # self.test()
        self.labelCall = QLabel("Call")
        self.labelCall.setFont(QtGui.QFont(settingsDict['font-app'], 9))

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

        self.labelRstR.setFont(QtGui.QFont(settingsDict['font-app'], 7))

        self.inputRstR = QLineEdit()

        self.inputRstR.setFixedWidth(35)
        self.inputRstR.setFixedHeight(35)
        self.inputRstR.setStyleSheet(styleform)

        if settingsDict['mode-swl'] == 'enable':
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
        self.labelRstS.setFont(QtGui.QFont(settingsDict['font-app'], 7))
        self.inputRstS = QLineEdit("59")
        self.inputRstS.setFixedWidth(35)
        self.inputRstS.setFixedHeight(35)
        self.inputRstS.setStyleSheet(styleform)
        self.inputRstS.returnPressed.connect(self.logFormInput)

        self.labelName = QLabel('Name')
        self.labelName.setFont(QtGui.QFont(settingsDict['font-app'], 9))
        self.inputName = QLineEdit()
        self.inputName.setFixedWidth(137)
        self.inputName.setFixedHeight(30)
        self.inputName.setStyleSheet(styleform)
        self.inputName.returnPressed.connect(self.logFormInput)

        self.labelQth = QLabel("QTH  ")
        self.labelQth.setFixedWidth(36)
        self.labelQth.setFont(QtGui.QFont(settingsDict['font-app'], 9))

        self.inputQth = QLineEdit()
        self.inputQth.setFixedWidth(137)
        self.inputQth.setFixedHeight(30)
        self.inputQth.setStyleSheet(styleform)
        self.inputQth.returnPressed.connect(self.logFormInput)

        self.comboMode = QComboBox()
        self.comboMode.setFixedWidth(80)
        self.comboMode.setFixedHeight(30)
        self.comboMode.addItems(["SSB", "ESSB", "CW", "AM", "FM", "DSB", "DIGI"])
        indexMode = self.comboMode.findText(settingsDict['mode'])
        self.comboMode.setCurrentIndex(indexMode)
        self.comboMode.currentTextChanged.connect(self.changed_mode)
        #self.comboMode.
        #self.comboMode.activated[str].connect(self.rememberMode)

        self.comboBand = QComboBox()
        self.comboBand.setFixedWidth(80)
        self.comboBand.setFixedHeight(30)
        self.comboBand.addItems(["160", "80", "40", "30", "20", "17", "15", "12", "10", "6", "2", "100", "200", "GEN"])
        indexBand = self.comboBand.findText(settingsDict['band'])
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
        self.labelMyCall = QLabel(settingsDict['my-call'])
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

        style = "QTextEdit{background:" + settingsDict['form-background'] + "; border: 1px solid " + settingsDict[
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


        print(event.button())

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
            print(event.pos().y(), x_r, self.resize_wnd.x())
            self.resize(self.x - x_r, self.y - y_r)

    def full_clear_form(self):
        self.inputCall.clear()
        if settingsDict['mode-swl'] == 'enable':
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
        # print("Change_freq_event:_>", freq)

    def freq_window(self):
        # print("Click by freq label")
        self.freq_input_window = FreqWindow(settings_dict=settingsDict, parent_window=self)

    def changed_band(self):
        self.comboBand.clearFocus()
        self.rememberBand(self.comboBand.currentText().strip())
    def rememberBand(self, text):
        with open(Path(__file__).parent/'settings.cfg', 'r') as file:
            # read a list of lines into data
            data = file.readlines()
        for i in range(len(data)):
            string = data[i]
            string = string.strip()
            string = string.replace("\r", "")
            string = string.replace("\n", "")
            string = string.split('=')
            # print(string)
            if data[i][0] != "#":
                if string[0] == 'band':
                    string[1] = self.comboBand.currentText().strip()
                data[i] = string[0] + '=' + string[1] + '\n'
                with open(Path(__file__).parent/'settings.cfg', 'w') as file:
                    file.writelines(data)

    def changed_mode(self):
        self.comboMode.clearFocus()
        self.rememberMode(self.comboMode.currentText())
        self.change_mode_signal.emit(self.comboMode.currentText())
        self.mode = self.comboMode.currentText()
        self.change_mode_signal.emit(self.mode)
        if self.sender is not None:
            self.sender()

    def rememberMode(self, text):
        # print(self.comboMode.currentText())
        with open(Path(__file__).parent/'settings.cfg', 'r') as file:
            # read a list of lines into data
            data = file.readlines()
        for i in range(len(data)):
            string = data[i]
            string = string.strip()
            string = string.replace("\r", "")
            string = string.replace("\n", "")
            string = string.split('=')
            # print(string)
            if data[i][0] != "#" and string[0] == 'mode':
                    string[1] = self.comboMode.currentText().strip()
                    data[i] = string[0] + '=' + string[1] + '\n'
                    with open(Path(__file__).parent/'settings.cfg', 'w') as file:
                        file.writelines(data)

    def key_lay_reverse(self, string: str):
        '''
        This method reciev string on russian and reverse lay
        in equivalent to english keyboard lay. ЙЦУКЕН => QWERTY
        :param string: input original string
        :return:
        '''

        reverse_dict = {"Й": "Q", "Ц": "W", "У": "E", "К": "R", "Е": "T", "Н": "Y", "Г": "U",
                        "Ш": "I", "Щ": "O", "З": "P", "Х": "", "Ъ": "",
                        "Ф": "A", "Ы": "S", "В": "D", "А": "F", "П": "G", "Р": "H", "О": "J",
                        "Л": "K", "Д": "L", "Ж": ":", "Э": "",
                        "Я": "Z", "Ч": "X", "С": "C", "М": "V", "И": "B", "Т": "N", "Ь": "M",
                        "Б": "", "Ю": "", ".": "/"}
        new_string = ""

        for char in string:
            if re.search('[А-Я]', char):
                char_reverse = reverse_dict[char]
            else:
                char_reverse = char
            new_string += char_reverse
        return new_string

    def onChanged(self, text):
        '''метод который отрабатывает как только произошло изменение в поле ввода'''
        if (re.search('[a-zа-я]', text)):
            print("lowwer")
            self.inputCall.setText(text.upper())

        if re.search('[А-Я]', text):
            string_old = self.inputCall.text()
            string_reverse = self.key_lay_reverse(string_old)
            self.inputCall.setText(string_reverse)
        if len(text) > 2:
            print(f"Get country")
            country = self.get_country(text)
            if country != []:
                self.set_country_label(country[0] + ' <h6 style="font-size: 10px;">ITU: ' + str(country[1]) + '</h6>')
            else:
                self.set_country_label('')

        if len(text) < 2:
            self.set_country_label("")
        if len(text) >= 4:
            if (not re.search('[А-Я]', text) and text.isupper() and text.isalnum()):
                print(f"Start Search")
                self.db.search_like_qsos(text)
                self.get_info_from_qrz(text)
        else:
            self.logSearch.clear_table()

        if len(text) == 0:
            print(f"Clear Seach window")
            self.logSearch.clear_table()

    def get_country(self, call_dark):

        call = call_dark.upper()

        country_lists = []
        country_list = []

        for keys in self.country_dict:
            for list_elem in self.country_dict[keys]['prefix']:
                if call.find(list_elem) == 0:
                    country_lists.append(
                        [list_elem, keys, self.country_dict[keys]['itu'], self.country_dict[keys]['cq-zone']])
        count = 0
        for i in range(len(country_lists)):
            lenght_str = len(country_lists[i][0])
            if lenght_str > count:
                count = lenght_str
                country_list = country_lists[i]
                country_list.pop(0)
        return country_list

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

            country_label = self.country_label.text().strip()
            data_country = country_label.split("|")
            country = data_country[0]
            self.EQSL_QSL_SENT = 'N'
            self.CLUBLOG_QSO_UPLOAD_STATUS = "N"

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
                'STATION_CALLSIGN': call}

            logWindow.addRecord(self.recordObject)
            # Check current spot
            if self.current_spot is not None and call == self.current_spot['call']:
                self.current_spot['complete'] = 1
                self.spot_index_by_band[self.get_current_band()] -= 1

            call_dict = {'call': call, 'mode': mode, 'band': band}
            if settingsDict['diplom'] == 'enable':
                for diploms in self.diploms:
                    if diploms.filter(call_dict):
                        diploms.add_qso(self.recordObject)

            try:
                if settingsDict['tci'] == "enable":
                    tci_sndr.change_color_spot(call, freq)
            except BaseException:
                print("LogFormInput:_> Can't connect to TCI server (set spot)")

            logForm.inputCall.setFocus()

            if settingsDict['mode-swl'] == 'enable':
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
                print("Minimized")
                if settingsDict['search-internet-window'] == 'True':
                    internetSearch.showMinimized()
                if settingsDict['log-search-window'] == 'True':
                    logSearch.showMinimized()
                    settingsDict['log-search-window'] = 'True'
                if settingsDict['log-window'] == 'True':
                    logWindow.showMinimized()
                    settingsDict['log-window'] = 'True'
                if settingsDict['telnet-cluster-window'] == 'True':
                    telnetCluster.showMinimized()
                    settingsDict['telnet-cluster-window'] = 'True'
            else:

                if settingsDict['search-internet-window'] == 'True':
                    internetSearch.showNormal()
                    settingsDict['search-internet-window'] = 'True'
                if settingsDict['log-search-window'] == 'True':
                    logSearch.showNormal()
                    settingsDict['log-search-window'] = 'True'
                if settingsDict['log-window'] == 'True':
                    logWindow.showNormal()
                    settingsDict['log-window'] = 'True'
                if settingsDict['telnet-cluster-window'] == 'True':
                    telnetCluster.showNormal()
                    settingsDict['telnet-cluster-window'] = 'True'

            QWidget.changeEvent(self, event)

    def showEvent(self, event):
        if settingsDict['log-window'] == 'True':
            logWindow.showNormal()

        if settingsDict['log-search-window'] == 'True':
            logSearch.showNormal()
        if settingsDict['telnet-cluster-window'] == 'True':
            telnetCluster.showNormal()
        if settingsDict['search-internet-window'] == 'True':
            internetSearch.showNormal()

    def closeEvent(self, event):
        '''
        This function recieve signal close() from logForm window
        Save coordinate and size all windows
        Stop real-time thread
        Close app
        '''
        self.run_time.stop_()
        self.run_time.wait()
        self.parameter = self.get_coordinate_windows()
        logWindow.close()
        internetSearch.close()
        logSearch.close()

        logForm.close()
        telnetCluster.close()
        try:
            if self.cw_machine.isVisible():
                self.settings_dict["cw"] = "True"
                self.cw_machine.close()
            else:
                print("closed CW machine")
                self.settings_dict["cw"] = "False"
                settings_file.save_all_settings(self, self.settings_dict)
        except BaseException:
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
        except BaseException:
            pass
        try:
            if self.eqsl_inbox_window.isEnabled():
                self.eqsl_inbox_window.close()

        except BaseException:
            pass

        if about_window.isEnabled():
            about_window.close()
        self.remember_in_cfg(self.parameter)
        settingsDict['app'].exit(0)

    def remember_in_cfg(self, parameter):
        '''
        This function recieve Dictionary parametr with key:value
        record key=value into config.cfg

        :param parameter:
        :return:
        '''
        filename = 'settings.cfg'
        with open(Path(__file__).parent/filename, 'r') as f:
            old_data = f.readlines()
        for line, string in enumerate(old_data):
            key_in_file = string.split('=')
            for key in parameter:
                # print (string)
                if key == key_in_file[0]:
                    # print(key, string)
                    string = key + "=" + parameter[key] + "\n"
                    old_data[line] = string
        with open(Path(__file__).parent/filename, 'w') as f:
            f.writelines(old_data)

    def logSettings(self):
        # menu_window.show()
        self.menu = settings.Menu(
            db,
            app_env,
            settingsDict,
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
            # print('statTelnet')
            telnetCluster.show()
        elif telnetCluster.isEnabled():
            telnetCluster.hide()

    def stat_internet_search(self):
        if internetSearch.isHidden():
            # print('internet_search')
            internetSearch.show()
        elif internetSearch.isEnabled():
            internetSearch.hide()

    def stat_repeat_qso(self):
        if logSearch.isHidden():
            # print('internet_search')
            logSearch.show()
        elif logSearch.isEnabled():
            logSearch.hide()

    def set_band(self, band):
        # print("LogForm.set_band. input band:", band)
        indexMode = self.comboBand.findText(band)
        self.comboBand.setCurrentIndex(indexMode)

    def set_freq(self, freq):
        freq_string = str(freq)
        freq_string = freq_string.replace('.', '')
        len_freq = len(freq)

        freq_to_label = freq[0:len_freq - 6] + "." + freq[len_freq - 6:len_freq - 3] + "." + freq[len_freq - 3:]
        self.labelFreq.setText("Freq: " + str(freq_to_label))
        band = std.std().get_std_band(freq)

        index_band = self.comboBand.findText(band)
        self.comboBand.setCurrentIndex(index_band)
        try:
            if self.freq_input_window.isEnabled():
                if settingsDict['cat'] != "enable":
                    self.freq_input_window.set_freq(freq)
                else:
                    pass
        except Exception:
            pass

    def set_vfo(self, vfo_str):
        self.labelVfo.setText(str(vfo_str).upper())
    def set_freq_for_cat(self, freq):

        try:
            self.cat_system.sender_cat(freq=freq)
        except Exception:
            print("Can't set frequency by CAT")

    def set_call(self, call):
        self.inputCall.setText(str(call))

    def set_mode_rigctl(self, mode_input):
        mode = str(mode_input).lower()
        print("mode:", mode)
        if mode in ("lsb", "usb"):
            mode_string = 'SSB'
        if mode in ("am", "sam"):
            mode_string = 'AM'
        if mode == "dsb":
            mode_string = 'DSB'
        if mode in ("cw", "cwr"):
            mode_string = 'CW'
        if mode in ("nfm", "wfm", "fm"):
            mode_string = 'FM'
        if mode in ("digl", "digu", "drm", "wspr", "ft8", "ft4", "jt65", "jt9", "rtty", "bpsk", "pktusb", "pktlsb"):
            mode_string = 'DIGI'

        indexMode = self.comboMode.findText(mode_string)
        self.comboMode.setCurrentIndex(indexMode)
        self.mode = mode
        try:
            self.cw_machine.set_mode()
        except Exception:
            pass

    def set_mode_tci(self, mode_input):
        mode = str(mode_input).lower()
        # print("mode:", mode)
        if mode == "lsb" or mode == "usb":
            mode_string = 'SSB'
        if mode == "am" or mode == "sam":
            mode_string = 'AM'
        if mode == "dsb":
            mode_string = 'DSB'
        if mode == "cw":
            mode_string = 'CW'
        if mode == "nfm" or mode == "wfm":
            mode_string = 'FM'
        if mode == "digl" or mode == "digu" or mode == "drm" or mode == "wspr" or mode == "ft8" or mode == "ft4" or \
                mode == "jt65" or mode == "jt9" or mode == "rtty" or mode == "bpsk":
            mode_string = 'DIGI'

        indexMode = self.comboMode.findText(mode_string)
        self.comboMode.setCurrentIndex(indexMode)
        self.mode = mode
        try:
            self.cw_machine.set_mode()
        except Exception:
            pass

    def set_tci_stat(self, values, color="#57BD79"):
        self.labelStatusCat.setStyleSheet("color: " + color + "; font-weight: bold;")
        self.labelStatusCat.setText(values)


    def set_tci_label_found(self, values=''):
        self.labelStatusCat.setStyleSheet("color: #FF6C49; font-weight: bold;")
        self.labelStatusCat.setText("TCI Found " + values)
        sleep(0.55)
        self.labelStatusCat.setText("")

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
        # print("label_status_change")
        sleep(0.15)
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
        freq_string = self.labelFreq.text()
        freq_string = freq_string.replace('Freq: ', '')
        freq_string = freq_string.replace('.', '')

        if freq_string == '' or not freq_string.isdigit():
            band = self.get_band()
            if band == "160":
                freq_string = '1800000'
            elif band == "80":
                freq_string = '3500000'
            elif band == "40":
                freq_string = '7000000'
            elif band == "30":
                freq_string = '10000000'
            elif band == "20":
                freq_string = '14000000'
            elif band == "17":
                freq_string = '18000000'
            elif band == "15":
                freq_string = '21000000'
            elif band == "12":
                freq_string = '24000000'
            elif band == "10":
                freq_string = '28000000'
            elif band == "6":
                freq_string = '54000000'
            elif band == "144":
                freq_string = '144500000'
            else:
                freq_string = 'non'

        return freq_string

    def refresh_interface(self):
        self.setGeometry(int(settingsDict['log-form-window-left']), int(settingsDict['log-form-window-top']),
                         int(settingsDict['log-form-window-width']), int(settingsDict['log-form-window-height']))
        self.labelMyCall.setText(settingsDict['my-call'])
        self.country_dict = self.get_country_dict()
        self.profile_update_menu()
        # Connecting to qrz.com
        if self.settings_dict["qrz-com-enable"] == "enable" and \
                self.settings_dict["qrz-com-username"] != "" and \
                self.settings_dict["qrz-com-password"] != "":
            self.qrz_com = QrzComApi(self.settings_dict["qrz-com-username"],
                                  self.settings_dict["qrz-com-password"])
            self.qrz_com.data_info.connect(self.fill_form)
            self.qrz_com.qrz_com_connect.connect(self.qrz_com_status)
            #self.qrz_com_ready = True

        # SWL mode
        if settingsDict['mode-swl'] == 'enable':
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
        # print("setingsDict['cat']:_>", settingsDict['cat'])
        if settingsDict['cat'] == "enable":
            try:
                self.start_cat()
            except Exception:
                print("Can't start CAT interface (maybe incorrect port)")
        else:
            try:
                self.stop_cat()
            except Exception:
                print("Can't stop CAT interface (maybe it not start)")

    def update_color_schemes(self):
        style = "background-color:" + settingsDict['background-color'] + "; color:" + \
                settingsDict['color'] + ";"
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
        style_form = "background-color:" + settingsDict['form-background'] + "; color:" + settingsDict[
            'color-table'] + "; font: 12px"
        self.inputCall.setStyleSheet(style_form)
        self.inputRstR.setStyleSheet(style_form)
        self.inputRstS.setStyleSheet(style_form)
        self.inputName.setStyleSheet(style_form)
        self.inputQth.setStyleSheet(style_form)
        self.comments.setStyleSheet(style_form)

        self.setStyleSheet(style)

    def update_settings(self, new_settingsDict):
        settingsDict.update(new_settingsDict)

    def diploms_init(self):
        self.diplomsList = []
        self.diploms = self.get_diploms()
        for diplom in self.diploms:
            print("Diplom_", diplom.get_data())
            if diplom.get_data() != []:
                self.diplomsList.append(ext.Diplom(diplom.get_data()[0]['name'], settingsDict))
            else:
                pass

    def diplomsCheck(self):
        for i, diplom in enumerate(self.diplomsList):
            if diplom.complete():
                std.std.message(self, diplom.name+" is completed", "Good")
            # print ("diplom.get_data()['call']", diplom.get_data()[0]['call'])
            # qsoByPatern = Db(settingsDict).getQsoByCallPattern(diplom.get_data()[i]['call'])
            # print("qso by patern:",qsoByPatern )
            # diplom.filter({'call'})
        # print("*" * 10)
        # temp = self.diplomsName[0]
        # print(temp.get_rules(temp.))
        # print("*" * 10)

    def get_diploms(self):
        diploms = []
        if settingsDict['diploms-json'] != '':
            rulesObject = json.loads(settingsDict['diploms-json'])
            for i in range(len(rulesObject)):
                rulesObject[i]['name_programm'] = ext.diplom(rulesObject[i]['name_programm'] + ".adi",
                                                             rulesObject[i]['name_programm'] + ".rules",
                                                             settingsDict)
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
        print("update mod")
        self.set_mode()

    def set_mode(self):
        self.mode = self.parent_window.get_mode()
        print(self.mode)
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
                # print("send_CQ_cw")
                string = self.cq_line_edit_1.text()
                string_tci = self.get_cw_macros_string(string)
                # print(string_tci)
                tci_sndr.send_command("cw_macros:0," + string_tci + ";")

            if button.text() == "1":
                button.setStyleSheet(
                    self.style + " font-size: 12px; background: #337733; color: #ffffff; font-color: bold;")
                # print("send_1_cw")
                string = self.answer_line_edit_1.text()
                string_tci = self.get_cw_macros_string(string)
                print(string_tci)
                tci_sndr.send_command("cw_macros:0," + string_tci + ";")
            if button.text() == "2":
                button.setStyleSheet(
                    self.style + " font-size: 12px; background: #337733; color: #ffffff; font-color: bold;")
                # print("send_2_cw")
                string = self.final_line_edit_1.text()
                string_tci = self.get_cw_macros_string(string)
                print(string_tci)
                tci_sndr.send_command("cw_macros:0," + string_tci + ";")
            if button.text() == "3":
                button.setStyleSheet(
                    self.style + " font-size: 12px; background: #337733; color: #ffffff; font-color: bold;")
                print("send_3_cw")
                string = self.user_line_edit_1.text()
                string_tci = self.get_cw_macros_string(string)
                print(string_tci)
                tci_sndr.send_command("cw_macros:0," + string_tci + ";")
            if button.text() == "4":
                button.setStyleSheet(
                    self.style + " font-size: 12px; background: #337733; color: #ffffff; font-color: bold;")
                print("send_4_cw")
                string = self.user_line_edit_2.text()
                string_tci = self.get_cw_macros_string(string)
                print(string_tci)
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
        self.close()

    def change_status(self):
        self.settings_dict['wpm'] = self.wpm_linedit.text().strip()
        tci_sndr.send_command("CW_MACROS_SPEED:" + self.settings_dict['wpm'] + ";")
        self.set_status(self.wpm_linedit.text().strip())
        settings_file.save_all_settings(self, self.settings_dict)

    def set_status(self, text):
        self.status_label.setText("WPM set: " + text)
        self.wpm_speed = text


class TelnetCluster(QWidget):

    def __init__(self):
        super().__init__()
        # self.mainwindow = mainwindow
        # self.log_form = log_form
        self.host = settingsDict['telnet-host']
        self.port = settingsDict['telnet-port']
        self.call = settingsDict['my-call']
        self.tableWidget = QTableWidget()
        self.allRows = 0
        self.settings_dict = settingsDict
        self.all_spots = []
        self.run_cluster = ClusterThread(settings_dict=settingsDict, parent=self)
        self.initUI()

    def initUI(self):
        """
        Design of cluster window
        """

        self.setGeometry(int(settingsDict['telnet-cluster-window-left']),
                         int(settingsDict['telnet-cluster-window-top']),
                         int(settingsDict['telnet-cluster-window-width']),
                         int(settingsDict['telnet-cluster-window-height']))
        self.setWindowTitle('Telnet cluster')
        self.setWindowIcon(QIcon('logo.png'))
        if self.settings_dict['border_wnd'] == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(float(settingsDict['clusterWindow-opacity']))
        style = "background-color:" + settingsDict['background-color'] + "; color:" + settingsDict[
            'color'] + ";"
        self.setStyleSheet(style)
        self.labelIonosphereStat = QLabel()
        self.labelIonosphereStat.setFixedWidth(250)
        self.labelIonosphereStat.setFixedHeight(10)
        self.labelIonosphereStat.setStyleSheet("font: 8px;")
        # self.labelIonosphereStat.setText("A=12, K=23, F=21, No storm, no storm")
        style_table = "background-color:" + settingsDict['form-background'] + "; color:" + settingsDict[
            'color-table'] + "; font: 12px;  gridline-color: " + settingsDict['solid-color'] + ";"
        self.tableWidget.setStyleSheet("QWidget {" + style_table + "}")
        fnt = self.tableWidget.font()
        fnt.setPointSize(9)
        self.tableWidget.setFont(fnt)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(["Time Loc", "Time GMT", "Call", "Freq", " Spot"])
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.cellClicked.connect(self.click_to_spot)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(3)
        self.layout.addWidget(self.labelIonosphereStat)
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
        self.start_cluster()

    def set_telnet_wrong(self, text):
        logForm.set_telnet_wrong(text)

    def set_telnet_stat(self):
        logForm.set_telnet_stat()

    def send_to_telnet_cluster(self):
        if self.command_input.text() in ("", " "):
            return None
        self.run_cluster.send_to_telnet(self.command_input.text().strip())
        self.textarea.appendPlainText(self.command_input.text().strip())
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


        print(event.button())

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
            print(event.globalPosition().y(), x_r, self.resize_wnd.x())
            self.resize(self.x - x_r, self.y - y_r)

    def parsing_telnet_string(self, telnet_string):
        spot_data_dict = {}
        if telnet_string[:2] == "DX":
            elem_string_list = [elem for elem in telnet_string.split(' ') if elem not in ("", " ")]
            standart_lib = std.std()
            call = elem_string_list[int(self.settings_dict['telnet-call-position'])]
            freq = standart_lib.std_freq(elem_string_list[int(self.settings_dict['telnet-freq-position'])])
            band = standart_lib.get_std_band(str(freq).replace(".",""))
            mode  = standart_lib.mode_band_plan(band, freq)
            complete = 0 if db.search_qso_in_base(elem_string_list[int(self.settings_dict['telnet-call-position'])]) == () else 1  # todo Create method search qso in current contest. In present method searching qso in general database (all qso at all time)
            comment = " ".join(elem_string_list[int(self.settings_dict['telnet-call-position']) + 1:])
            de = elem_string_list[2]
            spot_data_dict.update({
                "call": call,
                "freq": freq,
                "band": band,
                "mode": mode,
                "complete": complete,
                "comment": comment,
                "de": de,
                "timestamp": datetime.datetime.now(datetime.timezone.utc)
            })
            return spot_data_dict

    def add_row_to_cluster(self, string_from_telnet):
        clean_list = []
        last_row = self.tableWidget.rowCount()
        try:
            #print(f"Reciever string: {string_from_telnet.decode(self.settings_dict['encodeStandart'], errors='ignore')[:2]}")
            if string_from_telnet[:2] == "DX":
                split_telnet_string = string_from_telnet.split(' ')
                # get clean list with data from string of telnet
                for item_from_string in split_telnet_string:
                    if item_from_string != '':
                        clean_list.append(item_from_string)
                search_in_diplom_rules_flag = 0
                call_dict = {'call': clean_list[int(self.settings_dict['telnet-call-position'])].strip(),
                             'mode': 'cluster',
                             'band': 'cluster'}
                diplom_list = logForm.get_diploms()
                for diplom in diplom_list:
                    if diplom.filter(call_dict):
                        color = diplom.get_color_bg()
                        search_in_diplom_rules_flag = 1
                if self.cluster_filter(cleanList=clean_list):
                    self.tableWidget.insertRow(last_row)
                    self.tableWidget.setItem(last_row, 0, QTableWidgetItem(strftime("%H:%M:%S", localtime())))
                    self.tableWidget.setItem(last_row, 1, QTableWidgetItem(strftime("%H:%M:%S", gmtime())))
                    if len(clean_list) > 4:
                        self.tableWidget.setItem(last_row, 2, QTableWidgetItem(clean_list[int(self.settings_dict['telnet-call-position'])]))

                        self.tableWidget.setItem(last_row, 3, QTableWidgetItem(clean_list[int(self.settings_dict['telnet-freq-position'])]))
                    self.tableWidget.setItem(last_row, 4, QTableWidgetItem(string_from_telnet.replace('\x07\x07\r\n', '')))
                    self.tableWidget.scrollToBottom()
                    for col in range(self.tableWidget.columnCount()):
                        if search_in_diplom_rules_flag == 1:
                            self.tableWidget.item(last_row, col).setBackground(color)
                        else:
                            self.tableWidget.item(last_row, col).setForeground(QColor(self.settings_dict["color-table"]))

                    self.tableWidget.resizeColumnsToContents()
                    self.tableWidget.resizeRowsToContents()

                    if settingsDict['spot-to-pan'] == 'enable':
                        freq = std.std().std_freq(freq=clean_list[3])
                        try:
                            if settingsDict['tci'] == 'enable':
                                tci_sndr.set_spot(clean_list[4], freq, color="19711680")
                        except BaseException:
                            print("clusterThread: Except in Tci_sender.set_spot", traceback.format_exc())
            elif string_from_telnet[0:3] == "WWV":
                self.labelIonosphereStat.setText("Propagination info: " + string_from_telnet.replace('\x07\x07\r\n', ''))
        except BaseException:
            print("Bad string from cluster (incorrect encoding)")

    @QtCore.pyqtSlot(object)
    def add_spot_to_table(self, string_from_telnet: object):
        # print(f"Emit add_spot_to_table {string_from_telnet}")
        self.add_new_spot(string_from_telnet)
        self.add_row_to_cluster(string_from_telnet)

    @QtCore.pyqtSlot(object)
    def communicate_out(self, telnet_string):
        if telnet_string != "DX":
            self.textarea.appendPlainText(str(telnet_string, settingsDict["encodeStandart"], errors="ignore"))

    def add_new_spot(self, string_from_telnet):
        spot_dict = self.parsing_telnet_string(string_from_telnet)
        if spot_dict is not None:
            self.all_spots.append(spot_dict)

    def get_all_spots(self):
        return self.all_spots

    def stop_cluster(self):
        print("stop_cluster:", self.run_cluster.quit())

    def start_cluster(self):
        self.run_cluster.reciev_spot_signal.connect(self.add_spot_to_table)
        self.run_cluster.reciev_string_signal.connect(self.communicate_out)

    def click_to_spot(self):
        row = self.tableWidget.currentItem().row()
        freq = self.tableWidget.item(row, 3).text()
        call = self.tableWidget.item(row, 2).text()
        self.img_search = internetworker.internetWorker(window=internetSearch, settings=settingsDict)
        self.img_search.set_callsign_for_search(callsign=call)
        self.img_search.start()
        freq = std.std().std_freq(freq)
        band = std.std().get_std_band(freq)
        mode = std.std().mode_band_plan(band, freq)
        complete = complete = 0 if db.search_qso_in_base(call) == () else 1
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

        if settingsDict['tci'] == 'enable':
            try:
                tci_sndr.set_freq(freq)
                if mode != 'ERROR':
                    tci_sndr.set_mode('0', mode[0])

            except BaseException:
                print("Set_freq_cluster: Can't connection to server:", settingsDict['tci-server'], ":",
                      settingsDict['tci-port'], "freq:_>", freq)

        if settingsDict['cat'] == 'enable':
            # print(freq)
            try:
                logForm.cat_system.sender_cat(freq=freq, mode=freq)
            except Exception:
                print("Can't read/write to CAT port")

        if self.settings_dict["rigctl-enabled"] == "enable":
            print(f"Rigctl mode from cluster: {mode}")
            logForm.rigctl_set_freq_to_trx(freq)



    def cluster_filter(self, cleanList):
        flag = False
        if len(cleanList) >= 4:

            if settingsDict['cluster-filter'] == 'enable':
                # filtering by spot prefix
                filter_by_band = False
                filter_by_spotter_flag = False
                filter_by_prefix_flag = False

                if settingsDict['filter-by-prefix'] == 'enable':
                    list_prefix_spot = settingsDict['filter-prefix'].split(',')
                    if cleanList[4][0:2] in list_prefix_spot:
                        filter_by_prefix_flag = True
                else:
                    filter_by_prefix_flag = True
                # filtering by prefix spotter
                if settingsDict['filter-by-prefix-spotter'] == "enable":
                    list_prefix_spotter = settingsDict['filter-prefix-spotter'].split(',')
                    if cleanList[2][0:2] in list_prefix_spotter:
                        filter_by_spotter_flag = True
                else:
                    filter_by_spotter_flag = True
                # filtering by band
                if settingsDict['filter_by_band'] == "enable":
                    list_prefix_spotter = settingsDict['list-by-band'].split(',')
                    freq = std.std().std_freq(cleanList[3])
                    band = std.std().get_std_band(freq)
                    if band in list_prefix_spotter:
                        filter_by_band = True
                else:
                    filter_by_band = True
                # print("cluster_filter: filter_by_prefix_flag:",filter_by_prefix_flag,
                # "\nfilter_by_spotter_flag:",filter_by_spotter_flag,"\nfilter_by_band", filter_by_band)
                if filter_by_prefix_flag and filter_by_spotter_flag and filter_by_band:
                    flag = True
                else:
                    flag = False
            else:
                flag = True
        return flag

    def changeEvent(self, event):

        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            if self.isMinimized():
                settingsDict['telnet-cluster-window'] = 'False'
                print("telnet-cluster-window: changeEvent:_>", settingsDict['telnet-cluster-window'])
                # telnetCluster.showMinimized()
            elif self.isVisible():
                settingsDict['telnet-cluster-window'] = 'True'
                print("telnet-cluster-window: changeEvent:_>", settingsDict['telnet-cluster-window'])

            QWidget.changeEvent(self, event)

    def refresh_interface(self):
        self.setGeometry(int(settingsDict['telnet-cluster-window-left']),
                         int(settingsDict['telnet-cluster-window-top']),
                         int(settingsDict['telnet-cluster-window-width']),
                         int(settingsDict['telnet-cluster-window-height']))

        self.update_color_schemes()

    def update_color_schemes(self):
        style = "background-color:" + settingsDict['background-color'] + "; color:" + \
                settingsDict['color'] + ";"
        self.labelIonosphereStat.setStyleSheet(style)
        style_form = "background-color:" + settingsDict['form-background'] + "; color:" + settingsDict[
            'color-table'] + "; font: 12px;  gridline-color: " + settingsDict['solid-color'] + ";"
        self.tableWidget.setStyleSheet(style_form)
        rows = self.tableWidget.rowCount()
        cols = self.tableWidget.columnCount()
        for row in range(rows):
            for col in range(cols):
                self.tableWidget.item(row, col).setForeground(QColor(settingsDict['color-table']))

        self.setStyleSheet(style)


class InternetSearch(QWidget):

    def __init__(self):
        super().__init__()
        self.labelImage = QLabel(self)
        # self.pixmap=""
        self.initUI()

    def initUI(self):
        self.hbox = QHBoxLayout(self)
        self.pixmap = QPixmap(f"{Path(__file__).parent}/logo.png")
        self.labelImage = QLabel(self)
        self.labelImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.labelImage.setPixmap(self.pixmap)
        self.hbox.addWidget(self.labelImage)
        self.setLayout(self.hbox)

        # self.move(100, 200)
        self.setGeometry(int(settingsDict['search-internet-left']),
                         int(settingsDict['search-internet-top']),
                         int(settingsDict['search-internet-width']),
                         int(settingsDict['search-internet-height']))
        self.setWindowIcon(QIcon(f"{Path(__file__).parent}/logo.png"))
        self.setWindowTitle('Image from internet')
        if settingsDict['border_wnd'] == "disable":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(float(settingsDict['searchInetWindow-opacity']))
        style = "QWidget{background-color:" + settingsDict['background-color'] + "; color:" + settingsDict[
            'color'] + ";}"
        self.setStyleSheet(style)
        # self.show()

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.RightButton:
            self.resize_wnd = event.pos()
            self.x = self.width()
            self.y = self.height()
            self.flag_button = "right"
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()
            self.flag_button = "left"


        print(event.button())

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
            print(event.globalPosition().y(), x_r, self.resize_wnd.x())
            self.resize(self.x - x_r, self.y - y_r)

    def changeEvent(self, event):

        # if event.type() == QtCore.QEvent.WindowStateChange:
        #   if self.isMinimized():
        # settingsDict['search-internet-window'] = 'False'
        #       print("search-internet-window: changeEvent:_>", settingsDict['search-internet-window'])
        # telnetCluster.showMinimized()
        #   elif self.isVisible():
        # settingsDict['search-internet-window'] = 'True'
        #       print("search-internet-window: changeEvent:_>", settingsDict['search-internet-window'])

        QWidget.changeEvent(self, event)

    def update_photo(self):
        pixmap = QPixmap(Path(__file__).parent/"logo.png")

        # self.labelImage.setFixedWidth(self.settings['image-width'])
        self.labelImage.setPixmap(pixmap)

    def refresh_interface(self):
        self.setGeometry(int(settingsDict['search-internet-left']),
                         int(settingsDict['search-internet-top']),
                         int(settingsDict['search-internet-width']),
                         int(settingsDict['search-internet-height']))

        self.update_color_schemes()

    def update_color_schemes(self):
        style = "background-color:" + settingsDict['background-color'] + "; color:" + \
                settingsDict['color'] + ";"
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
        # print("hello_window: ", desktop.width(), width_coordinate)

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
        if self.call_input.text().strip() != "" and len(self.call_input.text().strip()) >= 3:
            db_name = settingsDict['db-name']
            db = Db(settingsDict, first_run=True)
            answer = db.check_database(db_name)
            if answer == ():
                db.create_database()
                settingsDict['db-name'] = db_name
                table = db.create_table(
                    self.call_input.text().strip().upper(),
                    self.table_columns
                )
            else:
                if settingsDict['db-name'] == '':
                    settingsDict['db-name'] = db_name
                    settingsDict['my-call'] = self.call_input.text().strip().upper()
                    connect = db.get_all_records(1)
                    print("Connect:", connect)
                table = db.create_table(
                    self.call_input.text().strip().upper(),
                    self.table_columns
                )
            print("Table:", table)
            # table=1
            if table != 0:
                settingsDict['my-call'] = self.call_input.text().strip().upper()
                try:
                    connect = Db(settingsDict).get_all_records(2)
                    print("Connect:", connect)
                    settings_file.save_all_settings(self, settingsDict)
                    hello_window.close()
                    subprocess.call(["python3", "main.py"])
                    exit(0)
                except BaseException:
                    try:
                        table = Db(settingsDict).create_table(
                            self.call_input.text().strip().upper(),
                            self.table_columns
                        )
                    except Exception:
                        Messages("DB ERROR",
                                 "Can't create table for " + str(self.call_input.text().strip().upper()) + "\n" + str(
                                     table))
                # print ("Error create table")
            else:
                settingsDict['my-call'] = self.call_input.text().strip().upper()
                settings_file.save_all_settings(self, settingsDict)
                hello_window.close()
                subprocess.call(["python3", "main.py"])
                exit(0)
        else:
            self.call_input.setStyleSheet(self.style_form)
            Messages("Oops!", "Please enter correct HAM callsign")
            self.welcome_text_label.setText("Please enter you callsign")
        # print("Ok_button")


class settings_file:

    def save_all_settings(self, settingsDict):
        # print("save_all_settings", settingsDict)
        filename = 'settings.cfg'
        with open(Path(__file__).parent/filename, 'r') as f:
            old_data = f.readlines()
        for index, line in enumerate(old_data):
            key_from_line = line.split('=')[0]
            # print ("key_from_line:",key_from_line)
            for key in settingsDict:

                if key_from_line == key:
                    # print("key",key , "line", line)
                    old_data[index] = key + "=" + settingsDict[key] + "\n"

        with open(Path(__file__).parent/filename, 'w') as f:
            f.writelines(old_data)
        # print("Save_and_Exit_button: ", old_data)


class ReadStringDb(QThread):
    dict_from_base = pyqtSignal(object)
    fill_complite = pyqtSignal()

    def __init__(self, db, parent):
        super().__init__(parent)
        self.parent = parent
        self.db = db

    def run(self):
        records_dict = db.get_all_records(0)
        self.parent.allRows = records_dict
        for qso in records_dict:
            self.dict_from_base.emit(qso)
        self.fill_complite.emit()


class FoundThread(QThread):

    result = QtCore.pyqtSignal(object)

    def __init__(self, connection, query):
        super().__init__()
        self.sql_query_list = []
        self.connection = connection
        self.query = query

    def add_to_stack(self, sql_query):
        self.sql_query_list.append(sql_query)

    def run(self):
        self.cursor = self.connection.cursor()
        self.cursor.execute(self.query)
        records_dict = self.cursor.fetchall()
        self.result.emit(records_dict)

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
        if first_run:
            self.create_database()
        self.connection_sql()
        self.connect_to_sql = self.connect_sql()
        # self.db_conn =
        # print("Create and run FoundThread")


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
        query_string = f"DELETE FROM {self.settingsDict['my-call']} WHERE 1;"
        sql_connect = self.connect_sql()
        query = sql_connect.cursor()
        query.execute(query_string)
        result = sql_connect.commit()
        return result

    def getQsoByCallPattern(self, patern):
        query = self.connect_sql().cursor()
        query.execute("SELECT * FROM " + self.settingsDict['my-call'] +
                      " WHERE `call` LIKE '" + patern + "'")
        QsosByCallPatternList = query.fetchall()
        return QsosByCallPatternList

    def getRange(self, start_id, step):
        db_conn = self.connect_sql()
        query = db_conn.cursor()
        query.execute("SELECT * FROM " + settingsDict['my-call'] + " WHERE `id`<" + str(
            start_id) + " ORDER BY id DESC LIMIT " + str(step))
        answer_db = query.fetchall()
        return answer_db

    def check_database(self, name_db):

        try:
            connection = pymysql.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_pass,
            )
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES LIKE '" + name_db + "'")
            answer = cursor.fetchall()

        except Exception:
            print("Except check connection to mysql")
            subprocess.call(["python3", "help_system.py", 'db-error'])
            exit(1)
            # answer = ()

        return answer

    def create_database(self):

        db_connect_new = pymysql.connect(
            host=self.db_host,
            user=self.db_user,
            password=self.db_pass,

        )
        cursor = db_connect_new.cursor()
        try:
            cursor.execute(f"USE {self.db_name}")
            print(cursor.fetchall())
        except pymysql.err.OperationalError:
            cursor.execute(f'CREATE DATABASE {self.db_name}')

    def connect_sql(self):
        if self.db_name == '':
            try:
                self.connection = pymysql.connect(
                    host=self.db_host,
                    user=self.db_user,
                    password=self.db_pass,

                )
            except Exception:
                print("Exception on DB.connect")
                subprocess.call(["python3", "help_system.py", 'db-error'])
                # Help("db")
                exit(0)

        else:
            try:
                self.connection = pymysql.connect(
                    host=self.db_host,
                    user=self.db_user,
                    password=self.db_pass,
                    db=self.db_name,
                    charset=self.db_charset,
                    cursorclass=DictCursor
                    )

                #self.main_connection
            except Exception:
                print("Exception on DB.connect (else) ")
                subprocess.call(["python3", "help_system.py", 'db-error'])

                # Help("db")
                exit(0)
        return self.connection

    def create_table(self, name_table, column_list):
        db_conn = self.connect_sql()
        sql_query = "CREATE TABLE " + name_table + "(`id` INT NOT NULL AUTO_INCREMENT"
        for column in column_list:
            sql_query += ", `" + column[0] + "` " + column[1]
        sql_query += ', PRIMARY KEY (`id`)) CHARACTER SET ' + str(self.db_charset)
        # print (sql_query)
        try:
            query = db_conn.cursor()
            result = query.execute(sql_query)
            print("result", result)

        except Exception:
            result = traceback.format_exc()
            # print("RESULT", result, pymysql.err.OperationalError)
        return result

    def record_qso_to_base(self, qso_dict, mode=''):
        db_conn = self.connect_sql()
        if len(qso_dict['TIME_ON'].strip()) == 4:
            time_format = qso_dict['TIME_ON'] + "00"
            # print("time_format:", time_format)
        else:
            time_format = qso_dict['TIME_ON']
        if len(str(qso_dict.get('TIME_OFF')).strip()) == 0 or qso_dict.get('TIME_OFF') is None:
            # print(f"Time_OFF none")
            time_off_format = time_format
        else:
            if len(qso_dict['TIME_OFF'].strip()) == 4:
                time_off_format = qso_dict['TIME_OFF'] + "00"
            else:
                time_off_format = qso_dict['TIME_OFF']
        if qso_dict['QSO_DATE'] != '':
            qso_date = qso_dict['QSO_DATE'][:4] + '-' + qso_dict['QSO_DATE'][4:6] + '-' + qso_dict['QSO_DATE'][6:]
        # print ("qso_date", qso_dict)

        call = qso_dict.get("OPERATOR")
        if call is None:
            call = self.settingsDict["my-call"]
        if qso_dict.get("STATION_CALLSIGN") is not None and qso_dict["STATION_CALLSIGN"] != '':
            call = qso_dict["STATION_CALLSIGN"]
        if mode == 'import':
            # print(qso_dict['CALL'])
            print("Time ON", time_format, qso_dict.get("TIME_ON"))
            print("Time OFF", time_off_format, qso_dict.get("TIME_OFF"))
            db_conn.cursor().execute("INSERT INTO `" + self.settingsDict['my-call'] + "` (`CALL`, `MODE`, `NAME`, `QSO_DATE`, `TIME_ON`,\
                       `TIME_OFF`, `QTH`, `RST_RCVD`, `RST_SENT`, `OPERATOR`, `COMMENT`, `EQSL_QSL_SENT`, `CLUBLOG_QSO_UPLOAD_STATUS`,\
                        `FREQ`, `BAND`, `ITUZ`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (
                str(qso_dict.get('CALL')).strip()[:50],
                str(qso_dict.get('MODE')).strip()[:50],
                str(qso_dict.get('NAME')).strip()[:50],
                qso_date,
                time_format,
                time_off_format,
                str(qso_dict.get("QTH")).strip()[:50],
                str(qso_dict.get("RST_RCVD")).strip()[:50],
                str(qso_dict.get("RST_SENT")).strip()[:50],
                call.strip(),
                str(qso_dict.get("COMMENT")).strip()[:500],
                str(qso_dict.get("EQSL_QSL_SENT")).strip(),
                str(qso_dict.get("CLUBLOG_QSO_UPLOAD_STATUS")).strip(),
                str(qso_dict.get("FREQ")).strip(),
                str(qso_dict.get("BAND")).strip(),
                str(qso_dict.get("ITUZ")).strip()
            )
                                     )

        else:
            db_conn.cursor().execute("INSERT INTO `" + self.settingsDict['my-call'] + "` (`CALL`, `MODE`, `NAME`, `QSO_DATE`, `TIME_ON`,\
            `TIME_OFF`, `QTH`, `RST_RCVD`, `RST_SENT`, `OPERATOR`, `COMMENT`, `EQSL_QSL_SENT`, `CLUBLOG_QSO_UPLOAD_STATUS`,\
             `FREQ`, `BAND`, `ITUZ`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (
                str(qso_dict.get('CALL')).strip(),
                str(qso_dict.get('MODE')).strip(),
                str(qso_dict.get('NAME')).strip(),
                qso_date,
                time_format,
                time_off_format,
                str(qso_dict.get("QTH")).strip(),
                str(qso_dict.get("RST_RCVD")).strip(),
                str(qso_dict.get("RST_SENT")).strip(),
                str(qso_dict.get("OPERATOR")).strip(),
                str(qso_dict.get("COMMENT")).strip(),
                str(qso_dict.get("EQSL_QSL_SENT")).strip(),
                str(qso_dict.get("CLUBLOG_QSO_UPLOAD_STATUS")).strip(),
                str(qso_dict.get("FREQ")).strip(),
                str(qso_dict.get("BAND")).strip(),
                str(qso_dict.get("ITUZ")).strip()
            )
                                     )

        db_conn.commit()
        cursor = self.connection.cursor()
        cursor.execute("SELECT LAST_INSERT_ID()")
        last_id = cursor.fetchall()

        return last_id

    def check_table(self, name_table):
        db_conn = self.connect_sql()
        sql_query = "SHOW TABLES LIKE" + name_table + ";"
        curr = db_conn.cursor()
        try:
            result = curr.execute(sql_query)
        except Exception:
            result = ()
        return result

    def get_all_records(self, count=0):
        cursor = self.connect_sql().cursor()
        if count > 0:
            records = cursor.execute(
                "SELECT * FROM " + self.settingsDict["my-call"] + " ORDER BY QSO_DATE + TIME_ON DESC LIMIT " + str(count))
        else:
            records = cursor.execute(
                "SELECT * FROM " + self.settingsDict["my-call"] + " ORDER BY QSO_DATE + TIME_ON DESC")

        # print(records)
        records_dict = cursor.fetchall()
        return records_dict

    def get_record_by_id(self, id):
        cursor = self.connection.cursor()
        records = cursor.execute("SELECT * FROM " + self.settingsDict["my-call"] + " WHERE `id`=%s", [id])
        records_dict = cursor.fetchall()
        return records_dict

    def search_like_qsos(self, text):
        sql_query = "SELECT * FROM `" + self.settingsDict['my-call'] + "` WHERE `CALL`  LIKE '" + text + "%';"
        self.found_thread = FoundThread(connection=self.connect_to_sql, query=sql_query)
        self.found_thread.result.connect(self.like_qso_return)
        self.found_thread.start()

    @QtCore.pyqtSlot(object)
    def like_qso_return(self, obj):
        print("I am Object", obj)
        self.search_in_db_like_signal.emit(obj)

    def search_qso_in_base(self, call):
        connection = self.connect_sql()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM `" + self.settingsDict['my-call'] + "` WHERE `CALL`=%s", [call.strip()])
        records = cursor.fetchall()
        # print ("Search in Base Found record:_>", records)
        return records

    def search_qso_by_full_data(self, call, date, time_qso, band, mode):
        connection = self.connect_sql()
        cursor = connection.cursor()
        # print("seach_qso_by_full_data:", call, date, time_qso, band, mode)
        cursor.execute("SELECT * FROM `" + self.settingsDict['my-call'] + "` WHERE `CALL`=%s AND `QSO_DATE`=%s AND `TIME_ON`=%s AND `BAND`=%s AND `MODE`=%s", [call.strip(), date.strip(), time_qso.strip(), band.strip(), mode.strip()])
        records = cursor.fetchall()
        # print ("Search in Base Found record:_>", records)
        return records

    def edit_qso(self, record_id, object_dict):
        connection = self.connect_sql()
        cursor = connection.cursor()
        update_query = "UPDATE `" + self.settingsDict['my-call'] + "` SET "
        keys = object_dict.keys()
        values = []
        i = 0
        for key in keys:
            i += 1
            # if object_dict[key] != "" and object_dict[key] != " ":
            if key in self.settingsDict["db_fields"] and \
                    object_dict[key] != "" and object_dict[key] != " ":
                update_query += "`" + key + "` = %s"
                if len(keys) != i:
                    update_query += ", "
                values.append(object_dict[key])
        update_query += "WHERE `id`= %s"
        update_query = update_query.replace(", WHERE", " WHERE")
        values.append(record_id)
        # print(update_query)
        # print(values)
        # print(record_id)
        # print("query:" )
        cursor.execute(update_query, values)
        connection.commit()

    def delete_qso(self, record_id):
        connect = self.connect_sql()
        cursor = connect.cursor()
        cursor.execute("DELETE FROM " + settingsDict['my-call'] + " WHERE `id`=%s", [int(record_id)])
        connect.commit()


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
        message.exec_()


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

    file = open(Path(__file__).parent/ "settings.cfg", "r")
    for configstring in file:
        if configstring != '' and configstring != ' ' and configstring[0] != '#':
            configstring = configstring.strip()
            configstring = configstring.replace("\r", "")
            configstring = configstring.replace("\n", "")
            splitString = configstring.split('=')
            settingsDict.update({splitString[0]: splitString[1]})
    file.close()

    ####
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = QApplication(sys.argv)
    settingsDict.update({"app":app})
    flag = 1
    if settingsDict['my-call'] == "":
        hello_window = hello_window(table_columns)

    else:

        db = Db(settingsDict=settingsDict)
        answer = db.check_database(settingsDict['db-name'])
        if answer == ():
            db.create_database()
            settingsDict['db-name'] = 'linuxlog'
        else:
            print("Database found")
        try:
            try:
                db.check_table(settingsDict['my-call'])
                print("Get table")
            except Exception:

                table = db.create_table(
                    settingsDict['my-call'].upper(),
                    table_columns
                )
                print("Create table")
        except Exception:
            try:
                db = Db(settingsDict=settingsDict)
                db_connect_new = db.connect_sql()
                cursor = db_connect_new.cursor()
                cursor.execute('CREATE DATABASE linuxlog')
                db_connect_new.close()
                db_connect = db.connect_sql()
                print("Create DB Linuxlog")
            except Exception:
                subprocess.call(["python3", "help_system.py-old", 'db-error'])
                exit(1)

        # global table_columns

        # init all global class
        logWindow = Log_Window_2()
        logSearch = LogSearch()
        internetSearch = InternetSearch()
        logForm = LogForm(settingsDict, logSearch)
        telnetCluster = TelnetCluster()
        tci_recv = tci.tci_connect(settingsDict, log_form=logForm)
        about_window = About_window("LinuxLog",
                                    "Version: " + APP_VERSION + "<br><a href='http://linuxlog.com.ua'>http://linuxlog.com.ua</a><br>Baston Sergey<br>UR4LGA<br>bastonsv@gmail.com")
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
        if settingsDict['cat'] == 'enable':
            pass
            # logForm.start_cat()
        if settingsDict['tci'] == 'enable':
            tci_recv.start_tci(settingsDict["tci-server"], settingsDict["tci-port"])
        tci_sndr = tci.Tci_sender(settingsDict["tci-server"] + ":" + settingsDict["tci-port"], "Disable", logForm, settingsDict)
    sys.exit(app.exec())
