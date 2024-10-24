import mysql.connector
from PyQt6.QtCore import pyqtSignal
from PySide6.QtCore import QObject, Signal, QThread, SignalInstance, Slot
from PySide6 import QtCore
#from PyQt6.QtCore import QObject, pyqtSignal, QThread



class DriverDB(QObject):
    """
    Class is driver for database.
    Responsible on connecting to database and action with db

    If connecting to db is correctly and active then emit signal conecting_ok_signal
    If error connection to db - emit signal connecting_error_signal

    Using
    After get instance need connect signals
    connecting_ok_signal (it signal using for start other component of log)
    connecting_error_signal
    error_signal

    """
    connecting_ok_signal = QtCore.Signal(object)
    connecting_error_signal = QtCore.Signal(object)
    error_signal = QtCore.Signal(object)

    def __init__(self, callsign, operator, settings_dict):
        super().__init__()
        self.callsign = callsign
        self.operator = operator
        self.settings_dict = settings_dict
        self.db_user = self.settings_dict["db-user"]
        self.db_pass = self.settings_dict["db-pass"]
        self.db_host = self.settings_dict["db-host"]
        self.database = self.settings_dict["db-name"]
        self.db_fields = None
        self.connecting_ok_signal.connect(self.start_after_connect)

        class Answer:
            status = None
            message = None
        self.__answer = Answer()

    @Slot(object)
    def start_after_connect(self, arg):
        self.get_fields_of_table()

    def init_connection(self):
        self.init_db()

    def init_db(self):
        try:
            self.connecting = mysql.connector.connect(user=self.db_user, password=self.db_pass,
                                                      host=self.db_host, database=self.database)
            self.__answer.status = "OK"
            self.__answer.message = f"Connecting to {self.database} active"
            print(f"Connecting to database active {self.__answer}")
            print(self.__answer.status)
            self.connecting_ok_signal.emit(self.__answer)
        except mysql.connector.errors.ProgrammingError:
            self.__answer.status = "ERROR"
            self.__answer.message = f"Error connection DB. Check data connection (user, password, host, database name)"
            print("ERROR: Connecting to database inactive. Check data connection (user, password, host, database name)")
            self.connecting_error_signal.emit(self.__answer)

    def get_fields_of_table(self):
        query = "describe UR4LGA_TEST"
        cursor = self.connecting.cursor()
        cursor.execute(query)
        self.db_fields = cursor.fetchall()

    def close_db(self):
        self.connecting.close()

    def db_out_to_dict(self, tuple_from_db):
        out_dict = {}
        for index, field in enumerate(self.db_fields):
            out_dict.update({field[0]: tuple_from_db[index]})
        return out_dict

    def commit_to_base(self, query):
        try:
            cursor = self.connecting.cursor()
            cursor.execute(query)
            answer = cursor.fetchall()
            self.__answer.status = "OK"
            self.__answer.message = answer
            cursor.close()
        except mysql.connector.errors.ProgrammingError:
            self.__answer.status = "ERROR"
            self.__answer.message = f"Error Connecting to Table {self.callsign} Check it field"
        return self.__answer

#### User functions
    def search_by_call(self, call):
        ...

    def get_all_qso(self):
        encode_out_list = []
        query = (f"SELECT * FROM {self.callsign};")
        raw_data = self.commit_to_base(query)
        if raw_data.status == "OK":
            for qso in raw_data.message:
                encode_out_list.append(self.db_out_to_dict(qso))
            self.__answer.status = "OK"
            self.__answer.message = encode_out_list
        else:
            self.__answer.status = "ERROR"
            self.__answer.message = f"ERROR: Incorrect query to db -> {raw_data.message}"

        return self.__answer



