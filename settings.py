#import telnetlib
import time
from pathlib import Path

import main
import internetworker
import traceback
import parse
import shutil
import std
import json
from PyQt6.QtWidgets import QMenu, QApplication, QWidget, QMainWindow, QTableView, QTableWidget, QTableWidgetItem, \
    QTextEdit, \
    QLineEdit, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QFrame, QSizePolicy
from PyQt6 import QtCore
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import  QWidget, QMessageBox, QLineEdit, QPushButton, QLabel, QColorDialog, QVBoxLayout, QHBoxLayout, QComboBox, QCheckBox, QFileDialog
from PyQt6.QtGui import QIcon, QFocusEvent, QPixmap, QTextTableCell, QStandardItemModel, QPalette, QColor, QAction
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtCore import QThread
from time import gmtime, strftime, localtime

class Menu (QWidget):
    def __init__(self, db, app_env, settingsDict, telnetCluster, logForm, logSearch,
                 logWindow, internetSearch, tci_recv, tci_sndr, table_columns, parent=None):
        super(Menu, self).__init__(parent)
        self.db_sql = db
        self.settingsDict = settingsDict
        self.label_style = "font: 12px;"
        self.initUI()
        self.initData()
        self.telnetCluster = telnetCluster
        self.logForm = logForm
        self.logSearch = logSearch
        self.logWindow = logWindow
        self.internetSearch = internetSearch
        self.tci_rcvr = tci_recv
        self.tci_sender = tci_sndr
        self.table_columns = table_columns
        self.app_env = app_env
        #print ("Menu init tci class:", self.tci_class.currentThreadId())
        #self.initUI()

    def initUI(self):

        self.setGeometry(300,
                         300,
                         600,
                         300)
        self.setWindowTitle('LinuxLog | Settings')

        self.setWindowIcon(QIcon('logo.png'))
        style = "QWidget{background-color:" + self.settingsDict['background-color'] + "; color:" + self.settingsDict['color'] + ";}"
        self.setStyleSheet(style)
    # declaration tab
        self.tab = QtWidgets.QTabWidget()
        self.tab.setMovable(False)
        self.tab.setUsesScrollButtons(False)
        self.general_tab = QWidget()

        self.cluster_tab = QWidget()
        self.tci_tab = QWidget()
        self.cat_tab = QWidget()
        self.io_tab = QWidget()
        self.service_widget = QWidget()
        self.country_list_edit = QWidget()
    #
        self.tab.addTab(self.general_tab, "General")
        self.tab.addTab(self.cluster_tab, "Cluster")
        self.tab.addTab(self.tci_tab, "TCI/ RIG control")
        self.tab.addTab(self.cat_tab, "CAT")
        self.tab.addTab(self.io_tab, "Log file")
        self.tab.addTab(self.service_widget, "Services")
        self.tab.addTab(self.country_list_edit, "Country List")
    # create General Tab
        formstyle = "background: "+self.settingsDict['form-background']+"; color: "+\
                    self.settingsDict['color-table']+"; "
        self.style_checkbox = "color:" + self.settingsDict['color'] + "; font-size: 12px;"
        self.style_headers = "font-weight: bold; background-color:" + self.settingsDict['background-color'] + "; color:" + self.settingsDict['color'] + ";"
        self.style_small = "font-style: italic; font-size: 12px; background-color:" + self.settingsDict['background-color'] + "; color:" + self.settingsDict['color'] + ";"
        self.general_tab.layout = QVBoxLayout(self) # create vertical lay
        self.call_label = QLabel("You Callsign:")
        self.call_label.setFixedWidth(80)
        self.call_input = QLineEdit()
        self.call_input.setFixedWidth(100)
        self.call_input.setStyleSheet(formstyle)
        # Checkbox Window border
        self.window_border = QCheckBox("Show window border (will be applied after restarting)")
        self.window_border.setStyleSheet(self.style_checkbox)
        # Chekbox SWL
        self.swl_chekbox = QCheckBox("Enable SWL mode")
        self.swl_chekbox.setStyleSheet(self.style_checkbox)
        # Button clear base
        self.clear_base_button = QPushButton("Clear base (DELETE all QSO)")
        self.clear_base_button.clicked.connect(self.clear_base_qso)
        self.dlg = QColorDialog(self)
        self.back_color_label = QLabel("Window color")
        self.back_color_label.setStyleSheet(self.label_style)
        self.back_color_input = QPushButton()
        self.back_color_input.clicked.connect(self.back_color_select)
        self.back_color_input.setFixedWidth(70)
        self.back_color_input.setStyleSheet("background:" + self.settingsDict['background-color'] + "; color:" + self.settingsDict['background-color'] + ";")
        self.back_color_input.setText(self.settingsDict['background-color'])
        #self.back_color_input.setStyleSheet(formstyle)
        self.text_color_label = QLabel("Text color")
        self.text_color_label.setStyleSheet(self.label_style)
        self.text_color_input = QPushButton()
        self.text_color_input.clicked.connect(self.text_color_select)
        self.text_color_input.setFixedWidth(70)
        self.text_color_input.setStyleSheet("background:" + self.settingsDict['color'] + "; color:" + self.settingsDict['color'] + ";")
        self.text_color_input.setText(self.settingsDict['color'])

        #self.text_color_input.setStyleSheet(formstyle)
        self.form_color_label = QLabel("Form background color")
        self.form_color_label.setStyleSheet(self.label_style)
        self.form_color_input = QPushButton()
        self.form_color_input.clicked.connect(self.form_color_select)
        self.form_color_input.setFixedWidth(70)
        self.form_color_input.setStyleSheet("background: " + self.settingsDict['form-background'] + "; color:" + self.settingsDict['form-background'] + ";")
        self.form_color_input.setText(self.settingsDict['form-background'])
        #
        self.text_form_color_label = QLabel("Form text color")
        self.text_form_color_label.setStyleSheet(self.label_style)
        self.text_form_color_button = QPushButton()
        self.text_form_color_button.clicked.connect(self.form_text_color_select)
        self.text_form_color_button.setFixedWidth(70)
        self.text_form_color_button.setStyleSheet("background: " + self.settingsDict['color-table']+ "; color: " + self.settingsDict['color-table'] + ";")
        self.text_form_color_button.setText(self.settingsDict['color-table'])

        # Fields DB
        self.label_db = QLabel()
        self.label_db.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.label_db.setStyleSheet(style+"text-align: center;")
        self.label_db.setText("Enter fields for MySQL database")

        # Login (Username) DB fields
        self.db_login_label = QLabel()
        self.db_login_label.setStyleSheet(style)
        self.db_login_label.setFixedWidth(70)
        self.db_login_label.setText("Username:")

        self.db_login = QLineEdit()
        self.db_login.setFixedWidth(150)
        self.db_login.setFixedHeight(30)
        self.db_login.setStyleSheet(formstyle)

        # Password DB fields
        self.db_pass_label = QLabel()
        self.db_pass_label.setStyleSheet(style)
        self.db_pass_label.setFixedWidth(70)
        self.db_pass_label.setText("Password:")

        self.db_pass = QLineEdit()
        self.db_pass.setFixedWidth(150)
        self.db_pass.setFixedHeight(30)
        self.db_pass.setStyleSheet(formstyle)

        # DB Name (Username) DB fields
        self.db_name_label = QLabel()
        self.db_name_label.setStyleSheet(style)
        self.db_name_label.setFixedWidth(70)
        self.db_name_label.setText("DB Name:")

        self.db_name = QLineEdit()
        self.db_name.setFixedWidth(150)
        self.db_name.setFixedHeight(30)
        self.db_name.setStyleSheet(formstyle)

        # DB Name (Username) DB fields
        self.db_host_label = QLabel()
        self.db_host_label.setStyleSheet(style)
        self.db_host_label.setFixedWidth(70)
        self.db_host_label.setText("Host:")

        self.db_host = QLineEdit()
        self.db_host.setFixedWidth(150)
        self.db_host.setFixedHeight(30)
        self.db_host.setStyleSheet(formstyle)
        ########

        # setup all elements to vertical lay
        self.call_lay = QHBoxLayout()
        self.call_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.call_lay.addWidget(self.call_label)
        self.call_lay.addWidget(self.call_input)
        self.call_lay.addWidget(self.swl_chekbox)
        self.call_lay.addWidget(self.clear_base_button)
        self.general_tab.layout.addLayout(self.call_lay)


        self.general_tab.layout.addSpacing(20)

        #self.general_tab.layout.addWidget(self.swl_chekbox)

        self.horizontal_lay = QHBoxLayout()
        self.color_lay = QVBoxLayout()
        self.color_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.color_lay.addWidget(self.window_border)
        self.color_lay.addWidget(self.back_color_label)
        self.color_lay.addWidget(self.back_color_input)
        self.color_lay.addWidget(self.text_color_label)
        self.color_lay.addWidget(self.text_color_input)
        self.color_lay.addWidget(self.form_color_label)
        self.color_lay.addWidget(self.form_color_input)
        self.color_lay.addWidget(self.text_form_color_label)
        self.color_lay.addWidget(self.text_form_color_button)
        self.horizontal_lay.addLayout(self.color_lay)
        self.db_lay = QVBoxLayout()
        self.db_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Setup label db
        self.db_lay.addWidget(self.label_db)
        self.db_lay.addSpacing(5)

        # setup login (Username) fields on lay
        self.login_bd_lay = QHBoxLayout()
        self.login_bd_lay.addWidget(self.db_login_label)
        self.login_bd_lay.addWidget(self.db_login)

        # setup password fields on lay
        self.password_bd_lay = QHBoxLayout()
        self.password_bd_lay.addWidget(self.db_pass_label)
        self.password_bd_lay.addWidget(self.db_pass)

        # setup DB Name fields on lay
        self.name_bd_lay = QHBoxLayout()
        self.name_bd_lay.addWidget(self.db_name_label)
        self.name_bd_lay.addWidget(self.db_name)

        # setup DB Host fields on lay
        self.host_bd_lay = QHBoxLayout()
        self.host_bd_lay.addWidget(self.db_host_label)
        self.host_bd_lay.addWidget(self.db_host)

        # self.db_lay.addWidget(self.label_db)
        self.db_lay.addLayout(self.login_bd_lay)
        self.db_lay.addLayout(self.password_bd_lay)
        self.db_lay.addLayout(self.login_bd_lay)
        self.db_lay.addLayout(self.password_bd_lay)
        self.db_lay.addLayout(self.name_bd_lay)
        self.db_lay.addLayout(self.host_bd_lay)
        self.db_lay.addStretch(1)

        self.horizontal_lay.addLayout(self.db_lay)
        self.general_tab.layout.addLayout(self.horizontal_lay)

        #self.general_tab.layout.addWidget(self.back_color_label)
        #self.general_tab.layout.addWidget(self.back_color_input)
        #self.general_tab.layout.addSpacing(20)
        #self.general_tab.layout.addWidget(self.text_color_label)
        #self.general_tab.layout.addWidget(self.text_color_input)
        #self.general_tab.layout.addSpacing(20)
        #self.general_tab.layout.addWidget(self.form_color_label)
        #self.general_tab.layout.addWidget(self.form_color_input)
        #self.general_tab.layout.addWidget(self.text_form_color_label)
        #self.general_tab.layout.addWidget(self.text_form_color_button)

        self.general_tab.setLayout(self.general_tab.layout)

    # create Cluster tab

        self.cluster_tab.layout = QVBoxLayout(self)
        self.cluster_host = QLabel("Cluster host:")
        self.cluster_host_input = QLineEdit()
        self.cluster_host_input.setFixedWidth(150)
        self.cluster_host_input.setStyleSheet(formstyle)
        self.cluster_port = QLabel("Cluster port:")
        self.cluster_port_input = QLineEdit()
        self.cluster_port_input.setFixedWidth(50)
        self.cluster_port_input.setStyleSheet(formstyle)

        # create host:port lay
        self.host_port_lay = QHBoxLayout()
        self.host_lay = QVBoxLayout()
        self.host_lay.addWidget(self.cluster_host)
        self.host_lay.addWidget(self.cluster_host_input)

        self.port_lay = QVBoxLayout()
        self.port_lay.addWidget(self.cluster_port)
        self.port_lay.addWidget(self.cluster_port_input)

        self.host_port_lay.addLayout(self.host_lay)
        self.host_port_lay.addLayout(self.port_lay)


        # Create calibrate cluster
        self.calibrate_lay = QHBoxLayout()
        ## Create text label
        self.text_and_button_Vlay = QVBoxLayout()
        text = "Press \"Start claibrate\" and select Callsign and Freq \n" \
               "from the received line from the telnet cluster"
        self.message_label = QLabel(text)
        self.message_label.setStyleSheet("font: 12px;")
        self. text_and_button_Vlay.addWidget(self.message_label)

        self.button_and_combo = QHBoxLayout()
        ## Create group from button and combobox
        self.cluster_start_calibrate_button = QPushButton("Start \n callibrate")
        self.cluster_start_calibrate_button.setFixedWidth(100)
        self.cluster_start_calibrate_button.setFixedHeight(60)
        self.button_and_combo.addWidget(self.cluster_start_calibrate_button)
        self.combo_lay = QVBoxLayout()
        self.call_H = QHBoxLayout()
        self.call_H.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.cluster_call_label = QLabel("Call:")

        self.cluster_combo_call = QComboBox()

        self.freq_H = QHBoxLayout()
        self.freq_H.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.cluster_freq_label = QLabel("Freq:")
        self.cluster_combo_freq = QComboBox()
        self.call_H.addWidget(self.cluster_call_label)
        self.call_H.addWidget(self.cluster_combo_call)
        self.freq_H.addWidget(self.cluster_freq_label)
        self.freq_H.addWidget(self.cluster_combo_freq)
        self.combo_lay.addLayout(self.call_H)
        self.combo_lay.addLayout(self.freq_H)
        self.button_and_combo.addLayout(self.combo_lay)
        self.text_and_button_Vlay.addLayout(self.button_and_combo)

        self.calibrate_lay.addLayout(self.text_and_button_Vlay)




        ## Create filter band
        self.cluster_filter_band_combo = QCheckBox("Filter BAND")
        self.cluster_filter_band_combo.setStyleSheet("QWidget{ color:" + self.settingsDict['color'] + "; font-size: 12px;}")
        self.cluster_filter_band_input = QLineEdit()
        self.cluster_filter_band_input.setFixedWidth(80)
        self.cluster_filter_band_input.setFixedHeight(20)
        self.cluster_filter_band_input.setStyleSheet("background-color:"+self.settingsDict['form-background']+"; font-size: 12px")
        text = "Bands in m."
        self.message_label_band = QLabel(text)
        self.message_label_band.setStyleSheet("font: 12px;")

        self.filter_band_lay = QVBoxLayout()
        self.filter_band_lay.addWidget(self.cluster_filter_band_combo)
        self.filter_band_lay.addWidget(self.message_label_band)
        self.filter_band_lay.addWidget(self.cluster_filter_band_input)



        ## Create filter spot
        self.cluster_filter_spot_combo = QCheckBox("Filter SPOT")
        self.cluster_filter_spot_combo.setStyleSheet(
            "QWidget {color:" + self.settingsDict['color'] + "; font-size: 12px;}")
        self.cluster_filter_spot_input = QLineEdit()
        self.cluster_filter_spot_input.setFixedWidth(80)
        self.cluster_filter_spot_input.setFixedHeight(20)
        self.cluster_filter_spot_input.setStyleSheet(
            "background-color:" + self.settingsDict['form-background'] + "; font-size: 12px")
        text = "Spot prefixes"
        self.message_label_spot = QLabel(text)
        self.message_label_spot.setStyleSheet("font: 12px;")

        self.filter_spot_lay = QVBoxLayout()
        self.filter_spot_lay.addWidget(self.cluster_filter_spot_combo)
        self.filter_spot_lay.addWidget(self.message_label_spot)
        self.filter_spot_lay.addWidget(self.cluster_filter_spot_input)

        ## create filter spotter
        self.cluster_filter_spotter_combo = QCheckBox("Filter SPOTTER")
        self.cluster_filter_spotter_combo.setStyleSheet(
            "QWidget {color:" + self.settingsDict['color'] + "; font-size: 12px;}")
        self.cluster_filter_spotter_input = QLineEdit()
        self.cluster_filter_spotter_input.setFixedWidth(80)
        self.cluster_filter_spotter_input.setFixedHeight(20)
        self.cluster_filter_spotter_input.setStyleSheet(
            "background-color:" + self.settingsDict['form-background'] + "; font-size: 12px")
        text = "Spotter prefixes"
        self.message_label_spotter = QLabel(text)
        self.message_label_spotter.setStyleSheet("font: 12px;")

        self.filter_spotter_lay = QVBoxLayout()
        self.filter_spotter_lay.addWidget(self.cluster_filter_spotter_combo)
        self.filter_spotter_lay.addWidget(self.message_label_spotter)
        self.filter_spotter_lay.addWidget(self.cluster_filter_spotter_input)

        text = "All value separate by comma"
        self.filter_message_label = QLabel(text)
        self.filter_message_label.setStyleSheet("font: 12px;")

        self.filters_Hlay = QHBoxLayout()
        self.filters_Hlay.addLayout(self.filter_band_lay)
        self.filters_Hlay.addLayout(self.filter_spot_lay)
        self.filters_Hlay.addLayout(self.filter_spotter_lay)

        self.filters_lay = QVBoxLayout()
        self.filters_lay.addSpacing(10)
        self.filters_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filters_lay.addLayout(self.filters_Hlay)
        self.filters_lay.addWidget(self.filter_message_label)
        self.filters_lay.addSpacing(10)
        Separador = QFrame()
        Separador.setFrameShape(QFrame.Shape.HLine)
        Separador.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        Separador.setLineWidth(1)
        self.filters_lay.addWidget(Separador)


        ## Create List view for input string from cluster

        self.line_text = QLabel()

        self.line_text.setFixedHeight(50)
        # Set all layers to window
        self.cluster_tab.layout.addLayout(self.host_port_lay)
        self.cluster_tab.layout.addSpacing(10)
        self.cluster_tab.layout.addLayout(self.filters_lay)
        self.cluster_tab.layout.addLayout(self.calibrate_lay)
        self.cluster_tab.layout.addWidget(self.line_text)

        ## install lay to main tab (Cluster)
        self.cluster_tab.setLayout(self.cluster_tab.layout)


    # create TCI Tab

        self.tci_enable_combo_lay = QHBoxLayout()
        self.tci_enable_combo_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tci_enable_combo = QCheckBox("TCI Enable")
        self.tci_enable_combo.setStyleSheet("QWidget {"+self.settingsDict['color']+"}")
        self.tci_enable_combo_lay.addWidget(self.tci_enable_combo)
        self.tci_auto_rs_checkbox = QCheckBox("RS from TCI")
        self.tci_auto_rs_checkbox.setStyleSheet("QWidget {"+self.settingsDict['color']+"}")
