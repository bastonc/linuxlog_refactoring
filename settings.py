import logging
import socket
import time
from pathlib import Path

import main
import internetworker
import config_store
import traceback
import parse
import shutil
from services.qso_repository import QsoRepository
import std
import json
from qth_locator import normalize_locator
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

THEMES = {
    "Dark": {
        "background-color": "#08131f",
        "color": "#c0bfbc",
        "form-background": "#102033",
        "color-table": "#d7e3f0",
        "solid-color": "#2b4a66",
    },
    "Light": {
        "background-color": "#f2f2f2",
        "color": "#1f1f1f",
        "form-background": "#ffffff",
        "color-table": "#1f1f1f",
        "solid-color": "#9aa0a6",
    },
    "Blue": {
        "background-color": "#0b1f3a",
        "color": "#d8e6ff",
        "form-background": "#122b4f",
        "color-table": "#eaf1ff",
        "solid-color": "#3a6ea5",
    },
    "Green": {
        "background-color": "#0f2418",
        "color": "#d9f0df",
        "form-background": "#173525",
        "color-table": "#eaf7ed",
        "solid-color": "#3f7f55",
    },
}

logger = logging.getLogger(__name__)


class Menu (QWidget):
    def __init__(self, db, app_env, settingsDict, telnetCluster, logForm, logSearch,
                 logWindow, internetSearch, tci_recv, tci_sndr, table_columns, parent=None):
        super(Menu, self).__init__(parent)
        self.db_sql = db
        self.settingsDict = settingsDict
        self._clublog_workers = {}
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

        self.tci_tab = QWidget()
        self.cat_tab = QWidget()
        self.io_tab = QWidget()
        self.service_widget = QWidget()
        self.country_list_edit = QWidget()
    #
        self.tab.addTab(self.general_tab, "General")
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
        self.theme_label = QLabel("Theme")
        self.theme_label.setStyleSheet(self.label_style)
        self.themes_path = Path(__file__).parent / "themes.json"
        self.custom_themes = {}
        try:
            if self.themes_path.exists():
                with self.themes_path.open("r", encoding="utf-8") as theme_file:
                    loaded = json.load(theme_file)
                if isinstance(loaded, dict):
                    self.custom_themes = loaded
        except Exception:
            self.custom_themes = {}
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()) + sorted(self.custom_themes.keys()))
        current_theme = self.settingsDict.get("theme", "Dark")
        if current_theme not in THEMES:
            current_theme = "Dark"
        self.theme_combo.setCurrentText(current_theme)
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
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

        self.qth_locator_label = QLabel("My QTH locator:")
        self.qth_locator_label.setFixedWidth(100)
        self.qth_locator_input = QLineEdit()
        self.qth_locator_input.setFixedWidth(100)
        self.qth_locator_input.setMaxLength(8)
        self.qth_locator_input.setPlaceholderText("e.g. KO50AA")
        self.qth_locator_input.setStyleSheet(formstyle)
        self.qth_locator_input.setToolTip(
            "Your Maidenhead grid locator (2, 4, 6 or 8 characters)"
        )

        self.qth_locator_lay = QHBoxLayout()
        self.qth_locator_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qth_locator_lay.addWidget(self.qth_locator_label)
        self.qth_locator_lay.addWidget(self.qth_locator_input)

        # setup all elements to vertical lay
        self.call_lay = QHBoxLayout()
        self.call_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.call_lay.addWidget(self.call_label)
        self.call_lay.addWidget(self.call_input)
        self.call_lay.addWidget(self.swl_chekbox)
        self.call_lay.addWidget(self.clear_base_button)
        self.general_tab.layout.addLayout(self.call_lay)
        self.general_tab.layout.addLayout(self.qth_locator_lay)


        self.general_tab.layout.addSpacing(20)

        #self.general_tab.layout.addWidget(self.swl_chekbox)

        self.horizontal_lay = QHBoxLayout()
        self.color_lay = QVBoxLayout()
        self.color_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.color_lay.addWidget(self.theme_label)
        self.color_lay.addWidget(self.theme_combo)
        self.theme_buttons_lay = QHBoxLayout()
        self.save_theme_button = QPushButton("Save theme")
        self.save_theme_button.clicked.connect(self.save_custom_theme)
        self.export_theme_button = QPushButton("Export")
        self.export_theme_button.clicked.connect(self.export_custom_theme)
        self.import_theme_button = QPushButton("Import")
        self.import_theme_button.clicked.connect(self.import_custom_theme)
        self.theme_buttons_lay.addWidget(self.save_theme_button)
        self.theme_buttons_lay.addWidget(self.export_theme_button)
        self.theme_buttons_lay.addWidget(self.import_theme_button)
        self.color_lay.addLayout(self.theme_buttons_lay)
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
        #self.tci_tab.layout.addWidget(Separador)
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
            logger.debug(f"Delete {delete_result}")


    def context_country(self, point):
        context_country = QMenu()
        #logger.debug(self.country_table.currentRow())
        index_row = self.country_table.currentRow()
        #if self.country_table.itemAt(point):
        delete_country = QAction("Delete country", context_country)
        delete_country.triggered.connect(lambda: self.country_del(index_row))
        context_country.addAction(delete_country)
        context_country.exec_(self.country_table.mapToGlobal(point))

    def country_del(self, index_row):
        #logger.debug("delete country", index_row)
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
        self.qth_locator_input.setText(
            self.settingsDict.get("my-qth-locator", "")
        )
        if self.settingsDict['border_wnd'] == "enable":
            self.window_border.setChecked(True)
        #self.text_color_input.setText(self.settingsDict['color'])
        #self.form_color_input.setText(self.settingsDict['form-background'])
        #self.back_color_input.setText(self.settingsDict['background-color'])
        # Cluster settings are now edited directly in the cluster window.

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
        calibration_thread = getattr(self, "cluster", None)
        if calibration_thread is not None and calibration_thread.isRunning():
            calibration_thread.stop()
            calibration_thread.wait(4000)
        e.accept()

    def search_country(self):
        country = self.country_found.text().strip().lower()
        pfx = self.pfx_found.text().strip().lower()
        logger.debug(pfx)

        for i in range(self.country_table.rowCount()):
            #logger.debug(country, self.country_table.item(i, 0).text())
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
                self.logWindow.load_bar.show()
                all_records_count = len(allRecords)
                db_importer = QsoRepository(self.settingsDict)
                for i, qso_in_file in enumerate(allRecords):
                    qso_date = parse.normalize_adi_date(qso_in_file.get("QSO_DATE"))
                    time_on = parse.normalize_adi_time(qso_in_file.get("TIME_ON"))
                    time_off = parse.normalize_adi_time(qso_in_file.get("TIME_OFF"))
                    if not qso_date or not time_on:
                        bad_qso.append(qso_in_file)
                        continue
                    qso_in_file["QSO_DATE"] = qso_date
                    qso_in_file["TIME_ON"] = time_on
                    qso_in_file["TIME_OFF"] = time_off or time_on
                    search_qso_in_base = db_importer.search_qso_by_full_data(
                        str(qso_in_file.get("CALL") or ""),
                        qso_date,
                        time_on,
                        str(qso_in_file.get("BAND") or ""),
                        str(qso_in_file.get("MODE") or ""),
                    )
                    if search_qso_in_base:
                        double_qso.append(qso_in_file)
                        continue
                    try:
                        db_importer.record_qso_to_base(qso_in_file, mode="import")
                    except Exception:
                        # Keep importing the rest of the file; save this
                        # record for later inspection.
                        bad_qso.append(qso_in_file)
                        continue
                    good_qso_count += 1
                    if all_records_count:
                        self.logWindow.load_bar.setValue(
                            int(i * 100 / all_records_count)
                        )
                if double_qso is not None:
                    main.Adi_file(self.settingsDict["APP_VERSION"],
                                  self.settingsDict).record_dict_qso(double_qso, self.allCollumn, name_file="double_adi.adi")
                if bad_qso is not None:
                    main.Adi_file(self.settingsDict["APP_VERSION"],
                                  self.settingsDict).record_dict_qso(bad_qso, self.allCollumn, name_file="bad_adi.adi")
                self.logWindow.load_bar.setValue(100)
                self.logWindow.refresh_data()
                message = f"Added QSO: {good_qso_count} \n"
                message += f"Bad QSO: {len(bad_qso)} Incorrect QSO_DATE/TIME_ON or database error \n The bad records are saved in bad_adi.adi" if bad_qso != [] else ""
                message += f"\nDouble QSO: {len(double_qso)} \n The duplicate records are saved in double_adi.adi" if double_qso != [] else ""
                std.std.message(self, message, "Import")
            except Exception:
                std.std.message(self, traceback.format_exc(), "STOP!")

    def export_adi(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export adi", "",
                                                  "Adi (*.adi)")
        if file_name:
            if not file_name.lower().endswith(".adi"):
                file_name += ".adi"

            allRecords = QsoRepository(self.settingsDict).all_records()
            main.Adi_file(self.app_env.appVersion(), self.settingsDict).record_dict_qso(
                list_data=allRecords,
                fields_list=self.table_columns,
                name_file=file_name)
            std.std.message(self, f"Export to\n{file_name}\n completed", "Export complited")

    def export_adi_clublog(self):
        self.export_clublog_button.setEnabled(False)
        clublog = internetworker.Clublog(settingsDict=self.settingsDict)
        clublog.export_completed.connect(self._clublog_export_completed)
        clublog.operation_error.connect(self._clublog_export_failed)

        thread = QThread(self)
        clublog.moveToThread(thread)
        clublog.export_requested.connect(clublog.export_file_async)
        clublog.operation_finished.connect(thread.quit)
        clublog.operation_finished.connect(clublog.deleteLater)
        thread.started.connect(lambda worker=clublog: worker.export_requested.emit("log.adi"))
        thread.finished.connect(self._enable_clublog_export)
        thread.finished.connect(thread.deleteLater)
        self._clublog_workers[thread] = clublog
        thread.finished.connect(lambda thread=thread: self._clublog_workers.pop(thread, None))
        thread.start()

    @QtCore.pyqtSlot(object)
    def _clublog_export_completed(self, response):
        message = response.content.decode(self.settingsDict['encodeStandart'], errors='replace')
        if response.status_code == 200:
            std.std.message(self, "Club Log: " + message, "Export completed")
        else:
            std.std.message(self, "Club Log: " + message, "ERROR")

    @QtCore.pyqtSlot(str)
    def _clublog_export_failed(self, message):
        std.std.message(self, message, "ERROR Club Log")

    @QtCore.pyqtSlot()
    def _enable_clublog_export(self):
        self.export_clublog_button.setEnabled(True)

    def start_calibrate_cluster(self):
       # logger.debug("start_calibrate_cluster:_>", self.settingsDict)
       self.telnetCluster.stop_cluster()
       if hasattr(self, "cluster") and self.cluster.isRunning():
           self.cluster.stop()
           if not self.cluster.wait(4000):
               std.std.message(self, "Cluster calibration is still stopping", "Telnet")
               return
       self.cluster = cluster_in_Thread (self.cluster_host_input.text().strip(),
                                          self.cluster_port_input.text().strip(),
                                          self.call_input.text().strip(),
                                          settingsDict=self.settingsDict, parent_window=self)
       self.cluster.calibration_result.connect(self.apply_cluster_calibration)
       self.cluster.start()

    @QtCore.pyqtSlot(object)
    def apply_cluster_calibration(self, clean_list):
        self.cluster_combo_call.clear()
        self.cluster_combo_freq.clear()
        for index, value in enumerate(clean_list):
            option = f"{index}:{value}"
            self.cluster_combo_call.addItem(option)
            self.cluster_combo_freq.addItem(option)

        call_index = int(self.settingsDict.get('telnet-call-position', 0))
        freq_index = int(self.settingsDict.get('telnet-freq-position', 0))
        self.cluster_combo_call.setCurrentIndex(call_index)
        self.cluster_combo_freq.setCurrentIndex(freq_index)
        self.line_text.setText(' '.join(clean_list))
        self.telnetCluster.start_cluster()

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

    def apply_theme(self, theme_name):
        theme = THEMES.get(theme_name) or self.custom_themes.get(theme_name)
        if not theme:
            return
        for key, value in theme.items():
            self.settingsDict[key] = value
        self.settingsDict["theme"] = theme_name
        self.back_color_input.setStyleSheet("background:" + theme["background-color"] + "; color:" + theme["background-color"] + ";")
        self.back_color_input.setText(theme["background-color"])
        self.text_color_input.setStyleSheet("background:" + theme["color"] + "; color:" + theme["color"] + ";")
        self.text_color_input.setText(theme["color"])
        self.form_color_input.setStyleSheet("background: " + theme["form-background"] + "; color:" + theme["form-background"] + ";")
        self.form_color_input.setText(theme["form-background"])
        self.text_form_color_button.setStyleSheet("background: " + theme["color-table"] + "; color: " + theme["color-table"] + ";")
        self.text_form_color_button.setText(theme["color-table"])
        style = "QWidget{background-color:" + theme['background-color'] + "; color:" + theme['color'] + ";}"
        self.setStyleSheet(style)

    def _current_theme_colors(self):
        return {
            "background-color": self.back_color_input.text().strip(),
            "color": self.text_color_input.text().strip(),
            "form-background": self.form_color_input.text().strip(),
            "color-table": self.text_form_color_button.text().strip(),
            "solid-color": self.settingsDict.get("solid-color", "#2b4a66"),
        }

    def save_custom_theme(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Save theme", "Theme name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in THEMES:
            QMessageBox.warning(self, "Save theme", "This name is reserved for a built-in theme.")
            return
        self.custom_themes[name] = self._current_theme_colors()
        try:
            with self.themes_path.open("w", encoding="utf-8") as theme_file:
                json.dump(self.custom_themes, theme_file, ensure_ascii=False, indent=2)
        except Exception as error:
            QMessageBox.warning(self, "Save theme", str(error))
            return
        if self.theme_combo.findText(name) < 0:
            self.theme_combo.addItem(name)
        self.theme_combo.setCurrentText(name)

    def export_custom_theme(self):
        name = self.theme_combo.currentText()
        theme = THEMES.get(name) or self.custom_themes.get(name)
        if not theme:
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Export theme", name + ".json", "JSON (*.json)")
        if not file_name:
            return
        try:
            with open(file_name, "w", encoding="utf-8") as theme_file:
                json.dump({name: theme}, theme_file, ensure_ascii=False, indent=2)
        except Exception as error:
            QMessageBox.warning(self, "Export theme", str(error))

    def import_custom_theme(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import theme", "", "JSON (*.json)")
        if not file_name:
            return
        try:
            with open(file_name, "r", encoding="utf-8") as theme_file:
                loaded = json.load(theme_file)
        except Exception as error:
            QMessageBox.warning(self, "Import theme", str(error))
            return
        if not isinstance(loaded, dict):
            QMessageBox.warning(self, "Import theme", "Invalid theme file.")
            return
        # Accept either {"Name": {...}} or a bare color dictionary.
        if all(isinstance(value, str) for value in loaded.values()):
            loaded = {"Imported theme": loaded}
        for name, theme in loaded.items():
            if not isinstance(theme, dict):
                continue
            if name in THEMES:
                name = name + " (imported)"
            self.custom_themes[name] = theme
        try:
            with self.themes_path.open("w", encoding="utf-8") as theme_file:
                json.dump(self.custom_themes, theme_file, ensure_ascii=False, indent=2)
        except Exception as error:
            QMessageBox.warning(self, "Import theme", str(error))
            return
        self.theme_combo.clear()
        self.theme_combo.addItems(list(THEMES.keys()) + sorted(self.custom_themes.keys()))
        if loaded:
            self.theme_combo.setCurrentText(next(iter(loaded.keys())))

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
        self.settingsDict['my-qth-locator'] = normalize_locator(
            self.qth_locator_input.text()
        )
        self.settingsDict['background-color'] = self.back_color_input.text()
        self.settingsDict['color'] = self.text_color_input.text()
        self.settingsDict['form-background'] = self.form_color_input.text()
        self.settingsDict['color-table'] = self.text_form_color_button.text()
        self.settingsDict['theme'] = self.theme_combo.currentText()
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
        # Cluster spot filtering is now configured in the cluster window.
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
                logger.debug("Exception in update country list str: 1149")
            #logger.debug(data_object)

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
        self.logForm.refresh_qth_map_locator()
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
        self.logForm.refresh_qth_map_locator()
        config_store.update_settings(self.settingsDict)
        config_store.ensure_settings({
            'my-qth-locator': self.settingsDict.get('my-qth-locator', ''),
            'qth-map-window': self.settingsDict.get('qth-map-window', 'False'),
            'qth-map-window-left': self.settingsDict.get('qth-map-window-left', '100'),
            'qth-map-window-top': self.settingsDict.get('qth-map-window-top', '100'),
            'qth-map-window-width': self.settingsDict.get('qth-map-window-width', '900'),
            'qth-map-window-height': self.settingsDict.get('qth-map-window-height', '520'),
            'cluster-connection-enabled': self.settingsDict.get('cluster-connection-enabled', 'enable'),
            'cluster-filter-enabled': self.settingsDict.get('cluster-filter-enabled', 'disable'),
            'cluster-filter-call': self.settingsDict.get('cluster-filter-call', ''),
            'cluster-filter-band': self.settingsDict.get('cluster-filter-band', ''),
            'cluster-filter-mode': self.settingsDict.get('cluster-filter-mode', ''),
            'cluster-filter-presence': self.settingsDict.get('cluster-filter-presence', 'all'),
            'theme': self.settingsDict.get('theme', 'Dark'),
        })
        self.close()

    def cancel_button(self):
        self.close()

class cluster_in_Thread(QThread):
    calibration_result = QtCore.pyqtSignal(object)

    def __init__(self, host, port, call, parent_window, settingsDict, parent=None):
        super().__init__()
        self.settingsDict = settingsDict
        self.host = host
        self.port = port
        self.call =call
        self.parent_window = parent_window
        self._stop_requested = False
        self._socket = None

    def stop(self):
        self._stop_requested = True
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass

    def run(self):
        while not self._stop_requested:
            try:
                self._socket = socket.create_connection((self.host, int(self.port)), timeout=3)
                break
            except (OSError, ValueError, TypeError):
                for _ in range(30):
                    if self._stop_requested:
                        return
                    self.msleep(100)

        if self._stop_requested or self._socket is None:
            return

        try:
            self._socket.settimeout(1)
            login_message = (self.call + "\n").encode('ascii')
            self._socket.sendall(login_message)
            self._socket.sendall(login_message)
            buffer = ""
            while not self._stop_requested:
                try:
                    received = self._socket.recv(4096)
                except socket.timeout:
                    continue
                if not received:
                    break

                buffer += received.decode(self.settingsDict['encodeStandart'], errors="ignore")
                lines = buffer.split("\n")
                buffer = lines.pop()
                for line in lines:
                    spot = line.replace("\x07", "").strip()
                    upper_spot = spot.upper()
                    if upper_spot.startswith("DX") and "Z" in upper_spot:
                        clean_list = spot.split()
                        if clean_list:
                            self.calibration_result.emit(clean_list)
                            return
        except (OSError, UnicodeError):
            return
        finally:
            if self._socket is not None:
                self._socket.close()
                self._socket = None
