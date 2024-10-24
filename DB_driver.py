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

    """
    connecting_ok_signal = QtCore.Signal(object, name="connecting_ok_signal")
    connecting_error_signal = QtCore.Signal(object)

    def __init__(self, callsign, operator):
        super().__init__()
        self.callsign = callsign
        self.operator = operator
        self.db_user = "linuxlog"
        self.db_pass = "Linuxlog12#"
        self.db_host = "localhost"
        self.database = "linuxlog"
        #self.connecting_ok_signal.connect(self.test_ok_slot)

        class Answer:
            status = None
            message = None
        self.__answer = Answer()

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

    def run(self):
        print("test")

    def close_db(self):
        self.connecting.close()


    def search_by_call(self, call):
        ...

    def get_all_qso(self):
        output_data = None
        cursor = self.connecting.cursor()
        query = (f"SELECT * FROM {self.callsign};")
        try:
            cursor.execute(query)
            self.__answer.status = "OK"
            self.__answer.message = cursor.fetchall()
            cursor.close()
        except mysql.connector.errors.ProgrammingError:
            self.__answer.status = "ERROR"
            self.__answer.message = f"Error Connecting to Table {self.callsign} Check it field"
        output_data = self.__answer
        return output_data