# + self.settingsDict['color']

        # Layout and checkbox Rigctl
        self.rigctl_enable_combo_lay = QHBoxLayout()
        self.rigctl_enable_combo_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rigctl_enable_combo = QCheckBox("RIGctl Enable")
        self.rigctl_enable_combo.setStyleSheet("QWidget {" + self.settingsDict['color'] + "}")
        self.rigctl_enable_combo_lay.addWidget(self.rigctl_enable_combo)


        self.tci_tab.layout = QVBoxLayout(self)
        self.tci_host = QLabel("TCI host:")
        self.tci_host_input = QLineEdit()
        self.tci_host_input.setFixedWidth(150)
        self.tci_host_input.setStyleSheet(formstyle)
        self.tci_port = QLabel("TCI port:")
        self.tci_port_input = QLineEdit()
        self.tci_port_input.setFixedWidth(50)
        self.tci_port_input.setStyleSheet(formstyle)
        self.host_port_lay = QHBoxLayout()

        # self.tci_tab.layout = QVBoxLayout(self)
        self.rigctl_host = QLabel("RIGctl host:")
        self.rigctl_host_input = QLineEdit()
        self.rigctl_host_input.setFixedWidth(150)
        self.rigctl_host_input.setStyleSheet(formstyle)


        # Port rigctl rx1
        self.rigctl_port = QLabel("RIGctl port:")
        self.rigctl_port_input = QLineEdit()
        self.rigctl_port_input.setFixedWidth(50)
        self.rigctl_port_input.setStyleSheet(formstyle)

        # Port rigctl rx2
        self.rigctl_port_rx2 = QLabel("RIGctl port RX2:")
        self.rigctl_port_input_rx2 = QLineEdit()
        self.rigctl_port_input_rx2.setFixedWidth(50)
        self.rigctl_port_input_rx2.setStyleSheet(formstyle)

        self.host_port_lay = QHBoxLayout()

        # create host:port lay
        # self.host_lay = QVBoxLayout()



        # TCI host lay
        self.host_lay = QVBoxLayout()
        self.host_lay.addWidget(self.tci_host)
        self.host_lay.addWidget(self.tci_host_input)

        # TCI host lay
        self.port_lay = QVBoxLayout()
        self.port_lay.addWidget(self.tci_port)
        self.port_lay.addWidget(self.tci_port_input)



        # Rigctl host lay
        self.rigctl_host_lay = QVBoxLayout()
        self.rigctl_host_lay.addWidget(self.rigctl_host)
        self.rigctl_host_lay.addWidget(self.rigctl_host_input)

        # Rigctl port lay
        self.rigctl_port_lay = QVBoxLayout()
        self.rigctl_port_lay.addWidget(self.rigctl_port)
        self.rigctl_port_lay.addWidget(self.rigctl_port_input)

        # Rigctl port lay
        self.rigctl_port_lay_rx2 = QVBoxLayout()
        self.rigctl_port_lay_rx2.addWidget(self.rigctl_port_rx2)
        self.rigctl_port_lay_rx2.addWidget(self.rigctl_port_input_rx2)


        # Setup TCI port and host to Hlay
        self.host_port_lay.addLayout(self.host_lay)
        self.host_port_lay.addLayout(self.port_lay)
        self.host_port_lay.addWidget(self.tci_auto_rs_checkbox)

        self.rigctl_host_port = QHBoxLayout()
        self.rigctl_host_port.addLayout(self.rigctl_host_lay)
        self.rigctl_host_port.addLayout(self.rigctl_port_lay)
        self.rigctl_host_port.addLayout(self.rigctl_port_lay_rx2)

        self.tci_tab.layout.addLayout(self.tci_enable_combo_lay)
        self.tci_tab.layout.addLayout(self.host_port_lay)
        self.tci_tab.layout.addWidget(Separador)
        self.tci_tab.layout.addLayout(self.rigctl_enable_combo_lay)
        self.tci_tab.layout.addLayout(self.rigctl_host_port)
        self.tci_tab.layout.addSpacing(250)
        self.tci_tab.setLayout(self.tci_tab.layout)
    # Create CAT tab
        # Cat Enable
        self.cat_enable = QCheckBox('CAT Enable')
        self.cat_enable.setStyleSheet(style)
        # Cat port
        self.port_cat_label = QLabel("CAT port (ex. ttyS20)")
        self.port_cat_label.setStyleSheet(style)
        self.port_cat_label.setFixedWidth(150)
        self.port_cat_input = QLineEdit()                                     # CAT port
        self.port_cat_input.setStyleSheet(formstyle)
        self.port_cat_input.setFixedWidth(100)
        self.port_cat_lay = QHBoxLayout()                                     # PORT lay
        #self.port_cat_lay.setAlignment(Qt.AlignCenter)
        self.port_cat_lay.addWidget(self.port_cat_label)
        self.port_cat_lay.addWidget(self.port_cat_input)
        # Cat baud
        self.baud_cat_label = QLabel("Baud rate")
        self.baud_cat_label.setStyleSheet(style)
        self.baud_cat_label.setFixedWidth(100)
        self.baud_cat_combo = QComboBox()
        self.baud_cat_combo.setFixedWidth(100)
        self.baud_cat_combo.setFixedHeight(30)
        self.baud_cat_combo.setStyleSheet(style)
        self.baud_cat_combo.addItems(['1200', '2400','4800', '9600', '19200', '38400', '57600', '115200'])
        self.baud_cat_lay = QHBoxLayout()                                       # BAUD lay
        self.baud_cat_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.baud_cat_lay.addWidget(self.baud_cat_label)
        self.baud_cat_lay.addWidget(self.baud_cat_combo)
        # Cat parity
        self.parity_cat_label = QLabel('Parity')
        self.parity_cat_label.setStyleSheet(style)
        self.parity_cat_label.setFixedWidth(100)
        self.parity_cat_combo = QComboBox()
        self.parity_cat_combo.setFixedWidth(100)
        self.parity_cat_combo.setFixedHeight(30)
        self.parity_cat_combo.setStyleSheet(style)
        self.parity_cat_combo.addItems(['None', 'Odd', 'Even', 'Mark', 'Space'])
        self.parity_cat_lay = QHBoxLayout()                                     # PARITY lay
        self.parity_cat_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parity_cat_lay.addWidget(self.parity_cat_label)
        self.parity_cat_lay.addWidget(self.parity_cat_combo)
        # Cat Data
        self.data_cat_label = QLabel('Data')
        self.data_cat_label.setStyleSheet(style)
        self.data_cat_label.setFixedWidth(100)
        self.data_cat_combo = QComboBox()
        self.data_cat_combo.setFixedWidth(100)
        self.data_cat_combo.setFixedHeight(30)
        self.data_cat_combo.setStyleSheet(style)
        self.data_cat_combo.addItems(['5', '6', '7', '8'])
        self.data_cat_lay = QHBoxLayout()                                       # DATA lay
        self.data_cat_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.data_cat_lay.addWidget(self.data_cat_label)
        self.data_cat_lay.addWidget(self.data_cat_combo)
        # Cat Stop Bit
        self.stop_cat_label = QLabel('Stop bit')
        self.stop_cat_label.setStyleSheet(style)
        self.stop_cat_label.setFixedWidth(100)
        self.stop_cat_combo = QComboBox()
        self.stop_cat_combo.setFixedWidth(100)
        self.stop_cat_combo.setFixedHeight(30)
        self.stop_cat_combo.setStyleSheet(style)
        self.stop_cat_combo.addItems(['1', '1.5', '2'])
        self.stop_cat_lay = QHBoxLayout()                                       # Stop lay
        self.stop_cat_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stop_cat_lay.addWidget(self.stop_cat_label)
        self.stop_cat_lay.addWidget(self.stop_cat_combo)
        # Cat protocol
        self.protocol_cat_label = QLabel('Protocol')
        self.protocol_cat_label.setStyleSheet(style)
        self.protocol_cat_label.setFixedWidth(100)
        self.protocol_cat_combo = QComboBox()
        self.protocol_cat_combo.setFixedWidth(120)
        self.protocol_cat_combo.setFixedHeight(30)
        self.protocol_cat_combo.setStyleSheet(style)
        self.protocol_cat_combo.addItems(['ExpertSDR', 'Kenwood', 'Icom - not tested'])
        self.protocol_cat_lay = QHBoxLayout()                                   # Protocol lay
        self.protocol_cat_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.protocol_cat_lay.addWidget(self.protocol_cat_label)
        self.protocol_cat_lay.addWidget(self.protocol_cat_combo)

        self.cat_layer = QVBoxLayout()
        self.cat_layer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cat_layer.addWidget(self.cat_enable)
        self.cat_layer.addLayout(self.port_cat_lay)
        self.cat_layer.addLayout(self.baud_cat_lay)
        self.cat_layer.addLayout(self.parity_cat_lay)
        self.cat_layer.addLayout(self.data_cat_lay)
        self.cat_layer.addLayout(self.stop_cat_lay)
        self.cat_layer.addLayout(self.protocol_cat_lay)
        self.cat_tab.setLayout(self.cat_layer)
        #


    # Create io_tab
        self.io_tab_lay = QVBoxLayout()
        self.io_tab_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.import_button = QPushButton("Import ADI")
        self.import_button.setFixedSize(150, 30)
        self.import_button.clicked.connect(self.import_adi)
        self.import_button.setStyleSheet("width: 100px;")
        self.export_button = QPushButton("Export ALL log to ADI")
        self.export_button.clicked.connect(self.export_adi)
        self.export_button.setFixedSize(150, 30)
        self.export_clublog_button = QPushButton("Export ALL to ClubLog")
        self.export_clublog_button.clicked.connect(self.export_adi_clublog)
        self.export_clublog_button.setFixedSize(150, 30)
        self.export_clublog_button.setToolTip("ATTENTION: This export will MERGE the QSO from the log with the Club Log base")

        self.io_tab_lay.addWidget(self.import_button)
        self.io_tab_lay.addWidget(self.export_button)
        self.io_tab_lay.addWidget(self.export_clublog_button)
        self.io_tab.setLayout(self.io_tab_lay)

    # Create Services tab

        self.service_tab = QVBoxLayout()
        self.service_tab.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # create elements form
        self.eqsl_lay = QVBoxLayout()
        self.eqsl_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.eqsl_label = QLabel("eQSL")
        self.eqsl_label.setStyleSheet(self.style_headers)

        self.eqsl_lay.addWidget(self.eqsl_label)
        self.eqsl_lay.addSpacing(10)
        self.eqsl_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.eqsl_activate = QHBoxLayout()
        self.eqsl_chekBox = QCheckBox("Auto sent eQSL after QSO")
        self.eqsl_chekBox.setStyleSheet("color:" + self.settingsDict['color'] + "; font-size: 12px; border-color: white;")

        self.eqsl_activate.addWidget(self.eqsl_chekBox)
        #self.eqsl_activate.addWidget(QLabel("eQSL.cc"))

        self.eqsl_form = QVBoxLayout()


        self.login = QHBoxLayout()
        self.login.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.eqsl_login = QLabel("Login:")
        self.eqsl_login.setStyleSheet(style)
        self.eqsl_login.setMaximumWidth(75)
        self.login.addWidget(self.eqsl_login)
        self.eqsl_login = QLineEdit()
        self.eqsl_login.setFixedWidth(200)
        self.eqsl_login.setStyleSheet(formstyle)
        self.login.addWidget(self.eqsl_login)
        #self.login.addSpacing(50)
        self.password = QHBoxLayout()
        self.password.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.eqsl_pass_label = QLabel("Password:")
        self.eqsl_pass_label.setStyleSheet(style)
        self.eqsl_pass_label.setMaximumWidth(75)
        self.password.addWidget(self.eqsl_pass_label)
        self.eqsl_password = QLineEdit()
        self.eqsl_password.setFixedWidth(200)
        self.eqsl_password.setStyleSheet(formstyle)
        self.password.addWidget(self.eqsl_password)
        self.password.addSpacing(50)
        self.eqsl_form.addLayout(self.login)
        self.eqsl_form.addLayout(self.password)
        self.eqsl_lay.addLayout(self.eqsl_form)
        self.color_label_eqsl = QLabel("Color for eQSL complited: ")
        self.color_label_eqsl.setStyleSheet(style)
        self.color_button_eqsl = QPushButton()
        self.color_button_eqsl.setStyleSheet("background:"+self.settingsDict['eqsl-sent-color']+"; color:"+self.settingsDict['eqsl-sent-color'])
        self.color_button_eqsl.setText(self.settingsDict['eqsl-sent-color'])
        self.color_button_eqsl.setFixedWidth(120)
        self.color_button_eqsl.setFixedHeight(40)
        self.color_button_eqsl.clicked.connect(self.select_eqsl_color)
        self.color_button_layer=QHBoxLayout()
        self.color_button_layer.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.color_button_layer.addWidget(self.color_label_eqsl)
        self.color_button_layer.addWidget(self.color_button_eqsl)
        self.eqsl_lay.addLayout(self.color_button_layer)
        self.eqsl_lay.addLayout(self.eqsl_activate)

        # Create CLub log layer
        self.clublog_lay = QVBoxLayout()
        self.clublog_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.clublog_login_lay = QHBoxLayout()
        self.clublog_login_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.clublog_login_label = QLabel("Login:")
        self.clublog_login_label.setFixedWidth(75)
        self.clublog_login_label.setStyleSheet(style)
        self.clublog_login_input = QLineEdit()
        self.clublog_login_input.setFixedWidth(200)
        self.clublog_login_input.setStyleSheet(formstyle)
        # set in login lay
        self.clublog_login_lay.addWidget(self.clublog_login_label)
        self.clublog_login_lay.addWidget(self.clublog_login_input)

        # set in pass lay
        self.clublog_pass_lay = QHBoxLayout()
        self.clublog_pass_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.clublog_pass_label = QLabel("Password:")
        self.clublog_pass_label.setFixedWidth(75)
        self.clublog_pass_label.setStyleSheet(style)
        self.clublog_pass_input = QLineEdit()
        self.clublog_pass_input.setFixedWidth(250)
        #self.clublog_pass_input.setFixedHeight(35)
        self.clublog_pass_input.setStyleSheet(formstyle)
        self.clublog_pass_lay.addWidget(self.clublog_pass_label)
        self.clublog_pass_lay.addWidget(self.clublog_pass_input)

        # set in chekbox Sync
        self.clublog_sync_chekbox = QHBoxLayout()
        self.clublog_sync = QCheckBox("Auto sent to ClubLog after QSO")
        self.clublog_sync.setStyleSheet(style)
        self.clublog_sync_chekbox.addWidget(self.clublog_sync)

        self.clublog_label = QLabel("ClubLog service")
        self.clublog_label.setStyleSheet(self.style_headers)
        spacer = QFrame()
        spacer.setFrameShape(QFrame.Shape.HLine)
        spacer.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        spacer.setContentsMargins(1, 5, 1, 10)
        spacer.setLineWidth(1)
        self.clublog_lay.addWidget(spacer)
        self.clublog_lay.addWidget(self.clublog_label)
        self.clublog_lay.addSpacing(10)
        self.clublog_lay.addLayout(self.clublog_login_lay)
        self.clublog_lay.addLayout(self.clublog_pass_lay)
        self.clublog_lay.addLayout(self.clublog_sync_chekbox)

        # Create qrz.com lay
        self.qrz_com_lay = QVBoxLayout()
        self.qrz_com_lay = QVBoxLayout()
        self.qrz_com_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.qrz_com_login_lay = QHBoxLayout()
        self.qrz_com_login_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.qrz_com_login_label = QLabel("Login:")
        self.qrz_com_login_label.setFixedWidth(75)
        self.qrz_com_login_label.setStyleSheet(style)
        self.qrz_com_login_input = QLineEdit()
        self.qrz_com_login_input.setFixedWidth(200)
        self.qrz_com_login_input.setStyleSheet(formstyle)
        # set in login lay
        self.qrz_com_login_lay.addWidget(self.qrz_com_login_label)
        self.qrz_com_login_lay.addWidget(self.qrz_com_login_input)

        # set in pass lay
        self.qrz_com_pass_lay = QHBoxLayout()
        self.qrz_com_pass_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.qrz_com_pass_label = QLabel("Password:")
        self.qrz_com_pass_label.setFixedWidth(75)
        self.qrz_com_pass_label.setStyleSheet(style)
        self.qrz_com_pass_input = QLineEdit()
        self.qrz_com_pass_input.setFixedWidth(250)
        # self.clublog_pass_input.setFixedHeight(35)
        self.qrz_com_pass_input.setStyleSheet(formstyle)
        self.qrz_com_pass_lay.addWidget(self.qrz_com_pass_label)
        self.qrz_com_pass_lay.addWidget(self.qrz_com_pass_input)


        # set in chekbox Sync
        self.qrz_com_sync_chekbox = QHBoxLayout()
        self.qrz_com_sync = QCheckBox("Use QRZ.com")
        self.qrz_com_sync.setStyleSheet(style)
        self.qrz_com_sync_chekbox.addWidget(self.qrz_com_sync)

        self.qrz_com_label = QLabel("QRZ.com service")
        self.qrz_com_label.setStyleSheet(self.style_headers)
        spacer = QFrame()
        spacer.setFrameShape(QFrame.Shape.HLine)
        spacer.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        spacer.setContentsMargins(1,5,1,10)
        spacer.setLineWidth(1)
        self.qrz_com_lay.addWidget(spacer)
        self.qrz_com_lay.addWidget(self.qrz_com_label)
        self.qrz_com_lay.addSpacing(10)
        self.qrz_com_lay.addLayout(self.qrz_com_login_lay)
        self.qrz_com_lay.addLayout(self.qrz_com_pass_lay)
        self.qrz_com_lay.addLayout(self.qrz_com_sync_chekbox)

        self.service_tab.addLayout(self.eqsl_lay)
        self.service_tab.addLayout(self.clublog_lay)
        self.service_tab.addLayout(self.qrz_com_lay)

        self.service_widget.setLayout(self.service_tab)

        # Create country_tab
        self.country_tab = QVBoxLayout()
        self.country_table = QTableWidget()
        self.country_table.setStyleSheet(formstyle)
        self.country_table.setColumnCount(4)
        self.country_table.setHorizontalHeaderLabels(['Country', 'Prefixes', 'ITU', 'CQ-zone'])
        self.country_table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.country_table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.country_table.customContextMenuRequested.connect(self.context_country)
        self.pb_add_country = QPushButton()
        self.pb_add_country.setStyleSheet(style)
        self.pb_add_country.setFixedWidth(100)
        self.pb_add_country.clicked.connect(self.add_country_row)
        self.pb_add_country.setText('Add country')

        self.country_found_label = QLabel()
        self.country_found_label.setStyleSheet(style)
        self.country_found_label.setFixedWidth(50)
        self.country_found_label.setText("Country:")
        self.country_found = QLineEdit()
        self.country_found.setStyleSheet(formstyle)
        self.country_found.setFixedWidth(100)
        self.country_found.setFixedHeight(25)
        self.country_found.returnPressed.connect(self.search_country)

        self.country_lay = QHBoxLayout()
        self.country_lay.addWidget(self.country_found_label)
        self.country_lay.addWidget(self.country_found)
        self.country_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.pfx_found_label = QLabel()
        self.pfx_found_label.setFixedWidth(20)
        self.pfx_found_label.setStyleSheet(style)
        self.pfx_found_label.setText("Pfx:")

        self.pfx_found = QLineEdit()
        self.pfx_found.setStyleSheet(formstyle)
        self.pfx_found.setFixedWidth(100)
        self.pfx_found.setFixedHeight(25)
        self.pfx_found.returnPressed.connect(self.search_country)

        self.pfx_lay = QHBoxLayout()

        self.pfx_lay.addWidget(self.pfx_found_label)
        self.pfx_lay.addWidget(self.pfx_found)
        self.pfx_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.search_go_bt = QPushButton()
        self.search_go_bt.setStyleSheet(style)
        self.search_go_bt.setText('Search')
        self.search_go_bt.clicked.connect(self.search_country)


        self.country_found_lay = QHBoxLayout()
        self.country_found_lay.addLayout(self.country_lay)
        self.country_found_lay.addLayout(self.pfx_lay)
        self.country_found_lay.addWidget(self.search_go_bt)

        self.country_tab.addLayout(self.country_found_lay)
        self.country_tab.addWidget(self.country_table)
        self.country_tab.addWidget(self.pb_add_country)
        self.country_list_edit.setLayout(self.country_tab)



    # button panel
        self.button_panel = QHBoxLayout()
        button_style = "font: 12px;"
        self.button_save = QPushButton("Save and Exit")
        self.button_save.setStyleSheet(button_style)
        self.button_save.clicked.connect(self.save_and_exit_button)
        self.button_apply = QPushButton("Apply")
        self.button_apply.setStyleSheet(button_style)
        self.button_apply.clicked.connect(self.apply_button)
        self.button_cancel = QPushButton("Cancel")
        self.button_cancel.setStyleSheet(button_style)
        self.button_cancel.clicked.connect(self.cancel_button)
        self.button_cancel.setFixedWidth(60)
        self.button_panel.addWidget(self.button_cancel)
        self.button_panel.addWidget(self.button_apply)
        self.button_panel.addWidget(self.button_save)


        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.tab)
        self.mainLayout.addLayout(self.button_panel)
        #self.mainLayout.addWidget(self.tab)
        self.setLayout(self.mainLayout)

    def clear_base_qso(self):
        confirm_dialog = QMessageBox.question(self, "WARNING",
                                              "<p style='color: red; font-weight: bold'>DELETE all QSO from base</p>Are you shure?",
                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if confirm_dialog == QMessageBox.StandardButton.Yes:
            delete_result = self.db_sql.delete_all_qso()
            self.logWindow.refresh_data()
            print(f"Delete {delete_result}")


    def context_country(self, point):
        context_country = QMenu()
        #print(self.country_table.currentRow())
        index_row = self.country_table.currentRow()
        #if self.country_table.itemAt(point):
        delete_country = QAction("Delete country", context_country)
        delete_country.triggered.connect(lambda: self.country_del(index_row))
        context_country.addAction(delete_country)
        context_country.exec_(self.country_table.mapToGlobal(point))

    def country_del(self, index_row):
        #print("delete country", index_row)
        self.country_table.removeRow(index_row)

    def add_country_row(self):
        self.country_table.insertRow(self.country_table.rowCount())
        #self.fill_country()
        self.country_table.scrollToBottom()

    def fill_country(self):
        with open(Path(__file__).parent/self.settingsDict['country-file'], 'r') as f:
            country_dict = json.load(f)
        self.country_table.setRowCount(0)


        for country in country_dict:

            prefix_string = ''
            i = 0
            for prefix in country_dict[country]['prefix']:
                prefix_string += prefix
                if i != len(country_dict[country]['prefix']) - 1 :
                    prefix_string += ','
                i += 1

            self.country_table.insertRow(0)
            self.country_table.setItem(0, 0, QTableWidgetItem(country))
            self.country_table.setItem(0, 1, QTableWidgetItem(prefix_string))
            self.country_table.setItem(0, 2, QTableWidgetItem(country_dict[country]['itu']))
            self.country_table.setItem(0, 3, QTableWidgetItem(country_dict[country]['cq-zone']))

    def select_eqsl_color(self):
        color_eqsl = QColorDialog.getColor(initial=QColor(self.color_button_eqsl.text()), parent=None,
                                      title="Select color for sent eQSL")

        if color_eqsl.isValid():
            # self.back_color_input.setText()
            self.color_button_eqsl.setStyleSheet("background:" + color_eqsl.name() + ";")
            self.color_button_eqsl.setText(color_eqsl.name())
            self.color_button_eqsl.autoFillBackground()

    def initData (self):
        #init data in general tab
        self.call_input.setText(self.settingsDict["my-call"])
        if self.settingsDict['border_wnd'] == "enable":
            self.window_border.setChecked(True)
        #self.text_color_input.setText(self.settingsDict['color'])
        #self.form_color_input.setText(self.settingsDict['form-background'])
        #self.back_color_input.setText(self.settingsDict['background-color'])
        #init data in cluster tab
        self.cluster_host_input.setText(self.settingsDict['telnet-host'])
        self.cluster_port_input.setText(self.settingsDict['telnet-port'])
        if self.settingsDict['filter_by_band'] == 'enable':
            self.cluster_filter_band_combo.setChecked(True)
        self.cluster_filter_band_input.setText(self.settingsDict['list-by-band'])
        if self.settingsDict['filter-by-prefix'] == 'enable':
            self.cluster_filter_spot_combo.setChecked(True)
        self.cluster_filter_spot_input.setText(self.settingsDict['filter-prefix'])
        if self.settingsDict['filter-by-prefix-spotter'] == 'enable':
            self.cluster_filter_spotter_combo.setChecked(True)
        self.cluster_filter_spotter_input.setText(self.settingsDict['filter-prefix-spotter'])
        self.cluster_start_calibrate_button.clicked.connect(self.start_calibrate_cluster)

        self.db_login.setText(self.settingsDict['db-user'])
        self.db_pass.setText(self.settingsDict['db-pass'])
        self.db_name.setText(self.settingsDict['db-name'])
        self.db_host.setText(self.settingsDict['db-host'])

        #init data in tci tab
        if self.settingsDict['tci'] == 'enable':
            self.tci_enable_combo.setChecked(True)
        host = self.settingsDict['tci-server'].replace("ws://", '')
        self.tci_host_input.setText(host)
        self.tci_port_input.setText(self.settingsDict['tci-port'])
        if self.settingsDict['rs-from-tci'] == "True":
            self.tci_auto_rs_checkbox.setChecked(True)



        # Init data Rigctl
        if self.settingsDict['rigctl-enabled'] == "enable":
            self.rigctl_enable_combo.setChecked(True)
        self.rigctl_host_input.setText(self.settingsDict['rigctl-uri'])
        self.rigctl_port_input.setText(self.settingsDict['rigctl-port-rx1'])
        self.rigctl_port_input_rx2.setText(self.settingsDict['rigctl-port-rx2'])


        # init data eQSL
        self.eqsl_login.setText(self.settingsDict['eqsl_user'])
        self.eqsl_password.setText(self.settingsDict['eqsl_password'])
        if self.settingsDict['eqsl'] == 'enable':
            self.eqsl_chekBox.setChecked(True)
        if self.settingsDict['mode-swl'] == 'enable':
            self.swl_chekbox.setChecked(True)

        # Init data clublog
        self.clublog_login_input.setText(self.settingsDict['email-clublog'])
        self.clublog_pass_input.setText(self.settingsDict['pass-clublog'])
        if self.settingsDict['clublog'] == 'enable':
            self.clublog_sync.setChecked(True)
        else:
            self.clublog_sync.setChecked(False)

        # intt data clublog
        self.qrz_com_login_input.setText(self.settingsDict['qrz-com-username'])
        self.qrz_com_pass_input.setText(self.settingsDict['qrz-com-password'])
        if self.settingsDict['qrz-com-enable'] == 'enable':
            self.qrz_com_sync.setChecked(True)
        else:
            self.qrz_com_sync.setChecked(False)


        # Init CAT tab
        if self.settingsDict['cat'] == 'enable':
            self.cat_enable.setChecked(True)
        else:
            self.cat_enable.setChecked(False)
        self.port_cat_input.setText(self.settingsDict['cat-port'])
        cat_baud_index = self.baud_cat_combo.findText(self.settingsDict['speed-cat'])
        self.baud_cat_combo.setCurrentIndex(cat_baud_index)
        cat_parity_index = self.parity_cat_combo.findText(self.settingsDict['cat-parity'])
        self.parity_cat_combo.setCurrentIndex(cat_parity_index)
        cat_data_index = self.data_cat_combo.findText(self.settingsDict['cat-data'])
        self.data_cat_combo.setCurrentIndex(cat_data_index)
        cat_stop_index = self.stop_cat_combo.findText(self.settingsDict['cat-stop-bit'])
        self.stop_cat_combo.setCurrentIndex(cat_stop_index)
        cat_protocol_index = self.protocol_cat_combo.findText(self.settingsDict['cat-protocol'])
        self.protocol_cat_combo.setCurrentIndex(cat_protocol_index)
        # Init country_data
        self.fill_country()

    def closeEvent(self, e):
        #print("Close menu", e)
        self.close()

    def search_country(self):
        country = self.country_found.text().strip().lower()
        pfx = self.pfx_found.text().strip().lower()
        print(pfx)

        for i in range(self.country_table.rowCount()):
            #print(country, self.country_table.item(i, 0).text())
            if self.country_table.item(i,0).text().lower() == country:
                self.country_table.scrollToItem(self.country_table.item(i,0))
                self.country_table.item(i, 0).setBackground(
                            QColor(self.settingsDict["eqsl-sent-color"]))

            if pfx != '':
                pfx_list = self.country_table.item(i, 1).text().lower().split(",")
                for pfx_elem in pfx_list:
                   if pfx_elem == pfx:
                        self.country_table.scrollToItem(self.country_table.item(i, 1))
                        self.country_table.item(i, 1).setBackground(
                            QColor(self.settingsDict["eqsl-sent-color"]))


    def import_adi(self):
        fileimport = QFileDialog()
        #options = QFileDialog.options()
        home_page = '~'
        fname = fileimport.getOpenFileName(self, 'Import adi file', home_page, "*.adi | *.ADI")[0]
        if fname:
            self.allCollumn = ['QSO_DATE', 'TIME_ON', 'BAND', 'CALL', 'FREQ', 'MODE', 'RST_RCVD', 'RST_SENT', 'NAME',
                               'QTH', 'COMMENT', 'ITUZ', 'TIME_OFF', 'EQSL_QSL_RCVD', 'OPERATOR', 'EQSL_QSL_SENT',
                               'CLUBLOG_QSO_UPLOAD_STATUS', 'STATION_CALLSIGN']
            try:
                good_qso_count = 0
                double_qso = []
                bad_qso = []
                allRecords = parse.getAllRecord(self.allCollumn, fname, key="import")
                print(f"All records {allRecords}")
                self.logWindow.load_bar.show()
                all_records_count = len(allRecords)
                for i, qso_in_file in enumerate(allRecords):
                    if len(qso_in_file["TIME_ON"].strip()) < 6:
                        while len(qso_in_file["TIME_ON"]) < 6:
                            qso_in_file["TIME_ON"] += "0"
                    if len(qso_in_file["TIME_ON"].strip()) > 6:
                        qso_in_file["TIME_ON"] = qso_in_file["TIME_ON"][:6]
                    if len(qso_in_file["QSO_DATE"].strip()) != 8 or len(qso_in_file["TIME_ON"].strip()) != 6:
                        bad_qso.append(qso_in_file)
                        continue
                    double_counter = len(double_qso)
                    search_qso_in_base = main.Db(self.settingsDict).search_qso_by_full_data(
                        str(qso_in_file["CALL"]),
                        str(qso_in_file["QSO_DATE"]),
                        str(qso_in_file["TIME_ON"]),
                        str(qso_in_file["BAND"]),
                        str(qso_in_file["MODE"])
                    )
                    if search_qso_in_base:
                        double_qso.append(qso_in_file)
                    if len(double_qso) > double_counter:
                        continue
                    good_qso_count += 1
                    main.Db(self.settingsDict).record_qso_to_base(qso_in_file, mode="import")
                    self.logWindow.load_bar.setValue(int(i * 100 / all_records_count))
                if double_qso is not None:
                    main.Adi_file(self.settingsDict["APP_VERSION"],
                                  self.settingsDict).record_dict_qso(double_qso, self.allCollumn, name_file="double_adi.adi")
                if bad_qso is not None:
                    main.Adi_file(self.settingsDict["APP_VERSION"],
                                  self.settingsDict).record_dict_qso(bad_qso, self.allCollumn, name_file="bad_adi.adi")
                self.logWindow.refresh_data()
                message = f"Added QSO: {good_qso_count} \n"
                message += f"Bad QSO: {len(bad_qso)} Incorect QSO_DATE or TIME_ON \n The bad records save in /home/linlog/bad_adi.adi" if bad_qso != [] else ""
                message += f"\nDouble QSO: {len(double_qso)} \n The double records save in /home/linlog/double_adi.adi" if double_qso != [] else ""
                std.std.message(self, message, "Import")
            except Exception:
                std.std.message(self, traceback.format_exc(), "STOP!")

    def export_adi(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export adi", "",
                                                  "Adi (*.adi)")
        if file_name:

            allRecords = main.Db(self.settingsDict).get_all_records()
            main.Adi_file(self.app_env.appVersion(), self.settingsDict).record_dict_qso(
                list_data=allRecords,
                fields_list=self.table_columns,
                name_file=file_name+'.adi')
            std.std.message(self, f"Export to\n{file_name}\n completed", "Export complited")

    def export_adi_clublog(self):

        try:
            clublog = internetworker.Clublog(settingsDict=self.settingsDict)
            response = clublog.export_file("log.adi")
            if response.status_code == 200:
                print("response for Club log:_>", response, response.headers)
                std.std.message(self, "Club log: "+response.content.decode(self.settingsDict['encodeStandart']), "Ok")
            elif response.status_code == 403:
                print("response for Club log:_>", response,  response.content)
                std.std.message(self, "Club log: "+response.content.decode(self.settingsDict['encodeStandart'])+"\n", "ERROR")
        except Exception:
            std.std.message(self, "Check internet connection\n",
                            "ERROR Club log")

    def start_calibrate_cluster(self):
       # print("start_calibrate_cluster:_>", self.settingsDict)
        self.telnetCluster.stop_cluster()
        self.cluster = cluster_in_Thread (self.cluster_host_input.text().strip(),
                                          self.cluster_port_input.text().strip(),
                                          self.call_input.text().strip(),
                                          settingsDict=self.settingsDict, parent_window=self)
        self.cluster.start()

    def refresh_interface(self):
        self.update_color_schemes()

    def text_color_select(self):
        color = QColorDialog.getColor(initial=QColor(self.text_color_input.text()), parent=None, title="Select color for text in window")

        if color.isValid():
            self.text_color_input.setText(color.name())
            self.text_color_input.setStyleSheet("background:" + color.name() + ";")
            self.text_color_input.autoFillBackground()

    def form_color_select(self):
        color = QColorDialog.getColor(initial=QColor(self.form_color_input.text()), parent=None, title="Select color for text in tables")

        if color.isValid():
            self.form_color_input.setText(color.name())
            self.form_color_input.setStyleSheet("background:" + color.name() + ";")
            self.form_color_input.autoFillBackground()

    def form_text_color_select(self):
        color = QColorDialog.getColor(initial=QColor(self.text_form_color_button.text()), parent=None, title="Select color for text in tables")

        if color.isValid():
            self.text_form_color_button.setText(color.name())
            self.text_form_color_button.setStyleSheet("background:" + color.name() + ";")
            self.text_form_color_button.autoFillBackground()
    #self.back_color_input.clicked.connect(self.text_color_select)

    def back_color_select(self):
        #self.dlg.show()
        color = QColorDialog.getColor(initial=QColor(self.back_color_input.text()), parent=None, title="Select color for background color")

        if color.isValid():
            #self.back_color_input.setText()
            self.back_color_input.setStyleSheet("background:"+color.name()+";")
            self.back_color_input.setText(color.name())
            self.back_color_input.autoFillBackground()

    def update_color_schemes(self):
        style = "QWidget{background-color:" + self.settingsDict['background-color'] + "; color:" + \
                self.settingsDict['color'] + ";}"



        self.setStyleSheet(style)

    def store_new_settingsDict(self):

        # SAve general tab
        call = self.settingsDict['my-call']
        self.settingsDict['my-call'] = self.call_input.text()
        self.settingsDict['background-color'] = self.back_color_input.text()
        self.settingsDict['color'] = self.text_color_input.text()
        self.settingsDict['form-background'] = self.form_color_input.text()
        self.settingsDict['color-table'] = self.text_form_color_button.text()
        self.settingsDict['telnet-host'] = self.cluster_host_input.text().strip()
        self.settingsDict['telnet-port'] = self.cluster_port_input.text().strip()
        self.settingsDict['list-by-band'] = self.cluster_filter_band_input.text()
        self.settingsDict['filter-prefix'] = self.cluster_filter_spot_input.text()
        self.settingsDict['filter-prefix-spotter'] = self.cluster_filter_spotter_input.text()
        if self.cluster_combo_call.currentText() != '':
            self.settingsDict['telnet-call-position'] = self.cluster_combo_call.currentText().split(":")[0]
        if self.cluster_combo_freq.currentText() != '':
            self.settingsDict['telnet-freq-position'] = self.cluster_combo_freq.currentText().split(":")[0]
        self.settingsDict['db-user'] = self.db_login.text().strip()
        self.settingsDict['db-pass'] = self.db_pass.text().strip()
        self.settingsDict['db-name'] = self.db_name.text().strip()
        self.settingsDict['db-host'] = self.db_host.text().strip()
        if self.window_border.isChecked():
            self.settingsDict['border_wnd'] = "enable"
        else:
            self.settingsDict['border_wnd'] = "disable"

        # Save eQSL data
        self.settingsDict['eqsl_user'] = self.eqsl_login.text()
        self.settingsDict['eqsl_password'] = self.eqsl_password.text()
        self.settingsDict['eqsl-sent-color'] = self.color_button_eqsl.text()
        if self.eqsl_chekBox.isChecked():
            self.settingsDict['eqsl'] = 'enable'
        else:
            self.settingsDict['eqsl'] = 'disable'
        if self.swl_chekbox.isChecked():
            self.settingsDict['mode-swl'] = 'enable'

        else:
            self.settingsDict['mode-swl'] = "disable"

        # Save Clublog data
        self.settingsDict['email-clublog'] = self.clublog_login_input.text().strip()
        self.settingsDict['pass-clublog'] = self.clublog_pass_input.text().strip()
        if self.clublog_sync.isChecked():
            self.settingsDict['clublog'] = 'enable'
        else:
            self.settingsDict['clublog'] = 'disable'

        # Save qrz.com data
        self.settingsDict['qrz-com-username'] = self.qrz_com_login_input.text().strip()
        self.settingsDict['qrz-com-password'] = self.qrz_com_pass_input.text().strip()
        if self.qrz_com_sync.isChecked():
            self.settingsDict['qrz-com-enable'] = 'enable'
        else:
            self.settingsDict['qrz-com-enable'] = 'disable'


        # Save TCI
        if self.tci_enable_combo.isChecked():
            self.settingsDict['tci'] = 'enable'
        else:
            self.settingsDict['tci'] = 'disable'
        self.settingsDict['tci-server'] = "ws://" + self.tci_host_input.text().strip()
        self.settingsDict['tci-port'] = self.tci_port_input.text().strip()
        if self.tci_auto_rs_checkbox.isChecked():
            self.settingsDict['rs-from-tci'] = 'True'
        else:
            self.settingsDict['rs-from-tci'] = 'False'

        # Save Rigctl
        if self.rigctl_enable_combo.isChecked():
            self.settingsDict['rigctl-enabled'] = 'enable'
        else:
            self.settingsDict['rigctl-enabled'] = 'disable'
        self.settingsDict['rigctl-uri'] = self.rigctl_host_input.text().strip()
        self.settingsDict['rigctl-port-rx1'] = self.rigctl_port_input.text().strip()
        self.settingsDict['rigctl-port-rx2'] = self.rigctl_port_input_rx2.text().strip()


        # Save CAT
        self.settingsDict['cat-port'] = self.port_cat_input.text().strip()
        self.settingsDict['speed-cat'] = self.baud_cat_combo.currentText()
        self.settingsDict['cat-parity'] = self.parity_cat_combo.currentText()
        self.settingsDict['cat-data'] = self.data_cat_combo.currentText()
        self.settingsDict['cat-stop-bit'] = self.stop_cat_combo.currentText()
        self.settingsDict['cat-protocol'] = self.protocol_cat_combo.currentText()
        if self.cat_enable.isChecked():
            self.settingsDict['cat'] = 'enable'
        else:
            self.settingsDict['cat'] = 'disable'

        # Save country list
        self.update_country_list()

        # Save cluster
        cluster_change_flag = 0
        if self.cluster_filter_band_combo.isChecked():
            if self.settingsDict['filter_by_band'] != "enable":
                self.settingsDict['filter_by_band'] = "enable"
                cluster_change_flag = 1
        else:
            if self.settingsDict['filter_by_band'] != "disable":
                self.settingsDict['filter_by_band'] = "disable"
                cluster_change_flag = 1

        if self.cluster_filter_spot_combo.isChecked():
            if self.settingsDict['filter-by-prefix'] != "enable":
                self.settingsDict['filter-by-prefix'] = "enable"
                cluster_change_flag = 1
        else:
            if self.settingsDict['filter-by-prefix'] != "disable":
                self.settingsDict['filter-by-prefix'] = "disable"
                cluster_change_flag = 1

        if self.cluster_filter_spotter_combo.isChecked():
            if self.settingsDict['filter-by-prefix-spotter'] != "enable":
                self.settingsDict['filter-by-prefix-spotter'] = "enable"
                cluster_change_flag = 1
        else:
            if self.settingsDict['filter-by-prefix-spotter'] != "disable":
                self.settingsDict['filter-by-prefix-spotter'] = "disable"
                cluster_change_flag = 1


        return cluster_change_flag

    def update_country_list(self):
        #self.country_table.

        data_object = {}
        for i in range(self.country_table.rowCount()):
            try:
                if self.country_table.item(i,0).text() != '' and \
                        self.country_table.item(i, 1).text() != '':
                    country = self.country_table.item(i,0).text()
                    pfx_list_dark = self.country_table.item(i,1).text().split(',')
                    pfx_list_clean = []
                    for elem in pfx_list_dark:
                        elem = elem.strip().upper()
                        pfx_list_clean.append(elem)
                    itu = self.country_table.item(i, 2).text()
                    cq_zone = self.country_table.item(i, 3).text()
                    data_object.update({country: {'prefix': pfx_list_clean,'itu': itu,'cq-zone': cq_zone }})
            except Exception:
                print("Exception in update country list str: 1149")
            #print(data_object)

        with open(Path(__file__).parent/self.settingsDict['country-file'], 'w') as f:
            json.dump(data_object, f)

    def apply_button(self):

        cluster_change_flag = self.store_new_settingsDict()   # save all lines from menu window \
                                                                # to dictionary settingsDict
        if self.settingsDict['tci'] == 'enable':
            self.tci_rcvr.stop_tci()
            self.tci_rcvr.start_tci(self.settingsDict['tci-server'], self.settingsDict['tci-port'])
            self.tci_sender.web_socket_init(f"{self.settingsDict['tci-server']}:{self.settingsDict['tci-port']}")
        else:
            self.tci_rcvr.stop_tci()

        if self.settingsDict['rigctl-enabled'] == 'enable':
            self.logForm.rigctl_stop()
            self.logForm.rigctl_init_base_data()
        else:
            self.logForm.rigctl_stop()

        self.logForm.refresh_interface()
        self.logSearch.refresh_interface()
        self.logWindow.refresh_interface()
        self.internetSearch.refresh_interface()
        self.telnetCluster.refresh_interface()
        self.refresh_interface()
        if cluster_change_flag == 1:
            self.telnetCluster.stop_cluster()
            self.telnetCluster.start_cluster()

    def save_and_exit_button(self):

        cluster_change_flag = self.store_new_settingsDict()
        self.logForm.refresh_interface()
        filename = 'settings.cfg'
        with open(Path(__file__).parent/filename, 'r') as f:
            old_data = f.readlines()
        for index, line in enumerate(old_data):
            key_from_line = line.split('=')[0]
            #print ("key_from_line:",key_from_line)
            for key in self.settingsDict:

                if key_from_line == key:
                    #print("key",key , "line", line)
                    old_data[index] = key+"="+self.settingsDict[key]+"\n"
        with open(Path(__file__).parent/filename, 'w') as f:
            f.writelines(old_data)
        #print ("Save_and_Exit_button: ", old_data)
        self.close()

    def cancel_button(self):
        self.close()

class cluster_in_Thread(QThread):
    def __init__(self, host, port, call, parent_window, settingsDict, parent=None):
        super().__init__()
        self.settingsDict = settingsDict
        self.host = host
        self.port = port
        self.call =call
        self.parent_window = parent_window
        # self.run()

    def run(self):

        while 1:
            try:
                telnetObj = telnetlib.Telnet(self.host, self.port)
                break
            except:
                time.sleep(3)
                continue

        lastRow = 0
        message = (self.call + "\n").encode('ascii')
        telnetObj.write(message)
        message2 = (self.call + "\n").encode('ascii')
        telnetObj.write(message2)
        splitString = []
        cleanList = []
        output_data = ""
        i = 0
        #print('Starting Telnet cluster:', self.host, ':', self.port, '\nCall:', self.call, '\n\n')
        while 1:
            try:
                output_data = telnetObj.read_some()
            except:
                continue

            if output_data != '':

                    if output_data[0:2].decode(self.settingsDict['encodeStandart']) == "DX":
                        splitString = output_data.decode(self.settingsDict['encodeStandart']).split(' ')
                        count_chars = len(splitString)
                        for i in range(count_chars):
                            if splitString[i] != '':
                                cleanList.append(splitString[i])
                        break
            time.sleep(0.3)
        ##########

        i = 0
        for value in cleanList:
            self.parent_window.cluster_combo_call.addItems([str(i) + ":" + value])
            self.parent_window.cluster_combo_freq.addItems([str(i) + ":" + value])
            i += 1

        self.parent_window.cluster_combo_call.setCurrentIndex(int(self.settingsDict['telnet-call-position']))
        self.parent_window.cluster_combo_freq.setCurrentIndex(int(self.settingsDict['telnet-freq-position']))
        self.parent_window.line_text.setText(' '.join(cleanList))
        self.parent_window.telnetCluster.start_cluster()

        self.currentThread().exit()
        self.currentThread().wait()






