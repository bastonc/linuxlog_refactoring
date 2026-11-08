import sys
import pymysql
import config_store
import time
import subprocess
import re
from pathlib import Path
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QWidget, QApplication, \
    QMainWindow, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt


class Help(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.key = key
        # self.input_data = input_data
        # if self.key == 'db-error':
        self.globad_db_name = 'linuxlog'
        self.help_text_style = "font-size: 12 px;"
        self.initUI()

    def initUI(self):
        # print("I a here")
        self.style_form = "background-color: " + settingsDict['form-background'] + "; color: " + settingsDict[
            'color-table'] + ";"
        screen = QApplication.primaryScreen()
        if screen is not None:
            desktop = screen.availableGeometry()
            width_coordinate = (desktop.width() / 2) - 200
            height_coordinate = (desktop.height() / 2) - 125
            self.move(int(width_coordinate), int(height_coordinate))

        self.setGeometry(100, 100, 500, 350)
        self.setWindowIcon(QIcon('logo.png'))
        self.setWindowTitle('Help system |Linux Log')
        style = "background-color:" + settingsDict['background-color'] + "; color:" + settingsDict[
            'color'] + ";"
        self.setStyleSheet(style)
        self.v_Box_Help = QVBoxLayout()
        self.v_Box_Help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Caption label
        self.hello_label = QLabel()
        self.hello_label.setText("LinuxLog help")
        self.hello_label.setStyleSheet("font-weight: bold; font-size: 18px;")
        # Help text label
        self.help_text_lay = QHBoxLayout()
        self.help_text = QLabel()
        self.help_text.setStyleSheet(self.help_text_style)
        self.help_text.setText(self.fill_help_text())
        # Help image
        self.help_image = QPixmap("logo.png")
        scaled_image = self.help_image.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio)
        self.help_image_label = QLabel()
        self.help_image_label.setPixmap(scaled_image)
        self.help_text_lay.addWidget(self.help_image_label)
        self.help_text_lay.addSpacing(10)
        self.help_text_lay.addWidget(self.help_text)
        # help form lay
        self.form_layout = QVBoxLayout()
        self.form_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_db_lay = QHBoxLayout()
        # label Username
        self.login_db_label = QLabel()
        self.login_db_label.setStyleSheet(style)
        self.login_db_label.setText("Username")
        self.login_db_label.setMaximumWidth(80)
        # linedit Username
        self.login_db = QLineEdit()
        self.login_db.setFixedWidth(100)
        self.login_db.setStyleSheet(self.style_form)
        self.login_db.setText(settingsDict['db-user'])
        # password fields
        self.pass_db_lay = QHBoxLayout()
        self.pass_db_label = QLabel()
        self.pass_db_label.setStyleSheet(style)
        self.pass_db_label.setText("Password")
        self.pass_db_label.setMaximumWidth(80)
        self.pass_db = QLineEdit()
        self.pass_db.setFixedWidth(100)
        self.pass_db.setStyleSheet(self.style_form)
        self.pass_db.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_db.setText(settingsDict['db-pass'])
        if config_store.is_process_env_managed('db-pass'):
            self.pass_db.setEnabled(False)
            self.pass_db.setToolTip(
                "Set by the LINUXLOG_DB_PASS environment variable; "
                "unset it to edit this field here."
            )
        # DataBase fields
        self.base_db_lay = QHBoxLayout()
        self.base_db_label = QLabel()
        self.base_db_label.setStyleSheet(style)
        self.base_db_label.setText("DB Name:")
        self.base_db_label.setMaximumWidth(80)
        self.base_db = QLineEdit()
        self.base_db.setFixedWidth(100)
        self.base_db.setStyleSheet(self.style_form)
        self.base_db.setText(settingsDict['db-name'])
        # Host db fields
        self.host_db_lay = QHBoxLayout()
        self.host_db_label = QLabel()
        self.host_db_label.setStyleSheet(style)
        self.host_db_label.setText("Host DB:")

        self.host_db_label.setMaximumWidth(80)
        self.host_db = QLineEdit()
        self.host_db.setFixedWidth(100)
        self.host_db.setStyleSheet(self.style_form)

        self.host_db.setText(settingsDict['db-host'])

        self.form_button_lay = QHBoxLayout()
        self.form_button_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_button = QPushButton("Check and Apply")
        self.apply_button.setFixedWidth(150)
        self.apply_button.setFixedHeight(30)
        self.apply_button.clicked.connect(self.check_base)

        self.login_db_lay.addWidget(self.login_db_label)
        self.login_db_lay.addWidget(self.login_db)
        self.pass_db_lay.addWidget(self.pass_db_label)
        self.pass_db_lay.addWidget(self.pass_db)
        self.base_db_lay.addWidget(self.base_db_label)
        self.base_db_lay.addWidget(self.base_db)
        self.host_db_lay.addWidget(self.host_db_label)
        self.host_db_lay.addWidget(self.host_db)
        self.form_button_lay.addWidget(self.apply_button)

        self.form_layout.addLayout(self.login_db_lay)
        self.form_layout.addLayout(self.pass_db_lay)
        self.form_layout.addLayout(self.base_db_lay)
        self.form_layout.addLayout(self.host_db_lay)
        self.form_layout.addLayout(self.form_button_lay)

        self.v_Box_Help.addWidget(self.hello_label)
        self.v_Box_Help.addLayout(self.help_text_lay)
        self.v_Box_Help.addLayout(self.form_layout)
        central_widget = QWidget()
        central_widget.setLayout(self.v_Box_Help)
        self.setCentralWidget(central_widget)
        self.show()

    def check_base(self):
        database_name = self.base_db.text().strip()
        if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
            self.message("Invalid database name", "Use only letters, digits, and underscores.")
            return

        connection = None
        try:
            connection = pymysql.connect(
                host=self.host_db.text().strip(),
                user=self.login_db.text().strip(),
                password=self.pass_db.text().strip(),
                charset=settingsDict['db-charset'],
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5,
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                    (database_name,),
                )
                if cursor.fetchone() is None:
                    cursor.execute(f"CREATE DATABASE `{database_name}`")
            connection.close()
            connection = None
            self.update_file_to_disk()
            self.close()
            subprocess.Popen(
                [sys.executable, str(Path(__file__).parent / "main.py")],
                cwd=str(Path(__file__).parent),
            )
        except (pymysql.MySQLError, OSError) as error:
            self.message("Database setup failed", str(error))
        finally:
            if connection is not None:
                connection.close()

    def update_file_to_disk(self):
        return config_store.update_settings({
            "db-host": self.host_db.text().strip(),
            "db-user": self.login_db.text().strip(),
            "db-pass": self.pass_db.text().strip(),
            "db-name": self.base_db.text().strip(),
        })

    def fill_help_text(self, lang='eng'):

        if lang == 'eng':
            text = "Hello. I'am help system by LinuxLog.\n" \
                   "You have problem with connected to MySQL database.\n" \
                   "It happens when value in fields incorrect. \n" \
                   "Please check fields bottom.\n\nDATABASE CONNECTION FIELDS"

        return text

    def message(self, caption, text_message):
        message = QMessageBox(self)
        # message.setFixedWidth(350)
        # message.setFixedHeight(200)
        # Geometry(500, 300, 1000, 700)
        message.setWindowTitle("Information")
        message.setText(caption)
        message.setInformativeText(text_message)
        message.setStandardButtons(QMessageBox.StandardButton.Ok)
        message.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    settingsDict = config_store.load_settings()

    if len(sys.argv) > 1:
        help_w = Help()
        help_w.show()
    sys.exit(app.exec())
